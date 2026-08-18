from datetime import date, datetime, timedelta
from typing import Any

from app.repositories.interfaces.stock_analytics_repository import (
    StockAnalyticsRepositoryInterface,
)
from app.schemas.stock_analytics import (
    AvgCostTrendResponse,
    CategorySpendItem,
    CategorySpendResponse,
    CategoryValueItem,
    ExpiryTimelineResponse,
    ExpiryWindowItem,
    HealthBandItem,
    MonthlySpendItem,
    ProductCostPoint,
    ProductCostTrendItem,
    SpendTrendResponse,
    StockHealthDistributionResponse,
    StockValueSummaryResponse,
    SupplierSpendItem,
    SupplierSpendResponse,
    TopProductItem,
    TopProductsResponse,
    WarehouseValueItem,
)


class StockAnalyticsService:
    """Domain service for aggregated stock metrics and visual analytics."""

    def __init__(self, analytics_repo: StockAnalyticsRepositoryInterface) -> None:
        self.repo = analytics_repo

    def get_value_summary(self) -> StockValueSummaryResponse:
        """Calculate total stock value and breakdowns by category and warehouse."""
        rows = self.repo.get_stock_valuation_data()
        total_val = sum(r["quantity"] * r["cost_price"] for r in rows)
        total_units = sum(r["quantity"] for r in rows)
        distinct_prods = {r["product_id"] for r in rows}

        by_cat = self._aggregate_by_category(rows, total_val)
        by_wh = self._aggregate_by_warehouse(rows, total_val)

        return StockValueSummaryResponse(
            total_stock_value=round(total_val, 2),
            total_units=round(total_units, 2),
            total_products=len(distinct_prods),
            by_category=by_cat,
            by_warehouse=by_wh,
        )

    def _aggregate_by_category(
        self, rows: list[dict[str, Any]], total_val: float
    ) -> list[CategoryValueItem]:
        cat_map: dict[str, dict[str, Any]] = {}
        for r in rows:
            cid = r["category_id"] or "uncategorized"
            cname = r["category_name"] or "Uncategorized"
            if cid not in cat_map:
                cat_map[cid] = {"name": cname, "val": 0.0, "qty": 0.0, "prods": set()}
            cat_map[cid]["val"] += r["quantity"] * r["cost_price"]
            cat_map[cid]["qty"] += r["quantity"]
            cat_map[cid]["prods"].add(r["product_id"])

        items: list[CategoryValueItem] = []
        for cid, data in cat_map.items():
            pct = (data["val"] / total_val * 100.0) if total_val > 0 else 0.0
            items.append(
                CategoryValueItem(
                    category_id=None if cid == "uncategorized" else cid,
                    category_name=data["name"],
                    total_value=round(data["val"], 2),
                    total_units=round(data["qty"], 2),
                    product_count=len(data["prods"]),
                    percentage=round(pct, 1),
                )
            )
        items.sort(key=lambda x: x.total_value, reverse=True)
        return items

    def _aggregate_by_warehouse(
        self, rows: list[dict[str, Any]], total_val: float
    ) -> list[WarehouseValueItem]:
        wh_map: dict[str, dict[str, Any]] = {}
        for r in rows:
            wid = r["warehouse_id"]
            wname = r["warehouse_name"]
            if wid not in wh_map:
                wh_map[wid] = {"name": wname, "val": 0.0, "qty": 0.0, "batches": 0}
            wh_map[wid]["val"] += r["quantity"] * r["cost_price"]
            wh_map[wid]["qty"] += r["quantity"]
            wh_map[wid]["batches"] += 1

        items: list[WarehouseValueItem] = []
        for wid, data in wh_map.items():
            pct = (data["val"] / total_val * 100.0) if total_val > 0 else 0.0
            items.append(
                WarehouseValueItem(
                    warehouse_id=wid,
                    warehouse_name=data["name"],
                    total_value=round(data["val"], 2),
                    total_units=round(data["qty"], 2),
                    batch_count=data["batches"],
                    percentage=round(pct, 1),
                )
            )
        items.sort(key=lambda x: x.total_value, reverse=True)
        return items

    def get_health_distribution(self) -> StockHealthDistributionResponse:
        """Categorize all active products into stock health status bands."""
        rows = self.repo.get_health_distribution_data()
        counts = {"healthy": 0, "low": 0, "critical": 0, "out_of_stock": 0}

        for r in rows:
            band = self.classify_product_health(r["total_on_hand"], r["reorder_point"])
            counts[band] += 1

        total = len(rows)
        bands = self._build_health_band_items(counts, total)

        return StockHealthDistributionResponse(
            healthy_count=counts["healthy"],
            low_count=counts["low"],
            critical_count=counts["critical"],
            out_of_stock_count=counts["out_of_stock"],
            total_products=total,
            bands=bands,
        )

    @staticmethod
    def classify_product_health(on_hand: float, reorder_point: float) -> str:
        """Classify single product into health band according to Step 5.3 rules."""
        if on_hand <= 0:
            return "out_of_stock"
        if reorder_point <= 0:
            return "healthy"
        if on_hand <= 0.25 * reorder_point:
            return "critical"
        if on_hand <= reorder_point:
            return "low"
        return "healthy"

    def _build_health_band_items(self, counts: dict[str, int], total: int) -> list[HealthBandItem]:
        configs = [
            ("healthy", "Healthy Stock", "Above reorder threshold"),
            ("low", "Low Stock", "At or below reorder threshold"),
            ("critical", "Critical", "25% or below reorder point"),
            ("out_of_stock", "Out of Stock", "0 units available"),
        ]
        items: list[HealthBandItem] = []
        for key, label, desc in configs:
            c = counts[key]
            pct = (c / total * 100.0) if total > 0 else 0.0
            items.append(
                HealthBandItem(
                    status=key,
                    label=label,
                    count=c,
                    percentage=round(pct, 1),
                    description=desc,
                )
            )
        return items

    def get_top_products(self, limit: int = 10) -> TopProductsResponse:
        """Retrieve top products sorted by total tied-up capital and volume."""
        raw_items = self.repo.get_top_products_data()
        items = [TopProductItem(**r) for r in raw_items]

        by_val = sorted(items, key=lambda x: x.total_value, reverse=True)[:limit]
        by_qty = sorted(items, key=lambda x: x.total_on_hand, reverse=True)[:limit]

        return TopProductsResponse(by_value=by_val, by_quantity=by_qty)

    def get_expiry_timeline(self) -> ExpiryTimelineResponse:
        """Aggregate active stock batches into forward-looking expiry windows."""
        rows = self.repo.get_batch_expiry_data()
        today = date.today()
        d7 = today + timedelta(days=7)
        d30 = today + timedelta(days=30)
        d90 = today + timedelta(days=90)

        groups = {
            "expired": {"label": "Expired Batches", "count": 0, "qty": 0.0, "val": 0.0},
            "this_week": {"label": "Expiring ≤ 7 Days", "count": 0, "qty": 0.0, "val": 0.0},
            "this_month": {"label": "Expiring 8-30 Days", "count": 0, "qty": 0.0, "val": 0.0},
            "next_3_months": {"label": "Expiring 31-90 Days", "count": 0, "qty": 0.0, "val": 0.0},
            "later": {"label": "Horizon > 90 Days", "count": 0, "qty": 0.0, "val": 0.0},
            "no_expiry": {"label": "No Expiry Limit", "count": 0, "qty": 0.0, "val": 0.0},
        }

        for r in rows:
            exp = r.get("expiry_date")
            key = self._resolve_expiry_key(exp, today, d7, d30, d90)
            val = float(r["quantity"]) * float(r["cost_price"] or 0.0)
            groups[key]["count"] += 1
            groups[key]["qty"] += float(r["quantity"])
            groups[key]["val"] += val

        windows = [
            ExpiryWindowItem(
                window_key=k,
                label=v["label"],
                batch_count=v["count"],
                total_quantity=round(v["qty"], 2),
                total_value=round(v["val"], 2),
            )
            for k, v in groups.items()
        ]

        soon_count = (
            groups["expired"]["count"]
            + groups["this_week"]["count"]
            + groups["this_month"]["count"]
        )
        soon_val = (
            groups["expired"]["val"] + groups["this_week"]["val"] + groups["this_month"]["val"]
        )

        return ExpiryTimelineResponse(
            windows=windows,
            total_expiring_soon_count=soon_count,
            total_expiring_soon_value=round(soon_val, 2),
        )

    @staticmethod
    def _resolve_expiry_key(exp: date | None, today: date, d7: date, d30: date, d90: date) -> str:
        if exp is None:
            return "no_expiry"
        if exp < today:
            return "expired"
        if exp <= d7:
            return "this_week"
        if exp <= d30:
            return "this_month"
        if exp <= d90:
            return "next_3_months"
        return "later"

    # --- Step 6.2: Purchasing Spend Service Methods ---

    def get_spend_trend(self, months: int = 12) -> SpendTrendResponse:
        """Calculate 12-month purchasing spend trend."""
        raw_rows = self.repo.get_spend_trend_data(months)
        buckets: dict[str, dict[str, Any]] = {}

        # Pre-seed last N months
        now = datetime.now()
        for i in range(months - 1, -1, -1):
            # Calculate month approx
            y = now.year
            m = now.month - i
            while m <= 0:
                m += 12
                y -= 1
            key = f"{y:04d}-{m:02d}"
            label = datetime(y, m, 1).strftime("%b %Y")
            buckets[key] = {
                "month": key,
                "label": label,
                "spend": 0.0,
                "orders": set(),
                "units": 0.0,
            }

        # Aggregate raw rows
        for r in raw_rows:
            od = r.get("order_date") or now
            m_key = od.strftime("%Y-%m") if hasattr(od, "strftime") else str(od)[:7]

            if m_key not in buckets:
                try:
                    dt = datetime.strptime(m_key, "%Y-%m")
                    label = dt.strftime("%b %Y")
                except ValueError:
                    label = m_key
                buckets[m_key] = {
                    "month": m_key,
                    "label": label,
                    "spend": 0.0,
                    "orders": set(),
                    "units": 0.0,
                }

            spend = float(r["qty_received"]) * float(r["unit_cost"])
            buckets[m_key]["spend"] += spend
            buckets[m_key]["units"] += float(r["qty_received"])
            if r.get("po_id"):
                buckets[m_key]["orders"].add(r["po_id"])

        sorted_keys = sorted(buckets.keys())[-months:]
        trend_items: list[MonthlySpendItem] = []
        total_spend = 0.0

        for k in sorted_keys:
            b = buckets[k]
            sp = round(b["spend"], 2)
            total_spend += sp
            trend_items.append(
                MonthlySpendItem(
                    month=b["month"],
                    label=b["label"],
                    total_spend=sp,
                    order_count=len(b["orders"]),
                    received_units=round(b["units"], 2),
                )
            )

        avg_spend = round(total_spend / max(len(trend_items), 1), 2)
        return SpendTrendResponse(
            monthly_trend=trend_items,
            total_period_spend=round(total_spend, 2),
            avg_monthly_spend=avg_spend,
        )

    def get_spend_by_supplier(self, months: int = 12) -> SupplierSpendResponse:
        """Calculate spend breakdown by supplier."""
        raw_rows = self.repo.get_spend_by_supplier_data(months)
        sup_map: dict[str, dict[str, Any]] = {}
        total_spend = 0.0

        for r in raw_rows:
            sid = str(r.get("supplier_id") or "unknown")
            sname = str(r.get("supplier_name") or "Unknown Supplier")
            spend = float(r["qty_received"]) * float(r["unit_cost"])
            total_spend += spend

            if sid not in sup_map:
                sup_map[sid] = {"name": sname, "spend": 0.0, "orders": set()}
            sup_map[sid]["spend"] += spend
            if r.get("po_id"):
                sup_map[sid]["orders"].add(r["po_id"])

        items: list[SupplierSpendItem] = []
        for sid, data in sup_map.items():
            pct = (data["spend"] / total_spend * 100.0) if total_spend > 0 else 0.0
            items.append(
                SupplierSpendItem(
                    supplier_id=sid,
                    supplier_name=data["name"],
                    total_spend=round(data["spend"], 2),
                    order_count=len(data["orders"]),
                    percentage=round(pct, 1),
                )
            )
        items.sort(key=lambda x: x.total_spend, reverse=True)
        return SupplierSpendResponse(
            suppliers=items,
            total_spend=round(total_spend, 2),
        )

    def get_spend_by_category(self, months: int = 12) -> CategorySpendResponse:
        """Calculate spend breakdown by product category."""
        raw_rows = self.repo.get_spend_by_category_data(months)
        cat_map: dict[str, dict[str, Any]] = {}
        total_spend = 0.0

        for r in raw_rows:
            cid = str(r.get("category_id") or "uncategorized")
            cname = str(r.get("category_name") or "Uncategorized")
            spend = float(r["qty_received"]) * float(r["unit_cost"])
            qty = float(r["qty_received"])
            total_spend += spend

            if cid not in cat_map:
                cat_map[cid] = {"name": cname, "spend": 0.0, "units": 0.0}
            cat_map[cid]["spend"] += spend
            cat_map[cid]["units"] += qty

        items: list[CategorySpendItem] = []
        for cid, data in cat_map.items():
            pct = (data["spend"] / total_spend * 100.0) if total_spend > 0 else 0.0
            items.append(
                CategorySpendItem(
                    category_id=None if cid == "uncategorized" else cid,
                    category_name=data["name"],
                    total_spend=round(data["spend"], 2),
                    received_units=round(data["units"], 2),
                    percentage=round(pct, 1),
                )
            )
        items.sort(key=lambda x: x.total_spend, reverse=True)
        return CategorySpendResponse(
            categories=items,
            total_spend=round(total_spend, 2),
        )

    def get_avg_cost_trend(self, product_ids: list[str] | None = None) -> AvgCostTrendResponse:
        """Calculate cost price movement and percentage price creep."""
        raw_rows = self.repo.get_product_cost_history_data(product_ids)
        items: list[ProductCostTrendItem] = []

        for r in raw_rows:
            cost_pts = [ProductCostPoint(**pt) for pt in r.get("cost_points", [])]
            base_cost = float(r.get("current_cost_price", 0.0))

            if len(cost_pts) <= 1:
                pct_change = 0.0
            else:
                first_cost = cost_pts[0].cost_price
                last_cost = cost_pts[-1].cost_price
                pct_change = (
                    ((last_cost - first_cost) / first_cost * 100.0) if first_cost > 0 else 0.0
                )

            items.append(
                ProductCostTrendItem(
                    product_id=r["product_id"],
                    sku=r["sku"],
                    name=r["name"],
                    current_cost_price=base_cost,
                    cost_history=cost_pts,
                    pct_change=round(pct_change, 1),
                )
            )

        return AvgCostTrendResponse(products=items)
