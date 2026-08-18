"""Sales Return domain service orchestrating RMA In requests and condition-based restocking."""

import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.core.security import CurrentUser

from app.models.returns import (
    ReturnItemConditionEnum,
    SalesReturn,
    SalesReturnItem,
    SalesReturnStatusEnum,
)
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.repositories.interfaces.sales_return_repository import SalesReturnRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.schemas.sales_returns import (
    SalesReturnCreateRequest,
    SalesReturnItemResponse,
    SalesReturnResponse,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class SalesReturnService:
    """
    Domain service for retailer inbound returns (RMA In).

    Enforces:
    1. Quantity validation: Cannot return more than was fulfilled on the sales order.
    2. Condition-based restocking: Resellable items replenish on-hand stock batches via
       RETURN_IN movements; Damaged items are logged in return records for loss tracking
       without altering sellable inventory batches.
    3. Audit logging for all return state transitions.
    """

    def __init__(
        self,
        return_repo: SalesReturnRepositoryInterface,
        sales_order_repo: SalesOrderRepositoryInterface,
        stock_repo: StockRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        audit_service: AuditService | None = None,
    ) -> None:
        self.return_repo = return_repo
        self.sales_order_repo = sales_order_repo
        self.stock_repo = stock_repo
        self.product_repo = product_repo
        self.audit_service = audit_service

    def create_return(
        self, payload: SalesReturnCreateRequest, current_user: CurrentUser
    ) -> SalesReturnResponse:
        """Create a new RMA In return request after validating sold quantities."""
        order = self.sales_order_repo.get_by_id(payload.sales_order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales order '{payload.sales_order_id}' not found.",
            )

        # 1. Validate order status
        returnable_statuses = {"confirmed", "packed", "shipped", "delivered"}
        order_status_str = (
            order.status.value if hasattr(order.status, "value") else str(order.status)
        ).lower()
        if order_status_str not in returnable_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Cannot create return for sales order '{order.so_number}' with status '{order_status_str}'. "
                    f"Orders must be confirmed, packed, shipped, or delivered."
                ),
            )

        # 2. Compute sold quantities and previously returned quantities per product
        sold_map: dict[str, float] = {}
        for it in order.items:
            prod_id = getattr(it, "product_id", None) or it.get("product_id")
            qty = float(getattr(it, "qty", None) or it.get("qty", 0.0))
            sold_map[prod_id] = round(sold_map.get(prod_id, 0.0) + qty, 2)

        returned_map = self.return_repo.get_returned_quantities_by_order(order.id)

        # 3. Validate requested return lines against remaining returnable limits
        requested_by_prod: dict[str, float] = {}
        for item_in in payload.items:
            requested_by_prod[item_in.product_id] = round(
                requested_by_prod.get(item_in.product_id, 0.0) + float(item_in.qty), 2
            )

        for prod_id, req_qty in requested_by_prod.items():
            sold_qty = sold_map.get(prod_id, 0.0)
            if sold_qty <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Product '{prod_id}' was not part of sales order '{order.so_number}'.",
                )

            already_ret = returned_map.get(prod_id, 0.0)
            max_returnable = round(sold_qty - already_ret, 2)
            if req_qty > max_returnable:
                prod = self.product_repo.get_by_id(prod_id)
                prod_name = getattr(prod, "name", None) or prod_id
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"Cannot return {req_qty} units of '{prod_name}': "
                        f"maximum returnable quantity on order '{order.so_number}' is {max_returnable} "
                        f"(sold {sold_qty}, already returned {already_ret})."
                    ),
                )

        # 4. Construct SalesReturn model
        retailer_id = payload.retailer_id or getattr(order, "retailer_id", None)
        if not retailer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retailer ID could not be identified from sales order.",
            )

        return_id = str(uuid.uuid4())
        return_items: list[SalesReturnItem] = []
        for it_in in payload.items:
            return_items.append(
                SalesReturnItem(
                    id=str(uuid.uuid4()),
                    return_id=return_id,
                    product_id=it_in.product_id,
                    qty=float(it_in.qty),
                    batch_id=it_in.batch_id,
                    condition=it_in.condition,
                )
            )

        sales_return = SalesReturn(
            id=return_id,
            sales_order_id=order.id,
            retailer_id=retailer_id,
            status=SalesReturnStatusEnum.REQUESTED,
            reason=payload.reason,
            requested_at=datetime.now(UTC),
            items=return_items,
        )

        saved = self.return_repo.create(sales_return)

        if self.audit_service and current_user.id:
            self.audit_service.log_action(
                actor_id=current_user.id,
                action="sales_return_requested",
                entity_type="sales_return",
                entity_id=saved.id,
                before_value=None,
                after_value={
                    "sales_order_id": order.id,
                    "so_number": order.so_number,
                    "retailer_id": retailer_id,
                    "status": saved.status.value,
                    "item_count": len(saved.items),
                },
            )

        return self._to_response(saved, order)

    def approve_return(self, return_id: str, current_user: CurrentUser) -> SalesReturnResponse:
        """
        Approve an RMA In return request and apply condition-based restocking:
        - Resellable: Replenishes stock batches and inserts RETURN_IN stock movement.
        - Damaged: Kept in return record for loss tracking; does NOT top up sellable inventory.
        """
        sales_return = self.return_repo.get_by_id(return_id)
        if not sales_return:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales return '{return_id}' not found.",
            )

        if sales_return.status != SalesReturnStatusEnum.REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Cannot approve sales return in status '{sales_return.status.value}'. "
                    f"Only returns in 'requested' status can be approved."
                ),
            )

        # Condition-based restocking
        for it in sales_return.items:
            cond = it.condition
            if isinstance(cond, str):
                is_resellable = cond.lower() == ReturnItemConditionEnum.RESELLABLE.value
            else:
                is_resellable = cond == ReturnItemConditionEnum.RESELLABLE

            if is_resellable:
                # Top up sellable stock
                self.stock_repo.record_sales_return_stock(
                    product_id=it.product_id,
                    quantity=float(it.qty),
                    batch_id=it.batch_id,
                    reference_id=sales_return.id,
                    created_by=current_user.id,
                )
            else:
                # Damaged condition: Excluded from sellable stock replenishment
                logger.info(
                    "Sales return %s item %s (%s units) is DAMAGED; skipping sellable batch restock.",
                    sales_return.id,
                    it.product_id,
                    it.qty,
                )

        updated = self.return_repo.update_status(sales_return.id, SalesReturnStatusEnum.APPROVED)
        result = updated or sales_return

        if self.audit_service and current_user.id:
            self.audit_service.log_action(
                actor_id=current_user.id,
                action="sales_return_approved",
                entity_type="sales_return",
                entity_id=result.id,
                before_value={"status": SalesReturnStatusEnum.REQUESTED.value},
                after_value={"status": result.status.value},
            )

        return self._to_response(result)

    def reject_return(
        self, return_id: str, reason: str | None, current_user: CurrentUser
    ) -> SalesReturnResponse:
        """Reject an RMA In return request without altering inventory."""
        sales_return = self.return_repo.get_by_id(return_id)
        if not sales_return:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales return '{return_id}' not found.",
            )

        if sales_return.status != SalesReturnStatusEnum.REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Cannot reject sales return with status '{sales_return.status.value}'.",
            )

        updated = self.return_repo.update_status(sales_return.id, SalesReturnStatusEnum.REJECTED)
        result = updated or sales_return

        if self.audit_service and current_user.id:
            self.audit_service.log_action(
                actor_id=current_user.id,
                action="sales_return_rejected",
                entity_type="sales_return",
                entity_id=result.id,
                before_value={"status": SalesReturnStatusEnum.REQUESTED.value},
                after_value={"status": result.status.value, "reason": reason},
            )

        return self._to_response(result)

    def get_return(self, return_id: str) -> SalesReturnResponse:
        """Fetch a single Sales Return by ID."""
        sales_return = self.return_repo.get_by_id(return_id)
        if not sales_return:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales return '{return_id}' not found.",
            )
        return self._to_response(sales_return)

    def list_returns(
        self,
        skip: int = 0,
        limit: int = 100,
        retailer_id: str | None = None,
        sales_order_id: str | None = None,
        status_filter: SalesReturnStatusEnum | None = None,
        search: str | None = None,
    ) -> list[SalesReturnResponse]:
        """Fetch filtered and paginated list of Sales Returns."""
        records = self.return_repo.list_all(
            skip=skip,
            limit=limit,
            retailer_id=retailer_id,
            sales_order_id=sales_order_id,
            status=status_filter,
            search=search,
        )
        return [self._to_response(r) for r in records]

    def _to_response(
        self, sales_return: SalesReturn, cached_order: Any | None = None
    ) -> SalesReturnResponse:
        """Map SalesReturn domain model to detailed response DTO."""
        order = cached_order or getattr(sales_return, "sales_order", None)
        if not order and sales_return.sales_order_id:
            order = self.sales_order_repo.get_by_id(sales_return.sales_order_id)

        retailer_name = None
        if hasattr(sales_return, "retailer") and sales_return.retailer:
            retailer_name = getattr(sales_return.retailer, "name", None)
        elif order and hasattr(order, "retailer") and order.retailer:
            retailer_name = getattr(order.retailer, "name", None)

        so_number = getattr(order, "so_number", None) if order else None

        # Build map of order item unit prices
        price_map: dict[str, float] = {}
        if order and hasattr(order, "items") and order.items:
            for o_it in order.items:
                pid = getattr(o_it, "product_id", None) or o_it.get("product_id")
                u_price = float(getattr(o_it, "unit_price", None) or o_it.get("unit_price", 0.0))
                price_map[pid] = u_price

        items_resp: list[SalesReturnItemResponse] = []
        total_credit_adj = 0.0

        for it in getattr(sales_return, "items", []):
            prod = getattr(it, "product", None)
            if not prod:
                prod = self.product_repo.get_by_id(it.product_id)

            prod_name = getattr(prod, "name", None) if prod else None
            prod_sku = getattr(prod, "sku", None) if prod else None

            batch = getattr(it, "batch", None)
            batch_no = getattr(batch, "batch_no", None) if batch else None

            unit_price = price_map.get(
                it.product_id,
                float(getattr(prod, "wholesale_price", 0.0) if prod else 0.0),
            )
            refund_amount = round(unit_price * float(it.qty), 2)
            total_credit_adj = round(total_credit_adj + refund_amount, 2)

            cond = it.condition
            if isinstance(cond, str):
                cond_enum = (
                    ReturnItemConditionEnum.DAMAGED
                    if cond.lower() == "damaged"
                    else ReturnItemConditionEnum.RESELLABLE
                )
            else:
                cond_enum = cond

            items_resp.append(
                SalesReturnItemResponse(
                    id=it.id,
                    return_id=it.return_id,
                    product_id=it.product_id,
                    product_name=prod_name,
                    product_sku=prod_sku,
                    qty=float(it.qty),
                    batch_id=it.batch_id,
                    batch_no=batch_no,
                    condition=cond_enum,
                    unit_price=unit_price,
                    refund_amount=refund_amount,
                )
            )

        status_enum = sales_return.status
        if isinstance(status_enum, str):
            status_enum = SalesReturnStatusEnum(status_enum.lower())

        req_at = getattr(sales_return, "requested_at", None)
        if isinstance(req_at, str):
            req_at = datetime.fromisoformat(req_at)
        elif not req_at:
            req_at = datetime.now(UTC)

        return SalesReturnResponse(
            id=sales_return.id,
            sales_order_id=sales_return.sales_order_id,
            so_number=so_number,
            retailer_id=sales_return.retailer_id,
            retailer_name=retailer_name,
            status=status_enum,
            reason=sales_return.reason,
            credit_adjustment_amount=total_credit_adj,
            requested_at=req_at,
            items=items_resp,
        )
