"""
Inventory Turnover Analytics Service (Step 16.1).

Computes inventory turnover ratio (units_sold / average_on_hand) and days of stock on hand,
serving as a continuous early-warning velocity indicator between normal movement and dead stock.
Follows SOLID Principles:
- Single Responsibility: Calculates inventory velocity, turnover ratios, and risk banding.
- Open/Closed: Extensible to custom banding thresholds and category rollups.
- Dependency Inversion: Injected with repository interfaces.
"""

from datetime import UTC, datetime, timedelta

from app.models.retailer import SOStatusEnum
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.schemas.analytics import (
    TurnoverItem,
    TurnoverResponse,
    TurnoverSummary,
)


class TurnoverService:
    """Service computing inventory turnover velocity, days of stock, and risk banding."""

    def __init__(
        self,
        sales_order_repo: SalesOrderRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        stock_repo: StockRepositoryInterface,
    ) -> None:
        self.sales_order_repo = sales_order_repo
        self.product_repo = product_repo
        self.stock_repo = stock_repo

    def get_turnover(
        self, period: str = "30d", as_of: datetime | None = None
    ) -> TurnoverResponse:
        """
        Calculate catalog inventory turnover ratio and days of stock on hand.

        Args:
            period: Time window ('7d', '30d', '90d', '12m', 'all').
            as_of: Reference timestamp (defaults to current UTC).
        """
        now = as_of or datetime.now(UTC)
        days_in_period, cutoff_date = self._parse_period(now, period)

        # 1. Fetch active products
        products = self.product_repo.list_products(limit=1000)

        # 2. Fetch sales orders within period
        so_tuple = self.sales_order_repo.list_all(limit=2000)
        orders = so_tuple[0] if isinstance(so_tuple, tuple) else so_tuple

        # Sum units sold per product in period
        units_sold_map: dict[str, float] = {}
        for o in orders:
            status_val = o.status.value if hasattr(o.status, "value") else str(o.status).lower()
            if status_val == SOStatusEnum.CANCELLED.value or status_val == "cancelled":
                continue

            order_dt = o.order_date or o.created_at
            if order_dt:
                if order_dt.tzinfo is None:
                    order_dt = order_dt.replace(tzinfo=UTC)
                if cutoff_date and order_dt < cutoff_date:
                    continue

            for item in getattr(o, "items", []) or []:
                p_id = item.product_id
                units_sold_map[p_id] = units_sold_map.get(p_id, 0.0) + float(item.qty)

        # 3. Compute turnover metrics for each product
        items: list[TurnoverItem] = []
        healthy_count = 0
        slowing_count = 0
        at_risk_count = 0

        total_turnover_sum = 0.0
        total_days_sum = 0.0
        active_stock_items_count = 0

        for prod in products:
            p_id = prod.id
            cat_name = (
                prod.category.name
                if hasattr(prod, "category") and prod.category
                else "Uncategorized"
            )
            unit_name = getattr(prod, "unit", "Piece") or "Piece"
            cost_price = float(prod.cost_price) if prod.cost_price else 0.0

            # Current on-hand stock across all warehouses
            current_on_hand = float(self.stock_repo.get_on_hand(p_id))
            units_sold = units_sold_map.get(p_id, 0.0)

            # Average inventory on-hand in period
            # Midpoint approximation: current stock + (units sold / 2)
            if units_sold > 0 or current_on_hand > 0:
                avg_on_hand = current_on_hand + (units_sold / 2.0)
            else:
                avg_on_hand = 0.0

            # Turnover Ratio = Units Sold / Average Stock
            if avg_on_hand > 0:
                turnover_ratio = round(units_sold / avg_on_hand, 2)
            elif units_sold > 0:
                turnover_ratio = 10.0  # High velocity: fully depleted stock
            else:
                turnover_ratio = 0.0

            # Days of Stock on Hand = (Average Stock / Units Sold) * Days
            if units_sold > 0:
                days_of_stock = round((avg_on_hand / units_sold) * days_in_period, 1)
            elif current_on_hand > 0:
                days_of_stock = 999.0  # Stagnant sitting stock
            else:
                days_of_stock = 0.0

            # Determine Health Banding
            # Healthy: turnover >= 1.0 (or days of stock <= 30d with positive velocity)
            # Slowing: 0.3 <= turnover < 1.0 (or 30d < days <= 90d)
            # At-Risk: turnover < 0.3 or days > 90d or zero sales with stock
            if turnover_ratio >= 1.0 or (0 < days_of_stock <= 30.0 and units_sold > 0):
                band = "healthy"
                healthy_count += 1
            elif turnover_ratio >= 0.3 or (30.0 < days_of_stock <= 90.0 and units_sold > 0):
                band = "slowing"
                slowing_count += 1
            else:
                band = "at_risk"
                at_risk_count += 1

            tied_up_capital = round(current_on_hand * cost_price, 2)

            if current_on_hand > 0 or units_sold > 0:
                total_turnover_sum += turnover_ratio
                if days_of_stock < 999.0:
                    total_days_sum += days_of_stock
                active_stock_items_count += 1

            items.append(
                TurnoverItem(
                    product_id=p_id,
                    product_name=prod.name,
                    sku=prod.sku,
                    category_name=cat_name,
                    unit=unit_name,
                    current_on_hand=round(current_on_hand, 2),
                    units_sold=round(units_sold, 2),
                    average_on_hand=round(avg_on_hand, 2),
                    turnover_ratio=turnover_ratio,
                    days_of_stock=days_of_stock,
                    turnover_band=band,
                    cost_price=cost_price,
                    tied_up_capital=tied_up_capital,
                )
            )

        # Sort ranked slowest-to-fastest (lowest turnover ratio first, secondary highest tied-up capital)
        items.sort(key=lambda x: (x.turnover_ratio, -x.tied_up_capital, x.product_name.lower()))

        avg_ratio = (
            round(total_turnover_sum / active_stock_items_count, 2)
            if active_stock_items_count > 0
            else 0.0
        )
        avg_days = (
            round(total_days_sum / active_stock_items_count, 1)
            if active_stock_items_count > 0
            else 0.0
        )

        summary = TurnoverSummary(
            average_turnover_ratio=avg_ratio,
            average_days_of_stock=avg_days,
            healthy_count=healthy_count,
            slowing_count=slowing_count,
            at_risk_count=at_risk_count,
            total_products=len(products),
        )

        return TurnoverResponse(
            period=period,
            summary=summary,
            items=items,
            generated_at=now,
        )

    def _parse_period(self, now: datetime, period: str) -> tuple[int, datetime | None]:
        p = period.lower().strip()
        if p == "7d":
            return 7, now - timedelta(days=7)
        if p == "30d":
            return 30, now - timedelta(days=30)
        if p == "90d":
            return 90, now - timedelta(days=90)
        if p in ("12m", "365d", "1y"):
            return 365, now - timedelta(days=365)
        if p == "all":
            return 365, None
        return 30, now - timedelta(days=30)
