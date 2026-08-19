import math
from datetime import date
from typing import TYPE_CHECKING, Any, Literal

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.core.security import CurrentUser

from app.models.catalog import Product
from app.models.warehouse import StockBatch
from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.repositories.interfaces.uom_repository import UomRepositoryInterface
from app.schemas.stock import (
    ProductStockResponse,
    StockBatchResponse,
    StockOverviewItem,
    StockOverviewResponse,
    WarehouseStockBreakdown,
    WarehouseSummary,
)
from app.schemas.stock_adjustments import (
    AdjustmentReasonEnum,
    StockAdjustmentCreateRequest,
    StockAdjustmentResponse,
    StockMovementListItemResponse,
    StockMovementListResponse,
)
from app.services.uom_service import UomService


class StockService:
    """Domain service managing inventory on-hand balances, batch tracking, and status calculations."""

    def __init__(
        self,
        stock_repo: StockRepositoryInterface,
        uom_repo: UomRepositoryInterface | None = None,
        uom_service: UomService | None = None,
        audit_repo: AuditRepository | None = None,
    ):
        self.stock_repo = stock_repo
        self.uom_repo = uom_repo
        self.uom_service = uom_service or (UomService(uom_repo=uom_repo) if uom_repo else None)
        self.audit_repo = audit_repo

    @staticmethod
    def calculate_stock_status(
        on_hand: float, reorder_point: float
    ) -> Literal["ok", "low", "critical"]:
        """
        Compute stock health status against reorder point threshold:
        - ok: on_hand > reorder_point
        - low: 0.25 * reorder_point < on_hand <= reorder_point
        - critical: on_hand <= 0.25 * reorder_point (or 0 / negative)
        """
        if reorder_point <= 0:
            return "ok" if on_hand > 0 else "critical"

        critical_threshold = 0.25 * float(reorder_point)
        if on_hand > reorder_point:
            return "ok"
        if on_hand <= critical_threshold:
            return "critical"
        return "low"

    def _convert_batch_to_response(self, batch: StockBatch) -> StockBatchResponse:
        """Helper to transform StockBatch ORM entity into StockBatchResponse with expiry metadata."""
        today = date.today()
        days_until_expiry: int | None = None
        is_expired = False

        if batch.expiry_date:
            days_until_expiry = (batch.expiry_date - today).days
            is_expired = days_until_expiry < 0

        warehouse_name = batch.warehouse.name if batch.warehouse else "Warehouse"

        return StockBatchResponse(
            id=batch.id,
            product_id=batch.product_id,
            warehouse_id=batch.warehouse_id,
            warehouse_name=warehouse_name,
            batch_no=batch.batch_no,
            quantity=float(batch.quantity),
            expiry_date=batch.expiry_date,
            received_at=batch.received_at,
            days_until_expiry=days_until_expiry,
            is_expired=is_expired,
        )

    def _get_preferred_uom_display(
        self, product: Product, base_qty: float
    ) -> tuple[str | None, float | None]:
        """Helper to determine largest packaging conversion ratio for human-friendly display."""
        if not self.uom_repo or not product.base_uom_id:
            return None, None

        conversions = self.uom_repo.list_product_conversions(product.id)
        if not conversions:
            return None, None

        # Look for conversion where to_uom_id is base_uom_id and factor > 1
        valid_convs = [
            c for c in conversions if c.to_uom_id == product.base_uom_id and float(c.factor) > 1.0
        ]
        if not valid_convs:
            return None, None

        # Pick highest packaging factor (e.g. Pallet or Case)
        best_conv = max(valid_convs, key=lambda c: float(c.factor))
        from_uom_name = best_conv.from_uom.name if best_conv.from_uom else "Case"
        converted_qty = round(base_qty / float(best_conv.factor), 2)
        return from_uom_name, converted_qty

    def get_product_stock(
        self, product_id: str, warehouse_id: str | None = None
    ) -> ProductStockResponse:
        """Retrieve full stock breakdown for a specific product."""
        product = self.stock_repo.get_product_with_base_uom(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found.",
            )

        batches = self.stock_repo.get_batches_by_product(product_id, warehouse_id)
        total_on_hand = sum(float(b.quantity) for b in batches)

        # Per-warehouse breakdown
        wh_map: dict[str, dict[str, Any]] = {}
        for b in batches:
            wid = b.warehouse_id
            wname = b.warehouse.name if b.warehouse else "Warehouse"
            if wid not in wh_map:
                wh_map[wid] = {
                    "warehouse_id": wid,
                    "warehouse_name": wname,
                    "on_hand": 0.0,
                    "batch_count": 0,
                }
            wh_map[wid]["on_hand"] = round(wh_map[wid]["on_hand"] + float(b.quantity), 2)
            wh_map[wid]["batch_count"] += 1

        warehouses = [
            WarehouseStockBreakdown(
                warehouse_id=item["warehouse_id"],
                warehouse_name=item["warehouse_name"],
                on_hand=item["on_hand"],
                batch_count=item["batch_count"],
            )
            for item in wh_map.values()
        ]

        batch_responses = [self._convert_batch_to_response(b) for b in batches]
        stock_status = self.calculate_stock_status(total_on_hand, product.reorder_point)

        pref_name, pref_qty = self._get_preferred_uom_display(product, total_on_hand)
        base_uom_name = product.base_uom.name if product.base_uom else product.unit or "Piece"

        return ProductStockResponse(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            base_uom_name=base_uom_name,
            cost_price=float(product.cost_price),
            wholesale_price=float(product.wholesale_price),
            reorder_point=product.reorder_point,
            reorder_qty=product.reorder_qty,
            total_on_hand=round(total_on_hand, 2),
            preferred_uom_name=pref_name,
            preferred_uom_qty=pref_qty,
            stock_status=stock_status,
            warehouses=warehouses,
            batches=batch_responses,
        )

    def get_stock_overview(
        self,
        warehouse_id: str | None = None,
        category_id: str | None = None,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> StockOverviewResponse:
        """Fetch filtered inventory overview feed across all products and warehouses."""
        raw_rows = self.stock_repo.get_stock_overview_data(
            warehouse_id=warehouse_id,
            category_id=category_id,
            search=search,
        )

        items: list[StockOverviewItem] = []
        ok_count = 0
        low_count = 0
        critical_count = 0

        for row in raw_rows:
            p: Product = row["product"]
            on_hand: float = row["total_on_hand"]
            item_status = self.calculate_stock_status(on_hand, p.reorder_point)

            if item_status == "ok":
                ok_count += 1
            elif item_status == "low":
                low_count += 1
            elif item_status == "critical":
                critical_count += 1

            if status_filter and item_status != status_filter.lower():
                continue

            wh_breakdown = [
                WarehouseStockBreakdown(
                    warehouse_id=w["warehouse_id"],
                    warehouse_name=w["warehouse_name"],
                    on_hand=w["on_hand"],
                    batch_count=w["batch_count"],
                )
                for w in row["warehouses"]
            ]

            pref_name, pref_qty = self._get_preferred_uom_display(p, on_hand)
            base_uom_name = p.base_uom.name if p.base_uom else p.unit or "Piece"
            category_name = p.category.name if p.category else None

            items.append(
                StockOverviewItem(
                    product_id=p.id,
                    sku=p.sku,
                    name=p.name,
                    category_id=p.category_id,
                    category_name=category_name,
                    image_url=p.image_url,
                    base_uom_name=base_uom_name,
                    total_on_hand=on_hand,
                    preferred_uom_name=pref_name,
                    preferred_uom_qty=pref_qty,
                    reorder_point=p.reorder_point,
                    stock_status=item_status,
                    warehouses=wh_breakdown,
                )
            )

        return StockOverviewResponse(
            items=items,
            total_products=len(items),
            ok_count=ok_count,
            low_count=low_count,
            critical_count=critical_count,
        )

    def get_batches_expiring_soon(
        self, days: int = 30, warehouse_id: str | None = None
    ) -> list[StockBatchResponse]:
        """Fetch active batches expiring within the specified horizon."""
        batches = self.stock_repo.get_batches_expiring_soon(days, warehouse_id)
        return [self._convert_batch_to_response(b) for b in batches]

    def list_warehouses(self, active_only: bool = True) -> list[WarehouseSummary]:
        """List registered storage warehouses."""
        warehouses = self.stock_repo.get_all_warehouses(active_only)
        return [
            WarehouseSummary(
                id=w.id,
                name=w.name,
                location=w.location,
                is_active=w.is_active,
            )
            for w in warehouses
        ]

    def receive_stock(
        self,
        product_id: str,
        warehouse_id: str,
        batch_no: str,
        quantity: float,
        uom_id: str | None = None,
        expiry_date: date | None = None,
        reference_id: str | None = None,
        actor_id: str | None = None,
    ) -> tuple[StockBatch, Any]:
        """
        Receive inbound stock for a product:
        - Converts received quantity from specified UoM to product's base UoM via UomService
        - Atomically writes StockBatch upsert and StockMovement(type=in) record
        """
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Received stock quantity must be greater than zero.",
            )

        if not batch_no or not batch_no.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch number is required for receiving stock.",
            )

        wh = self.stock_repo.get_warehouse_by_id(warehouse_id)
        if not wh:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Warehouse '{warehouse_id}' not found.",
            )

        base_qty = float(quantity)
        if self.uom_service:
            base_qty = self.uom_service.convert_to_base_uom(
                product_id=product_id,
                qty=quantity,
                uom_id=uom_id,
            )

        batch, movement = self.stock_repo.record_stock_receipt(
            product_id=product_id,
            warehouse_id=warehouse_id,
            batch_no=batch_no,
            quantity=base_qty,
            expiry_date=expiry_date,
            reference_id=reference_id,
            created_by=actor_id,
        )

        return batch, movement

    def adjust_stock(
        self, payload: StockAdjustmentCreateRequest, current_user: CurrentUser
    ) -> StockAdjustmentResponse:
        """
        Record a manual stock adjustment with validation and permission guards:
        - Reason is required (damage, loss, recount, other)
        - 'recount' reason strictly requires stock.recount / stock:recount permission or Owner role
        - Delta cannot be zero
        - Resulting batch quantity cannot be negative
        - Emits immutable stock_movements(type=adjustment) record and audit log
        """
        if payload.delta == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment delta cannot be zero.",
            )

        # Recount permission gate
        if payload.reason == AdjustmentReasonEnum.RECOUNT:
            has_recount_perm = (
                "stock:recount" in current_user.permissions
                or "stock.recount" in current_user.permissions
                or current_user.role.lower() == "owner"
            )
            if not has_recount_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Missing required permission for recount: stock.recount",
                )

        try:
            batch, movement, prev_qty, new_qty = self.stock_repo.record_stock_adjustment(
                product_id=payload.product_id,
                warehouse_id=payload.warehouse_id,
                batch_id=payload.batch_id,
                delta=payload.delta,
                reason=payload.reason.value,
                notes=payload.notes,
                created_by=current_user.email or current_user.id,
            )
        except ValueError as e:
            err_msg = str(e)
            if "not found" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=err_msg,
                ) from e
            if "negative" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=err_msg,
                ) from e
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            ) from e

        # Structured audit log
        if self.audit_repo:
            self.audit_repo.create_log(
                actor_id=current_user.id if hasattr(current_user, "id") else None,
                action="stock_adjusted",
                entity_type="stock_batch",
                entity_id=payload.batch_id,
                before_value={"quantity": prev_qty},
                after_value={
                    "quantity": new_qty,
                    "delta": payload.delta,
                    "reason": payload.reason.value,
                    "notes": payload.notes,
                },
            )

        return StockAdjustmentResponse(
            movement_id=movement.id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            batch_id=payload.batch_id,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            delta=payload.delta,
            reason=payload.reason,
            notes=payload.notes,
            created_at=movement.created_at,
            created_by=movement.created_by,
        )

    def list_movements(
        self,
        page: int = 1,
        page_size: int = 50,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        movement_type: str | None = None,
        start_date: Any | None = None,
        end_date: Any | None = None,
        search: str | None = None,
    ) -> StockMovementListResponse:
        """
        Fetch paginated stock movements with contextual human-readable labels.
        """
        raw_items, total = self.stock_repo.list_movements(
            page=page,
            page_size=page_size,
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )

        formatted_items: list[StockMovementListItemResponse] = []
        for item in raw_items:
            ref_type = item.get("reference_type")
            ref_id = item.get("reference_id")
            m_type = item.get("type", "").lower()

            human_label = f"{m_type.upper()}"
            if ref_type == "purchase_order":
                human_label = f"PO #{ref_id or '—'} (Goods Receipt)"
            elif ref_type == "sales_order":
                human_label = f"SO #{ref_id or '—'} (Fulfillment Dispatch)"
            elif ref_type == "sales_order_cancellation":
                human_label = f"SO #{ref_id or '—'} (Order Cancellation)"
            elif ref_type == "purchase_return":
                human_label = f"PR #{ref_id or '—'} (Supplier Return)"
            elif ref_type == "sales_return":
                human_label = f"RMA #{ref_id or '—'} (Retailer Return)"
            elif ref_type == "manual_adjustment":
                if ref_id and ":" in str(ref_id):
                    reason, notes = str(ref_id).split(":", 1)
                    human_label = f"Adjustment: {reason.capitalize()} ({notes})"
                elif ref_id:
                    human_label = f"Adjustment: {str(ref_id).capitalize()}"
                else:
                    human_label = "Manual Stock Adjustment"
            elif ref_id:
                human_label = f"{ref_type or m_type}: #{ref_id}"

            formatted_items.append(
                StockMovementListItemResponse(
                    id=item["id"],
                    product_id=item["product_id"],
                    product_name=item.get("product_name", "Unknown Product"),
                    product_sku=item.get("product_sku", ""),
                    warehouse_id=item["warehouse_id"],
                    warehouse_name=item.get("warehouse_name", "Unknown Warehouse"),
                    batch_id=item.get("batch_id"),
                    batch_no=item.get("batch_no"),
                    type=item["type"],
                    quantity=item["quantity"],
                    reference_type=ref_type,
                    reference_id=ref_id,
                    human_label=human_label,
                    created_by=item.get("created_by"),
                    created_at=item["created_at"],
                )
            )

        pages = max(1, math.ceil(total / page_size)) if page_size > 0 else 1
        return StockMovementListResponse(
            items=formatted_items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
