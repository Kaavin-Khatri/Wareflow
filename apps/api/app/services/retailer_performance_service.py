"""
Retailer Performance & Churn Risk Analytics Service (Step 16.2).

Ranks wholesale retailer accounts by purchasing revenue, tracks ordering frequency trends,
and flags churn risks when the elapsed gap exceeds 2x their historical average order interval.
Follows SOLID Principles:
- Single Responsibility: Calculates account performance, order intervals, and churn heuristic.
- Open/Closed: Extensible to customizable churn thresholds and predictive ML scoring.
- Dependency Inversion: Injected with repository interfaces.
"""

from datetime import UTC, datetime

from app.models.retailer import SOStatusEnum
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.schemas.analytics import (
    RetailerPerformanceItem,
    RetailerPerformanceResponse,
    RetailerPerformanceSummary,
)


class RetailerPerformanceService:
    """Service evaluating retailer account revenue, order velocity, and churn risk."""

    def __init__(
        self,
        retailer_repo: RetailerRepository,
        sales_order_repo: SalesOrderRepositoryInterface,
    ) -> None:
        self.retailer_repo = retailer_repo
        self.sales_order_repo = sales_order_repo

    def get_retailer_performance(
        self, as_of: datetime | None = None
    ) -> RetailerPerformanceResponse:
        """Calculate retailer scorecards, volume rankings, and churn risk flags."""
        now = as_of or datetime.now(UTC)

        retailers = self.retailer_repo.list_all(limit=1000)
        so_tuple = self.sales_order_repo.list_all(limit=2000)
        all_orders = so_tuple[0] if isinstance(so_tuple, tuple) else so_tuple

        # Group non-cancelled orders by retailer_id
        orders_by_retailer: dict[str, list] = {}
        for o in all_orders:
            status_val = o.status.value if hasattr(o.status, "value") else str(o.status).lower()
            if status_val in (SOStatusEnum.CANCELLED.value, "cancelled") or not o.retailer_id:
                continue
            orders_by_retailer.setdefault(o.retailer_id, []).append(o)

        items: list[RetailerPerformanceItem] = []
        total_revenue_all = 0.0
        active_retailers_count = 0
        churn_risk_count = 0
        total_orders_all = 0

        for ret in retailers:
            r_id = ret.id
            ret_orders = orders_by_retailer.get(r_id, [])

            # Sort orders chronologically
            ret_orders.sort(key=lambda x: x.order_date or x.created_at)

            order_count = len(ret_orders)
            total_rev = sum(float(o.total_amount) for o in ret_orders)
            avg_order_value = round(total_rev / order_count, 2) if order_count > 0 else 0.0

            last_order_dt = None
            last_order_date_str = None
            days_since_last = 0
            avg_gap = 0.0
            is_churn_risk = False
            churn_reason = None
            freq_trend = "steady"

            if order_count > 0:
                total_orders_all += order_count
                total_revenue_all += total_rev
                last_order = ret_orders[-1]
                last_order_dt = last_order.order_date or last_order.created_at
                if last_order_dt.tzinfo is None:
                    last_order_dt = last_order_dt.replace(tzinfo=UTC)

                last_order_date_str = last_order_dt.strftime("%Y-%m-%d")
                days_since_last = max((now - last_order_dt).days, 0)

                if days_since_last <= 90:
                    active_retailers_count += 1

                # Calculate average order gap
                if order_count >= 2:
                    first_dt = ret_orders[0].order_date or ret_orders[0].created_at
                    if first_dt.tzinfo is None:
                        first_dt = first_dt.replace(tzinfo=UTC)
                    span_days = max((last_order_dt - first_dt).days, 1)
                    avg_gap = round(span_days / (order_count - 1), 1)

                    # Frequency Trend
                    # Compare intervals in second half of history vs first half
                    mid = order_count // 2
                    first_half_span = max((ret_orders[mid].order_date - first_dt).days, 1)
                    second_half_span = max((last_order_dt - ret_orders[mid].order_date).days, 1)
                    first_half_avg = first_half_span / mid
                    second_half_avg = second_half_span / max(order_count - 1 - mid, 1)

                    if second_half_avg < first_half_avg * 0.75:
                        freq_trend = "increasing"
                    elif second_half_avg > first_half_avg * 1.35:
                        freq_trend = "decreasing"
                    else:
                        freq_trend = "steady"
                else:
                    avg_gap = 30.0  # Default assumed standard reorder cycle

                # Churn Risk Heuristic: days since last order > 2x historical average gap (min 14 days)
                threshold_days = max(2.0 * avg_gap, 14.0)
                if days_since_last > threshold_days:
                    is_churn_risk = True
                    churn_risk_count += 1
                    churn_reason = (
                        f"No order in {days_since_last} days (exceeds 2x historical average of {avg_gap:.1f}d)"
                    )
            else:
                # Registered retailer with 0 lifetime orders
                ret_created = getattr(ret, "created_at", None) or now
                if ret_created.tzinfo is None:
                    ret_created = ret_created.replace(tzinfo=UTC)
                days_registered = max((now - ret_created).days, 0)
                if days_registered >= 30:
                    is_churn_risk = True
                    churn_risk_count += 1
                    churn_reason = f"No orders placed since registration {days_registered} days ago"

            ret_name = ret.name or getattr(ret, "store_name", f"Retailer {r_id[:8]}")
            pricing_tier = (ret.pricing_tier or "standard").upper()

            items.append(
                RetailerPerformanceItem(
                    retailer_id=r_id,
                    retailer_name=ret_name,
                    contact_person=ret.contact_person,
                    phone=ret.phone,
                    pricing_tier=pricing_tier,
                    total_orders=order_count,
                    total_revenue=round(total_rev, 2),
                    avg_order_value=avg_order_value,
                    last_order_date=last_order_date_str,
                    days_since_last_order=days_since_last,
                    avg_order_gap_days=avg_gap,
                    frequency_trend=freq_trend,
                    is_churn_risk=is_churn_risk,
                    churn_risk_reason=churn_reason,
                )
            )

        # Sort descending by total revenue, secondary by total orders
        items.sort(key=lambda x: (-x.total_revenue, -x.total_orders, x.retailer_name.lower()))

        overall_aov = (
            round(total_revenue_all / total_orders_all, 2) if total_orders_all > 0 else 0.0
        )

        summary = RetailerPerformanceSummary(
            total_retailers=len(retailers),
            active_retailers_count=active_retailers_count,
            churn_risk_count=churn_risk_count,
            total_portfolio_revenue_inr=round(total_revenue_all, 2),
            average_order_value_inr=overall_aov,
        )

        return RetailerPerformanceResponse(
            summary=summary,
            items=items,
            generated_at=now,
        )
