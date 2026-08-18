"""Stock domain service for multi-warehouse batch visibility and inventory health."""

from datetime import date
from typing import Any, Literal

from fastapi import HTTPException, status

from app.models.catalog import Product
from app.models.warehouse import StockBatch
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
from app.services.uom_service import UomService


class StockService:
    """Domain service managing inventory on-hand balances, batch tracking, and status calculations."""

    def __init__(
        self,
        stock_repo: StockRepositoryInterface,
        uom_repo: UomRepositoryInterface | None = None,
        uom_service: UomService | None = None,
    ):
        self.stock_repo = stock_repo
        self.uom_repo = uom_repo
        self.uom_service = uom_service or (UomService(uom_repo=uom_repo) if uom_repo else None)

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
