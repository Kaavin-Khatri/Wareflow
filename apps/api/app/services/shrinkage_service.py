"""
Shrinkage & Inventory Loss Analytics Service (Step 16.2).

Computes damage, loss, and discrepancy write-offs from the immutable stock adjustment ledger.
Follows SOLID Principles:
- Single Responsibility: Calculates shrinkage totals, loss rates, and dimension rollups.
- Open/Closed: Extensible to insurance claims and root-cause classification.
- Dependency Inversion: Injected with repository interfaces.
"""

from datetime import datetime, timedelta, timezone

from app.models.inventory import StockMovementTypeEnum
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.schemas.analytics import (
    ShrinkageItem,
    ShrinkageResponse,
    ShrinkageSummary,
)


class ShrinkageService:
    """Service analyzing inventory shrinkage, damage write-offs, and loss rates."""

    def __init__(
        self,
        stock_repo: StockRepositoryInterface,
        product_repo: ProductRepositoryInterface,
    ) -> None:
        self.stock_repo = stock_repo
        self.product_repo = product_repo

    def get_shrinkage(
        self, group_by: str = "product", period: str = "30d", as_of: datetime | None = None
    ) -> ShrinkageResponse:
        """
        Calculate shrinkage loss from negative stock adjustments.

        Args:
            group_by: Dimension to roll up by ('product' or 'category').
            period: Time window ('7d', '30d', '90d', '12m', 'all').
            as_of: Reference timestamp (defaults to current UTC).
        """
        now = as_of or datetime.now(timezone.utc)
        cutoff_date = self._get_cutoff_date(now, period)

        products = self.product_repo.list_products(limit=1000)
        product_map = {}
        for p in products:
            p_id = p.id if hasattr(p, "id") else p["id"]
            product_map[p_id] = p

        # Calculate current total stock value for loss rate computation
        total_current_stock_val = 0.0
        for p_id, p in product_map.items():
            on_hand = float(self.stock_repo.get_on_hand(p_id))
            cost = float(getattr(p, "cost_price", 0.0) if hasattr(p, "cost_price") else p.get("cost_price", 0.0) or 0.0)
            total_current_stock_val += on_hand * cost

        # Fetch adjustment movements within the period
        movements, _ = self.stock_repo.list_movements(
            page=1,
            page_size=5000,
            movement_type=StockMovementTypeEnum.ADJUSTMENT.value,
            start_date=cutoff_date,
        )

        # Filter only negative adjustments (losses/damage/shrinkage)
        shrinkage_movements = []
        for m in movements:
            qty = float(m.get("quantity", 0.0))
            if qty < 0:
                shrinkage_movements.append(m)

        normalized_group_by = group_by.lower().strip()
        if normalized_group_by == "category":
            items, summary = self._aggregate_by_category(
                shrinkage_movements, product_map, total_current_stock_val
            )
        else:
            normalized_group_by = "product"
            items, summary = self._aggregate_by_product(
                shrinkage_movements, product_map, total_current_stock_val
            )

        return ShrinkageResponse(
            period=period,
            group_by=normalized_group_by,
            summary=summary,
            items=items,
            generated_at=now,
        )

    def _get_cutoff_date(self, now: datetime, period: str) -> datetime | None:
        p = period.lower().strip()
        if p == "7d":
            return now - timedelta(days=7)
        if p == "30d":
            return now - timedelta(days=30)
        if p == "90d":
            return now - timedelta(days=90)
        if p in ("12m", "365d", "1y"):
            return now - timedelta(days=365)
        if p == "all":
            return None
        return now - timedelta(days=30)

    def _aggregate_by_product(
        self, movements: list, product_map: dict, total_stock_val: float
    ) -> tuple[list[ShrinkageItem], ShrinkageSummary]:
        groups: dict[str, dict] = {}
        total_loss_val = 0.0
        total_units_lost = 0.0
        total_incidents = len(movements)

        for m in movements:
            p_id = m.get("product_id")
            prod = product_map.get(p_id)
            cost_price = (
                float(getattr(prod, "cost_price", 0.0) if hasattr(prod, "cost_price") else prod.get("cost_price", 0.0) or 0.0)
                if prod
                else 0.0
            )
            qty_lost = abs(float(m.get("quantity", 0.0)))
            loss_val = qty_lost * cost_price

            total_loss_val += loss_val
            total_units_lost += qty_lost

            if p_id not in groups:
                if prod:
                    p_name = getattr(prod, "name", "") if hasattr(prod, "name") else prod.get("name", "")
                    p_sku = getattr(prod, "sku", "") if hasattr(prod, "sku") else prod.get("sku", "")
                    cat_val = getattr(prod, "category", None) if hasattr(prod, "category") else prod.get("category")
                    cat_name = cat_val.name if hasattr(cat_val, "name") else (cat_val if isinstance(cat_val, str) else "Uncategorized")
                else:
                    p_name = m.get("product_name") or f"Product {p_id[:8]}"
                    p_sku = m.get("product_sku") or "SKU-N/A"
                    cat_name = "Uncategorized"

                groups[p_id] = {
                    "id": p_id,
                    "name": p_name,
                    "secondary_info": f"SKU: {p_sku}",
                    "badge": cat_name or "Uncategorized",
                    "units_lost": 0.0,
                    "incidents": 0,
                    "loss_val": 0.0,
                }

            g = groups[p_id]
            g["units_lost"] += qty_lost
            g["incidents"] += 1
            g["loss_val"] += loss_val

        items: list[ShrinkageItem] = []
        for g in groups.values():
            share = (
                round((g["loss_val"] / total_loss_val) * 100.0, 1) if total_loss_val > 0 else 0.0
            )

            items.append(
                ShrinkageItem(
                    id=g["id"],
                    name=g["name"],
                    secondary_info=g["secondary_info"],
                    badge=g["badge"],
                    units_lost=round(g["units_lost"], 2),
                    incidents_count=g["incidents"],
                    shrinkage_value_inr=round(g["loss_val"], 2),
                    pct_of_total_shrinkage=share,
                )
            )

        # Sort descending by shrinkage value
        items.sort(key=lambda x: (-x.shrinkage_value_inr, x.name.lower()))

        shrinkage_rate = (
            round((total_loss_val / (total_stock_val + total_loss_val)) * 100.0, 2)
            if (total_stock_val + total_loss_val) > 0
            else 0.0
        )

        summary = ShrinkageSummary(
            total_shrinkage_value_inr=round(total_loss_val, 2),
            total_units_lost=round(total_units_lost, 2),
            shrinkage_rate_pct=shrinkage_rate,
            damage_incidents_count=total_incidents,
        )

        return items, summary

    def _aggregate_by_category(
        self, movements: list, product_map: dict, total_stock_val: float
    ) -> tuple[list[ShrinkageItem], ShrinkageSummary]:
        groups: dict[str, dict] = {}
        total_loss_val = 0.0
        total_units_lost = 0.0
        total_incidents = len(movements)

        for m in movements:
            p_id = m.get("product_id")
            prod = product_map.get(p_id)
            cost_price = (
                float(getattr(prod, "cost_price", 0.0) if hasattr(prod, "cost_price") else prod.get("cost_price", 0.0) or 0.0)
                if prod
                else 0.0
            )
            qty_lost = abs(float(m.get("quantity", 0.0)))
            loss_val = qty_lost * cost_price

            if prod:
                cat_id = str(getattr(prod, "category_id", None) if hasattr(prod, "category_id") else prod.get("category_id")) or "uncategorized"
                cat_val = getattr(prod, "category", None) if hasattr(prod, "category") else prod.get("category")
                cat_name = cat_val.name if hasattr(cat_val, "name") else (cat_val if isinstance(cat_val, str) else "Uncategorized")
            else:
                cat_id = "uncategorized"
                cat_name = "Uncategorized"

            total_loss_val += loss_val
            total_units_lost += qty_lost

            if cat_id not in groups:
                groups[cat_id] = {
                    "id": cat_id,
                    "name": cat_name or "Uncategorized",
                    "products_set": set(),
                    "units_lost": 0.0,
                    "incidents": 0,
                    "loss_val": 0.0,
                }

            g = groups[cat_id]
            g["products_set"].add(p_id)
            g["units_lost"] += qty_lost
            g["incidents"] += 1
            g["loss_val"] += loss_val

        items: list[ShrinkageItem] = []
        for g in groups.values():
            share = (
                round((g["loss_val"] / total_loss_val) * 100.0, 1) if total_loss_val > 0 else 0.0
            )
            prod_count = len(g["products_set"])

            items.append(
                ShrinkageItem(
                    id=g["id"],
                    name=g["name"],
                    secondary_info=f"{prod_count} Affected Products",
                    badge="CATEGORY",
                    units_lost=round(g["units_lost"], 2),
                    incidents_count=g["incidents"],
                    shrinkage_value_inr=round(g["loss_val"], 2),
                    pct_of_total_shrinkage=share,
                )
            )

        items.sort(key=lambda x: (-x.shrinkage_value_inr, x.name.lower()))

        shrinkage_rate = (
            round((total_loss_val / (total_stock_val + total_loss_val)) * 100.0, 2)
            if (total_stock_val + total_loss_val) > 0
            else 0.0
        )

        summary = ShrinkageSummary(
            total_shrinkage_value_inr=round(total_loss_val, 2),
            total_units_lost=round(total_units_lost, 2),
            shrinkage_rate_pct=shrinkage_rate,
            damage_incidents_count=total_incidents,
        )

        return items, summary
