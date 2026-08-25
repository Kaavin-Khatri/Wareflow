"""Generic Period-over-Period and Year-over-Year Comparison Service (Step 16.3).

Provides unified comparison logic across all business KPIs (Revenue, Margin,
Turnover, Stock Value, Shrinkage, Units Sold), avoiding ad-hoc calculations.
"""

from datetime import UTC, datetime, timedelta

from app.repositories.interfaces.product_repository import (
    ProductRepositoryInterface,
)
from app.repositories.interfaces.sales_order_repository import (
    SalesOrderRepositoryInterface,
)
from app.repositories.interfaces.stock_repository import (
    StockRepositoryInterface,
)
from app.schemas.analytics import (
    ComparisonMetricResult,
    PeriodComparisonsResponse,
)


class ComparisonService:
    """Generic period comparison engine implementing period-over-period and YoY analysis."""

    def __init__(
        self,
        sales_order_repo: SalesOrderRepositoryInterface,
        stock_repo: StockRepositoryInterface,
        product_repo: ProductRepositoryInterface,
    ) -> None:
        self.sales_order_repo = sales_order_repo
        self.stock_repo = stock_repo
        self.product_repo = product_repo

    @staticmethod
    def compute_metric_delta(
        metric_key: str,
        metric_label: str,
        current: float,
        prior: float,
        prior_year: float | None = None,
        higher_is_better: bool = True,
        period_label: str = "vs prior period",
        is_currency: bool = False,
        is_pct: bool = False,
    ) -> ComparisonMetricResult:
        """Pure calculation helper for period delta and percentage change."""
        current_val = round(float(current), 2)
        prior_val = round(float(prior), 2)
        delta_val = round(current_val - prior_val, 2)

        # Period-over-period percentage calculation with zero-guard
        if prior_val == 0.0:
            delta_pct = 0.0 if current_val == 0.0 else (100.0 if current_val > 0.0 else -100.0)
        else:
            delta_pct = round(((current_val - prior_val) / abs(prior_val)) * 100.0, 2)

        # Year-over-year percentage calculation if available
        delta_year_pct = None
        if prior_year is not None:
            prior_year_val = round(float(prior_year), 2)
            if prior_year_val == 0.0:
                delta_year_pct = (
                    100.0 if current_val > 0.0 else (0.0 if current_val == 0.0 else -100.0)
                )
            else:
                delta_year_pct = round(
                    ((current_val - prior_year_val) / abs(prior_year_val)) * 100.0, 2
                )

        # Trend direction
        if delta_pct > 0.05:
            trend = "up"
        elif delta_pct < -0.05:
            trend = "down"
        else:
            trend = "flat"

        # Polarity check: is the movement desirable?
        if trend == "up":
            is_positive = higher_is_better
        elif trend == "down":
            is_positive = not higher_is_better
        else:
            is_positive = True

        # Formatted string representations
        if is_currency:
            formatted_curr = f"₹{current_val:,.0f}"
            formatted_pr = f"₹{prior_val:,.0f}"
        elif is_pct:
            formatted_curr = f"{current_val:.1f}%"
            formatted_pr = f"{prior_val:.1f}%"
        else:
            formatted_curr = (
                f"{current_val:,.1f}" if current_val % 1 != 0 else f"{int(current_val):,}"
            )
            formatted_pr = (
                f"{prior_val:,.1f}" if prior_val % 1 != 0 else f"{int(prior_val):,}"
            )

        return ComparisonMetricResult(
            metric_key=metric_key,
            metric_label=metric_label,
            current_value=current_val,
            prior_value=prior_val,
            prior_year_value=round(float(prior_year), 2) if prior_year is not None else None,
            delta_value=delta_val,
            delta_pct=delta_pct,
            delta_year_pct=delta_year_pct,
            trend=trend,
            is_positive=is_positive,
            higher_is_better=higher_is_better,
            period_label=period_label,
            formatted_current=formatted_curr,
            formatted_prior=formatted_pr,
        )

    def get_period_comparisons(
        self, period: str = "30d", as_of: datetime | None = None
    ) -> PeriodComparisonsResponse:
        """Compute full scorecard of comparative metrics across current and prior windows."""
        now = as_of or datetime.now(UTC)

        # 1. Resolve date windows
        days_map = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}
        window_days = days_map.get(period.lower(), 30)

        current_end = now
        current_start = now - timedelta(days=window_days)

        prior_end = current_start
        prior_start = prior_end - timedelta(days=window_days)

        yoy_end = now - timedelta(days=365)
        yoy_start = yoy_end - timedelta(days=window_days)

        # 2. Build product cost mapping
        products = self.product_repo.list_products(limit=1000)
        product_cost_map: dict[str, float] = {}
        for p in products:
            p_id = p.id if hasattr(p, "id") else p["id"]
            cost = float(
                getattr(p, "cost_price", 0.0)
                if hasattr(p, "cost_price")
                else p.get("cost_price", 0.0) or 0.0
            )
            product_cost_map[p_id] = cost

        # 3. Aggregate sales orders across windows
        # Fetch non-draft/cancelled orders
        if hasattr(self.sales_order_repo, "list_all"):
            so_res = self.sales_order_repo.list_all(limit=10000)
            all_orders = so_res[0] if isinstance(so_res, tuple) else so_res
        elif hasattr(self.sales_order_repo, "list_sales_orders"):
            all_orders = self.sales_order_repo.list_sales_orders()
        else:
            all_orders = []

        eligible_orders = [
            o
            for o in all_orders
            if (o.status.value.upper() if hasattr(o.status, "value") else str(getattr(o, "status", "")).upper())
            not in ("DRAFT", "CANCELLED", "VOID")
        ]

        def aggregate_order_metrics(start_dt: datetime, end_dt: datetime) -> dict[str, float]:
            tot_rev = 0.0
            tot_cost = 0.0
            tot_units = 0.0

            for o in eligible_orders:
                created = (
                    getattr(o, "order_date", None) or getattr(o, "created_at", None)
                    if hasattr(o, "order_date") or hasattr(o, "created_at")
                    else (o.get("order_date") or o.get("created_at"))
                )
                if not created:
                    continue
                if isinstance(created, str):
                    try:
                        created = datetime.fromisoformat(created)
                    except ValueError:
                        continue
                if created.tzinfo is None:
                    created = created.replace(tzinfo=UTC)

                if start_dt <= created <= end_dt:
                    items = o.items if hasattr(o, "items") else o.get("items", [])
                    for it in items:
                        p_id = it.product_id if hasattr(it, "product_id") else it.get("product_id")
                        qty = float(
                            getattr(it, "qty", None) or getattr(it, "quantity", None)
                            if hasattr(it, "qty") or hasattr(it, "quantity")
                            else (it.get("qty") or it.get("quantity") or 0.0)
                        )
                        price = float(
                            it.unit_price
                            if hasattr(it, "unit_price")
                            else it.get("unit_price", 0.0)
                        )

                        tot_rev += qty * price
                        tot_units += qty
                        tot_cost += qty * product_cost_map.get(p_id, 0.0)

            margin_inr = tot_rev - tot_cost
            margin_pct = (margin_inr / tot_rev * 100.0) if tot_rev > 0 else 0.0
            return {
                "revenue": tot_rev,
                "cost": tot_cost,
                "margin_inr": margin_inr,
                "margin_pct": margin_pct,
                "units_sold": tot_units,
            }

        curr_sales = aggregate_order_metrics(current_start, current_end)
        prior_sales = aggregate_order_metrics(prior_start, prior_end)
        yoy_sales = aggregate_order_metrics(yoy_start, yoy_end)

        # 4. Inventory Valuation
        overview_data = self.stock_repo.get_stock_overview_data()
        total_curr_stock_val = 0.0
        total_curr_stock_units = 0.0
        for row in overview_data:
            prod = row.get("product")
            if prod:
                p_id = prod.id if hasattr(prod, "id") else (prod.get("id") if isinstance(prod, dict) else str(prod))
            else:
                p_id = row.get("product_id")
            cost = product_cost_map.get(p_id, 0.0)
            on_hand = float(row.get("total_on_hand", 0.0))
            total_curr_stock_val += on_hand * cost
            total_curr_stock_units += on_hand

        # 5. Shrinkage Loss in windows
        movements, _ = self.stock_repo.list_movements(page=1, page_size=5000)

        def aggregate_shrinkage(start_dt: datetime, end_dt: datetime) -> float:
            loss_val = 0.0
            for m in movements:
                raw_type = (
                    getattr(m, "type", None)
                    or getattr(m, "movement_type", None)
                    if hasattr(m, "type") or hasattr(m, "movement_type")
                    else (m.get("type") if isinstance(m, dict) else m.get("movement_type"))
                )
                m_type = (
                    str(raw_type.value).lower()
                    if hasattr(raw_type, "value")
                    else (str(raw_type).lower() if raw_type is not None else "")
                )

                qty = float(
                    getattr(m, "quantity", 0.0)
                    if hasattr(m, "quantity")
                    else (m.get("quantity", 0.0) if isinstance(m, dict) else 0.0)
                )
                created = (
                    getattr(m, "created_at", None)
                    if hasattr(m, "created_at")
                    else (m.get("created_at") if isinstance(m, dict) else None)
                )
                if not created:
                    continue
                if isinstance(created, str):
                    try:
                        created = datetime.fromisoformat(created)
                    except ValueError:
                        continue
                if created.tzinfo is None:
                    created = created.replace(tzinfo=UTC)

                if start_dt <= created <= end_dt and m_type == "adjustment" and qty < 0:
                    p_id = (
                        getattr(m, "product_id", "")
                        if hasattr(m, "product_id")
                        else (m.get("product_id", "") if isinstance(m, dict) else "")
                    )
                    cost = product_cost_map.get(p_id, 0.0)
                    loss_val += abs(qty) * cost
            return loss_val

        curr_shrinkage = aggregate_shrinkage(current_start, current_end)
        prior_shrinkage = aggregate_shrinkage(prior_start, prior_end)

        # 6. Turnover Rate
        curr_avg_on_hand = total_curr_stock_units + (curr_sales["units_sold"] / 2.0)
        curr_turnover = round(curr_sales["units_sold"] / curr_avg_on_hand, 2) if curr_avg_on_hand > 0 else 0.0

        prior_avg_on_hand = total_curr_stock_units + (prior_sales["units_sold"] / 2.0)
        prior_turnover = round(prior_sales["units_sold"] / prior_avg_on_hand, 2) if prior_avg_on_hand > 0 else 0.0

        # Build period scorecard
        period_label = f"vs prior {window_days}d"
        metrics: dict[str, ComparisonMetricResult] = {
            "revenue": self.compute_metric_delta(
                "revenue", "Gross Revenue", curr_sales["revenue"], prior_sales["revenue"], yoy_sales["revenue"],
                higher_is_better=True, period_label=period_label, is_currency=True
            ),
            "gross_margin": self.compute_metric_delta(
                "gross_margin", "Gross Profit", curr_sales["margin_inr"], prior_sales["margin_inr"], yoy_sales["margin_inr"],
                higher_is_better=True, period_label=period_label, is_currency=True
            ),
            "gross_margin_pct": self.compute_metric_delta(
                "gross_margin_pct", "Gross Margin %", curr_sales["margin_pct"], prior_sales["margin_pct"], yoy_sales["margin_pct"],
                higher_is_better=True, period_label=period_label, is_pct=True
            ),
            "units_sold": self.compute_metric_delta(
                "units_sold", "Units Sold", curr_sales["units_sold"], prior_sales["units_sold"], yoy_sales["units_sold"],
                higher_is_better=True, period_label=period_label
            ),
            "turnover_ratio": self.compute_metric_delta(
                "turnover_ratio", "Inventory Turnover", curr_turnover, prior_turnover,
                higher_is_better=True, period_label=period_label
            ),
            "stock_valuation": self.compute_metric_delta(
                "stock_valuation", "Stock Valuation", total_curr_stock_val, total_curr_stock_val,
                higher_is_better=True, period_label=period_label, is_currency=True
            ),
            "shrinkage_value": self.compute_metric_delta(
                "shrinkage_value", "Shrinkage & Damage", curr_shrinkage, prior_shrinkage,
                higher_is_better=False, period_label=period_label, is_currency=True
            ),
        }

        return PeriodComparisonsResponse(
            period=period,
            current_range=f"{current_start.strftime('%d %b')} – {current_end.strftime('%d %b %Y')}",
            prior_range=f"{prior_start.strftime('%d %b')} – {prior_end.strftime('%d %b %Y')}",
            metrics=metrics,
            generated_at=now,
        )
