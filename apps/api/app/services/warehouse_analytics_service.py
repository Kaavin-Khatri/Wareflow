"""
Warehouse Analytics & Breakdown Service (Step 16.2).

Computes per-warehouse inventory valuation, batch concentrations, and 30-day movement throughput.
Follows SOLID Principles:
- Single Responsibility: Analyzes storage metrics and throughput per facility.
- Open/Closed: Extensible to square footage density and temperature zone tracking.
- Dependency Inversion: Injected with repository interfaces.
"""

from datetime import datetime, timedelta, timezone

from app.models.inventory import StockMovementTypeEnum
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.schemas.analytics import (
    WarehouseBreakdownResponse,
    WarehouseBreakdownSummary,
    WarehouseMetricsItem,
)


class WarehouseAnalyticsService:
    """Service providing multi-facility inventory valuation and 30-day throughput breakdown."""

    def __init__(
        self,
        stock_repo: StockRepositoryInterface,
        product_repo: ProductRepositoryInterface,
    ) -> None:
        self.stock_repo = stock_repo
        self.product_repo = product_repo

    def get_warehouse_breakdown(
        self, as_of: datetime | None = None
    ) -> WarehouseBreakdownResponse:
        """Calculate inventory holding values and 30-day throughput per warehouse facility."""
        now = as_of or datetime.now(timezone.utc)
        cutoff_30d = now - timedelta(days=30)

        warehouses = self.stock_repo.get_all_warehouses(active_only=False)
        products = self.product_repo.list_products(limit=1000)
        product_cost_map = {}
        for p in products:
            p_id = p.id if hasattr(p, "id") else p["id"]
            cost = float(getattr(p, "cost_price", 0.0) if hasattr(p, "cost_price") else p.get("cost_price", 0.0) or 0.0)
            product_cost_map[p_id] = cost

        # Fetch all stock movements for the 30-day window
        movements, _ = self.stock_repo.list_movements(page=1, page_size=5000, start_date=cutoff_30d)

        # 1. Compute per-warehouse holdings and valuation
        wh_metrics: dict[str, dict] = {}
        for wh in warehouses:
            wh_metrics[wh.id] = {
                "id": wh.id,
                "name": wh.name,
                "location": wh.location,
                "is_active": wh.is_active,
                "products_set": set(),
                "total_units": 0.0,
                "total_val": 0.0,
                "inbound_30d": 0.0,
                "outbound_30d": 0.0,
                "movements_30d": 0,
            }

        # Aggregate current stock overview data
        overview_data = self.stock_repo.get_stock_overview_data()
        for row in overview_data:
            prod = row.get("product")
            if prod:
                p_id = prod.id if hasattr(prod, "id") else (prod.get("id") if isinstance(prod, dict) else str(prod))
            else:
                p_id = row.get("product_id")

            cost = product_cost_map.get(p_id, 0.0)
            wh_list = row.get("warehouses") or row.get("warehouse_breakdown") or []

            for wh_entry in wh_list:
                w_id = wh_entry.get("warehouse_id")
                qty = float(wh_entry.get("on_hand", wh_entry.get("quantity", 0.0)))

                if w_id in wh_metrics and qty > 0:
                    wh_metrics[w_id]["products_set"].add(p_id)
                    wh_metrics[w_id]["total_units"] += qty
                    wh_metrics[w_id]["total_val"] += qty * cost

        # 2. Aggregate 30-day movement throughput
        for m in movements:
            w_id = m.get("warehouse_id")
            if not w_id or w_id not in wh_metrics:
                continue

            m_type = m.get("type")
            qty = float(m.get("quantity", 0.0))

            wh_metrics[w_id]["movements_30d"] += 1

            if m_type in (StockMovementTypeEnum.IN.value, "in", StockMovementTypeEnum.RETURN_IN.value, "return_in"):
                wh_metrics[w_id]["inbound_30d"] += abs(qty)
            elif m_type in (StockMovementTypeEnum.OUT.value, "out", StockMovementTypeEnum.RETURN_OUT.value, "return_out"):
                wh_metrics[w_id]["outbound_30d"] += abs(qty)
            elif m_type == StockMovementTypeEnum.TRANSFER.value or m_type == "transfer":
                if qty > 0:
                    wh_metrics[w_id]["inbound_30d"] += qty
                else:
                    wh_metrics[w_id]["outbound_30d"] += abs(qty)

        # 3. Calculate company totals
        company_total_units = sum(w["total_units"] for w in wh_metrics.values())
        company_total_val = sum(w["total_val"] for w in wh_metrics.values())
        total_inbound = sum(w["inbound_30d"] for w in wh_metrics.values())
        total_outbound = sum(w["outbound_30d"] for w in wh_metrics.values())

        items: list[WarehouseMetricsItem] = []
        for w in wh_metrics.values():
            share_pct = (
                round((w["total_val"] / company_total_val) * 100.0, 1)
                if company_total_val > 0
                else 0.0
            )

            items.append(
                WarehouseMetricsItem(
                    warehouse_id=w["id"],
                    warehouse_name=w["name"],
                    location=w["location"],
                    is_active=w["is_active"],
                    total_products_stored=len(w["products_set"]),
                    total_stock_units=round(w["total_units"], 2),
                    total_stock_value_inr=round(w["total_val"], 2),
                    inbound_30d_units=round(w["inbound_30d"], 2),
                    outbound_30d_units=round(w["outbound_30d"], 2),
                    movement_count_30d=w["movements_30d"],
                    valuation_share_pct=share_pct,
                )
            )

        # Sort descending by inventory valuation
        items.sort(key=lambda x: (-x.total_stock_value_inr, x.warehouse_name.lower()))

        summary = WarehouseBreakdownSummary(
            total_warehouses=len(warehouses),
            company_total_stock_units=round(company_total_units, 2),
            company_total_valuation_inr=round(company_total_val, 2),
            total_30d_inbound_units=round(total_inbound, 2),
            total_30d_outbound_units=round(total_outbound, 2),
        )

        return WarehouseBreakdownResponse(
            summary=summary,
            warehouses=items,
            generated_at=now,
        )
