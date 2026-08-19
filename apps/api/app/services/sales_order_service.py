"""Sales Order Domain Service managing orders, credit gates, and FIFO stock deductions."""

import uuid
from typing import Any

from fastapi import HTTPException, status

from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.repositories.interfaces.customer_repository import CustomerRepositoryInterface
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.schemas.sales_orders import (
    SalesOrderCreateRequest,
    SalesOrderItemCreateRequest,
    SalesOrderItemResponse,
    SalesOrderResponse,
    SalesOrderStatusUpdateRequest,
)
from app.services.anomaly_detection_service import AnomalyDetectionService
from app.services.audit_service import AuditService
from app.services.pricing_strategy import PricingEngineService
from app.services.uom_service import UomService


class SalesOrderService:
    """Domain service orchestrating sales orders, credit checks, and FIFO batch deductions."""

    VALID_TRANSITIONS: dict[SOStatusEnum, set[SOStatusEnum]] = {
        SOStatusEnum.DRAFT: {SOStatusEnum.CONFIRMED, SOStatusEnum.CANCELLED},
        SOStatusEnum.CONFIRMED: {SOStatusEnum.PACKED, SOStatusEnum.CANCELLED},
        SOStatusEnum.PACKED: {SOStatusEnum.SHIPPED},
        SOStatusEnum.SHIPPED: {SOStatusEnum.DELIVERED},
        SOStatusEnum.DELIVERED: set(),
        SOStatusEnum.CANCELLED: set(),
    }

    def __init__(
        self,
        so_repo: SalesOrderRepositoryInterface,
        retailer_repo: RetailerRepository,
        stock_repo: StockRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        pricing_engine: PricingEngineService,
        customer_repo: CustomerRepositoryInterface | None = None,
        uom_service: UomService | None = None,
        audit_service: AuditService | None = None,
        alert_engine: Any = None,
        anomaly_detector: AnomalyDetectionService | None = None,
    ):
        self.so_repo = so_repo
        self.retailer_repo = retailer_repo
        self.stock_repo = stock_repo
        self.product_repo = product_repo
        self.pricing_engine = pricing_engine
        self.customer_repo = customer_repo
        self.uom_service = uom_service
        self.audit_service = audit_service
        self.alert_engine = alert_engine
        self.anomaly_detector = anomaly_detector

    def create_order(
        self, payload: SalesOrderCreateRequest, current_user: Any = None
    ) -> SalesOrderResponse:
        """Create a new draft sales order with tier-calculated pricing."""
        retailer = self._resolve_retailer(payload)
        tier = getattr(retailer, "pricing_tier", "standard") if retailer else "standard"

        items = [self._build_order_item(item_in, tier) for item_in in payload.items]
        total_amount = round(sum(it.qty * it.unit_price for it in items), 2)

        so = SalesOrder(
            id=str(uuid.uuid4()),
            so_number=self.so_repo.generate_next_so_number(),
            buyer_type=payload.buyer_type,
            retailer_id=payload.retailer_id,
            customer_id=payload.customer_id,
            status=SOStatusEnum.DRAFT,
            total_amount=total_amount,
            items=items,
        )

        saved = self.so_repo.create(so)
        self._audit_log(
            action="sales_order_created",
            target_id=saved.id,
            after=self._so_to_dict(saved),
            current_user=current_user,
        )
        return self._to_response(saved)

    def confirm_order(self, order_id: str, current_user: Any = None) -> SalesOrderResponse:
        """Confirm a draft sales order: enforces credit gate first, then deducts stock via FIFO."""
        order = self._get_order_or_404(order_id)
        if order.status != SOStatusEnum.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot confirm order {order.so_number} with status '{order.status}'.",
            )

        # 1. Credit Gate First (before touching inventory)
        self._check_and_reserve_credit(order)

        # 2. Stock Gate Second (FIFO batch deduction)
        self._deduct_stock_fifo(order, current_user)

        # 3. Status update and audit trail
        before_state = self._so_to_dict(order)
        order.status = SOStatusEnum.CONFIRMED
        saved = self.so_repo.update(order)

        self._audit_log(
            action="sales_order_confirmed",
            target_id=saved.id,
            before=before_state,
            after=self._so_to_dict(saved),
            current_user=current_user,
        )

        # Inline smart alert trigger for all affected products
        if self.alert_engine:
            for item in order.items:
                try:
                    self.alert_engine.evaluate_product_stock_inline(item.product_id)
                except Exception:
                    pass

        return self._to_response(saved)

    def update_status(
        self, order_id: str, payload: SalesOrderStatusUpdateRequest, current_user: Any = None
    ) -> SalesOrderResponse:
        """Advance fulfillment status or cancel with compensating inventory adjustment."""
        order = self._get_order_or_404(order_id)
        target = payload.status

        if target == SOStatusEnum.CONFIRMED and order.status == SOStatusEnum.DRAFT:
            return self.confirm_order(order_id, current_user)

        allowed = self.VALID_TRANSITIONS.get(order.status, set())
        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid transition from '{order.status}' to '{target}'. Allowed: {[s.value for s in allowed]}",
            )

        before_state = self._so_to_dict(order)

        # Cancelling a confirmed order requires compensating inventory restoration & credit refund
        if target == SOStatusEnum.CANCELLED and order.status == SOStatusEnum.CONFIRMED:
            self._revert_stock_and_credit(order, current_user)

        order.status = target
        saved = self.so_repo.update(order)

        self._audit_log(
            action="sales_order_status_updated",
            target_id=saved.id,
            before=before_state,
            after=self._so_to_dict(saved),
            current_user=current_user,
        )
        return self._to_response(saved)

    def get_order(self, order_id: str) -> SalesOrderResponse:
        """Fetch sales order by ID."""
        order = self._get_order_or_404(order_id)
        return self._to_response(order)

    def list_orders(
        self,
        status: str | None = None,
        retailer_id: str | None = None,
        buyer_type: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[SalesOrderResponse], int]:
        """List sales orders with filters and pagination."""
        orders, total = self.so_repo.list_all(
            status=status,
            retailer_id=retailer_id,
            buyer_type=buyer_type,
            search=search,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(o) for o in orders], total

    # --- Private Helper Methods ---

    def _get_order_or_404(self, order_id: str) -> SalesOrder:
        order = self.so_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales Order '{order_id}' not found.",
            )
        return order

    def _resolve_retailer(self, payload: SalesOrderCreateRequest) -> Retailer | None:
        if payload.buyer_type == BuyerTypeEnum.RETAILER:
            if not payload.retailer_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="retailer_id is required when buyer_type is 'retailer'.",
                )
            retailer = self.retailer_repo.get_by_id(payload.retailer_id)
            if not retailer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Retailer '{payload.retailer_id}' not found.",
                )
            return retailer

        if (
            payload.buyer_type == BuyerTypeEnum.CUSTOMER
            and payload.customer_id
            and self.customer_repo
        ):
            customer = self.customer_repo.get_by_id(payload.customer_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer '{payload.customer_id}' not found.",
                )
        return None

    def _build_order_item(
        self, item_in: SalesOrderItemCreateRequest, pricing_tier: str
    ) -> SalesOrderItem:
        product = self.product_repo.get_by_id(item_in.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{item_in.product_id}' not found.",
            )

        prod_id = product.id if hasattr(product, "id") else product["id"]
        if item_in.unit_price is not None:
            unit_price = float(item_in.unit_price)
        else:
            base_wholesale = (
                float(product.wholesale_price)
                if hasattr(product, "wholesale_price")
                else float(product.get("wholesale_price", 0.0))
            )
            calc_res = self.pricing_engine.calculate_line_price(
                pricing_tier, base_wholesale, int(item_in.qty)
            )
            unit_price = calc_res.unit_price

        return SalesOrderItem(
            id=str(uuid.uuid4()),
            product_id=prod_id,
            qty=float(item_in.qty),
            unit_price=round(unit_price, 2),
            uom_id=item_in.uom_id,
        )

    def _check_and_reserve_credit(self, order: SalesOrder) -> None:
        if order.buyer_type != BuyerTypeEnum.RETAILER or not order.retailer_id:
            return

        retailer = self.retailer_repo.get_by_id(order.retailer_id)
        if not retailer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer '{order.retailer_id}' not found.",
            )

        credit_limit = float(retailer.credit_limit)
        credit_balance = float(retailer.credit_balance)
        order_total = float(order.total_amount)

        # 0 limit = cash-only, always allowed
        if credit_limit > 0:
            proposed_balance = round(credit_balance + order_total, 2)
            if proposed_balance > credit_limit:
                shortfall = round(proposed_balance - credit_limit, 2)
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Credit limit exceeded for retailer '{retailer.name}': "
                        f"limit ₹{credit_limit:.2f}, current balance ₹{credit_balance:.2f}, "
                        f"order amount ₹{order_total:.2f}, shortfall ₹{shortfall:.2f}"
                    ),
                )

        new_balance = round(credit_balance + order_total, 2)
        self.retailer_repo.update(retailer.id, {"credit_balance": new_balance})

    def _deduct_stock_fifo(self, order: SalesOrder, current_user: Any = None) -> None:
        user_id = getattr(current_user, "id", None)
        for item in order.items:
            qty_to_deduct = float(item.qty)
            if item.uom_id and self.uom_service:
                conv = self.uom_service.convert_to_base_uom(
                    item.product_id, qty_to_deduct, item.uom_id
                )
                qty_to_deduct = conv.base_quantity

            try:
                self.stock_repo.deduct_stock_fifo(
                    product_id=item.product_id,
                    quantity=qty_to_deduct,
                    reference_type="sales_order",
                    reference_id=order.id,
                    created_by=user_id,
                )
            except ValueError as e:
                # Revert credit balance increment if stock check fails
                self._refund_credit(order)
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(e),
                ) from e

    def _revert_stock_and_credit(self, order: SalesOrder, current_user: Any = None) -> None:
        user_id = getattr(current_user, "id", None)
        self.stock_repo.restore_sales_order_stock(
            sales_order_id=order.id,
            reason="Order Cancelled",
            created_by=user_id,
        )
        self._refund_credit(order)

    def _refund_credit(self, order: SalesOrder) -> None:
        if order.buyer_type == BuyerTypeEnum.RETAILER and order.retailer_id:
            retailer = self.retailer_repo.get_by_id(order.retailer_id)
            if retailer:
                new_balance = max(
                    0.0, round(float(retailer.credit_balance) - float(order.total_amount), 2)
                )
                self.retailer_repo.update(retailer.id, {"credit_balance": new_balance})

    def _audit_log(
        self,
        action: str,
        target_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        current_user: Any = None,
    ) -> None:
        if self.audit_service:
            self.audit_service.log(
                action=action,
                entity_type="sales_order",
                entity_id=target_id,
                before=before or {},
                after=after or {},
                current_user=current_user,
            )

    def _so_to_dict(self, order: SalesOrder) -> dict[str, Any]:
        return {
            "id": order.id,
            "so_number": order.so_number,
            "buyer_type": order.buyer_type,
            "retailer_id": order.retailer_id,
            "status": order.status,
            "total_amount": float(order.total_amount),
        }

    def get_order_anomalies(self, order_id: str):
        """Evaluate order line items for unusual quantities."""
        order = self._get_order_or_404(order_id)
        if self.anomaly_detector:
            return self.anomaly_detector.evaluate_order(order)
        return None

    def _to_response(self, order: SalesOrder) -> SalesOrderResponse:
        item_responses: list[SalesOrderItemResponse] = []
        retailer_id = getattr(order, "retailer_id", None)
        customer_id = getattr(order, "customer_id", None)
        order_id = getattr(order, "id", None)

        for it in order.items:
            prod_name = it.product.name if getattr(it, "product", None) else None
            prod_sku = it.product.sku if getattr(it, "product", None) else None
            uom_code = it.uom.code if getattr(it, "uom", None) else None

            is_unusual = False
            anomaly_reason = None
            h_mean = None
            h_stddev = None

            if self.anomaly_detector:
                try:
                    report = self.anomaly_detector.evaluate_line_item(
                        product_id=it.product_id,
                        qty=float(it.qty),
                        retailer_id=retailer_id,
                        customer_id=customer_id,
                        exclude_order_id=order_id,
                        product_name=prod_name,
                        product_sku=prod_sku,
                    )
                    is_unusual = report.is_unusual
                    anomaly_reason = report.anomaly_reason
                    h_mean = report.historical_mean
                    h_stddev = report.historical_stddev
                except Exception:
                    pass

            item_responses.append(
                SalesOrderItemResponse(
                    id=it.id,
                    so_id=it.so_id,
                    product_id=it.product_id,
                    product_name=prod_name,
                    product_sku=prod_sku,
                    qty=float(it.qty),
                    unit_price=float(it.unit_price),
                    line_total=round(float(it.qty) * float(it.unit_price), 2),
                    uom_id=it.uom_id,
                    uom_code=uom_code,
                    is_unusual=is_unusual,
                    anomaly_reason=anomaly_reason,
                    historical_mean=h_mean,
                    historical_stddev=h_stddev,
                )
            )

        retailer_name = order.retailer.name if getattr(order, "retailer", None) else None
        pricing_tier = (
            getattr(order.retailer, "pricing_tier", None)
            if getattr(order, "retailer", None)
            else None
        )

        customer_name = order.customer.name if getattr(order, "customer", None) else None
        if not customer_name and order.customer_id and self.customer_repo:
            cust = self.customer_repo.get_by_id(order.customer_id)
            if cust:
                customer_name = cust.name

        unusual_items = [it for it in item_responses if it.is_unusual]
        anomaly_warnings = [it.anomaly_reason for it in unusual_items if it.anomaly_reason]

        return SalesOrderResponse(
            id=order.id,
            so_number=order.so_number,
            buyer_type=order.buyer_type,
            retailer_id=order.retailer_id,
            retailer_name=retailer_name,
            retailer_pricing_tier=pricing_tier,
            customer_id=order.customer_id,
            customer_name=customer_name,
            status=order.status,
            order_date=order.order_date,
            total_amount=float(order.total_amount),
            created_at=order.created_at,
            items=item_responses,
            has_unusual_items=len(unusual_items) > 0,
            unusual_items_count=len(unusual_items),
            anomaly_warnings=anomaly_warnings,
        )
