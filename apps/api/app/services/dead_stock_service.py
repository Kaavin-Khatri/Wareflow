"""Dead-stock detection domain service (Step 14.2).

Identifies dormant catalog items with zero outbound movements in the trailing window
and ranks them by capital-at-risk (tied-up capital).
"""

import logging
from datetime import UTC, datetime

from app.repositories.interfaces.forecast_repository import ForecastRepositoryInterface
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.schemas.analytics import DeadStockItem, DeadStockResponse

logger = logging.getLogger(__name__)


class DeadStockService:
    """Domain service detecting inactive inventory holding tied-up working capital."""

    def __init__(
        self,
        product_repo: ProductRepositoryInterface,
        stock_repo: StockRepositoryInterface,
        forecast_repo: ForecastRepositoryInterface,
    ) -> None:
        self._product_repo = product_repo
        self._stock_repo = stock_repo
        self._forecast_repo = forecast_repo

    def get_dead_stock(
        self,
        window_days: int = 90,
        category_id: str | None = None,
    ) -> DeadStockResponse:
        """
        Detect dead-stock items sitting in warehouse with zero outbound sales in trailing window.

        Ranked descending by tied-up capital (on_hand * cost_price).
        """
        if hasattr(self._product_repo, "list_products"):
            active_products = self._product_repo.list_products(limit=1000, is_active=True)
        else:
            products = self._product_repo.list()
            active_products = [
                p
                for p in products
                if (p.get("is_active", True) if isinstance(p, dict) else getattr(p, "is_active", True))
            ]

        dead_items: list[DeadStockItem] = []
        now = datetime.now(UTC)

        for prod in active_products:
            p_id = prod.get("id") if isinstance(prod, dict) else getattr(prod, "id", None)
            p_name = prod.get("name") if isinstance(prod, dict) else getattr(prod, "name", "Product")
            sku = prod.get("sku") if isinstance(prod, dict) else getattr(prod, "sku", "SKU")
            prod_cat_id = (
                prod.get("category_id")
                if isinstance(prod, dict)
                else getattr(prod, "category_id", None)
            )
            cat_name = (
                prod.get("category_name")
                if isinstance(prod, dict)
                else getattr(prod, "category_name", None)
            )
            if not cat_name and hasattr(prod, "category") and prod.category:
                cat_name = getattr(prod.category, "name", None)

            # Filter by category if requested
            if category_id and prod_cat_id != category_id:
                continue

            raw_unit = prod.get("unit") if isinstance(prod, dict) else getattr(prod, "unit", None)
            unit = str(raw_unit) if raw_unit else "Piece"

            cost_price = float(
                prod.get("cost_price", 0.0)
                if isinstance(prod, dict)
                else getattr(prod, "cost_price", 0.0) or 0.0
            )
            wholesale_price = float(
                prod.get("wholesale_price", 0.0)
                if isinstance(prod, dict)
                else getattr(prod, "wholesale_price", 0.0) or 0.0
            )
            unit_cost = cost_price if cost_price > 0 else wholesale_price

            on_hand = float(self._stock_repo.get_on_hand(p_id))

            # Dead stock prerequisite 1: on_hand > 0
            if on_hand <= 0:
                continue

            # Dead stock prerequisite 2: zero outbound movements in trailing window
            window_movements = self._forecast_repo.get_outbound_movements_by_product(
                product_id=p_id, trailing_days=window_days
            )

            # If any movement exists in the window, it is NOT dead stock
            if len(window_movements) > 0:
                continue

            # Product is dead stock! Compute idle duration & capital
            tied_up_capital = round(on_hand * unit_cost, 2)

            # Check longer history for last known outbound activity
            all_movements = self._forecast_repo.get_outbound_movements_by_product(
                product_id=p_id, trailing_days=730
            )

            last_movement_at: datetime | None = None
            if all_movements:
                dates = [
                    m.get("created_at") if isinstance(m, dict) else getattr(m, "created_at", None)
                    for m in all_movements
                ]
                valid_dates = [d for d in dates if d is not None]
                if valid_dates:
                    last_movement_at = max(valid_dates)
                    if last_movement_at.tzinfo is None:
                        last_movement_at = last_movement_at.replace(tzinfo=UTC)

            if last_movement_at:
                idle_days = max(window_days, (now - last_movement_at).days)
            else:
                created_at = (
                    prod.get("created_at")
                    if isinstance(prod, dict)
                    else getattr(prod, "created_at", None)
                )
                if created_at:
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=UTC)
                    idle_days = max(window_days, (now - created_at).days)
                else:
                    idle_days = window_days

            # Action recommendations based on stagnation severity
            if idle_days >= 180:
                rec_action = "liquidate_or_return"
                action_label = "Liquidate lot or initiate vendor return"
            elif idle_days >= 90:
                rec_action = "discount_clearance"
                action_label = "Apply 25-35% clearance discount"
            else:
                rec_action = "bundle_promotion"
                action_label = "Bundle with top-moving items"

            dead_items.append(
                DeadStockItem(
                    product_id=p_id,
                    product_name=p_name,
                    sku=sku,
                    category_name=cat_name,
                    unit=unit,
                    on_hand=on_hand,
                    cost_price=unit_cost,
                    tied_up_capital=tied_up_capital,
                    last_movement_at=last_movement_at,
                    idle_days=idle_days,
                    recommended_action=rec_action,
                    action_label=action_label,
                )
            )

        # Rank dead stock descending by tied-up capital (highest capital at risk first)
        dead_items.sort(key=lambda x: x.tied_up_capital, reverse=True)

        total_capital = round(sum(i.tied_up_capital for i in dead_items), 2)

        return DeadStockResponse(
            items=dead_items,
            total_dead_items=len(dead_items),
            total_tied_up_capital=total_capital,
            window_days=window_days,
            generated_at=now,
        )
