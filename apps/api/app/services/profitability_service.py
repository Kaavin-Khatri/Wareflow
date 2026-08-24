"""
Profitability Analytics Service (Step 16.1).

Computes gross margins (selling_price - cost_price) weighted by units sold in the period,
accounting for retailer tier adjustments, rolled up per Product, Category, or Retailer.
Follows SOLID Principles:
- Single Responsibility: Calculates profitability margins and grouping aggregates.
- Open/Closed: Extensible to other grouping dimensions (e.g. Sales Rep, Region).
- Dependency Inversion: Depends on repository interfaces.
"""

from datetime import datetime, timedelta, timezone

from app.models.retailer import BuyerTypeEnum, SOStatusEnum
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.schemas.analytics import (
    ProfitabilityItem,
    ProfitabilityResponse,
    ProfitabilitySummary,
)


class ProfitabilityService:
    """Service calculating wholesale profitability and gross margin rollups."""

    def __init__(
        self,
        sales_order_repo: SalesOrderRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        retailer_repo: RetailerRepository,
    ) -> None:
        self.sales_order_repo = sales_order_repo
        self.product_repo = product_repo
        self.retailer_repo = retailer_repo

    def get_profitability(
        self, group_by: str = "product", period: str = "30d", as_of: datetime | None = None
    ) -> ProfitabilityResponse:
        """
        Calculate gross margin and revenue rollups.

        Args:
            group_by: Dimension to roll up by ('product', 'category', 'retailer').
            period: Time window ('7d', '30d', '90d', '12m', 'all').
            as_of: Reference timestamp (defaults to current UTC).
        """
        now = as_of or datetime.now(timezone.utc)
        cutoff_date = self._get_cutoff_date(now, period)

        # 1. Fetch products map to look up cost prices and categories
        products = self.product_repo.list_products(limit=1000)
        product_map = {p.id: p for p in products}

        # 2. Fetch retailers map
        retailers = self.retailer_repo.list_all(limit=1000)
        retailer_map = {r.id: r for r in retailers}

        # 3. Fetch sales orders
        so_tuple = self.sales_order_repo.list_all(limit=2000)
        orders = so_tuple[0] if isinstance(so_tuple, tuple) else so_tuple

        # Filter valid non-cancelled orders within time period
        valid_orders = []
        for o in orders:
            # Exclude cancelled orders
            status_val = o.status.value if hasattr(o.status, "value") else str(o.status).lower()
            if status_val == SOStatusEnum.CANCELLED.value or status_val == "cancelled":
                continue

            order_dt = o.order_date or o.created_at
            if order_dt:
                if order_dt.tzinfo is None:
                    order_dt = order_dt.replace(tzinfo=timezone.utc)
                if cutoff_date and order_dt < cutoff_date:
                    continue

            valid_orders.append(o)

        # 4. Aggregate by selected dimension
        normalized_group_by = group_by.lower().strip()
        if normalized_group_by == "category":
            items, summary = self._aggregate_by_category(valid_orders, product_map)
        elif normalized_group_by == "retailer":
            items, summary = self._aggregate_by_retailer(valid_orders, product_map, retailer_map)
        else:
            normalized_group_by = "product"
            items, summary = self._aggregate_by_product(valid_orders, product_map)

        return ProfitabilityResponse(
            group_by=normalized_group_by,
            period=period,
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
        self, orders: list, product_map: dict
    ) -> tuple[list[ProfitabilityItem], ProfitabilitySummary]:
        groups: dict[str, dict] = {}
        total_rev = 0.0
        total_cost = 0.0
        total_units = 0.0
        order_ids_set = set()

        for order in orders:
            order_ids_set.add(order.id)
            for item in getattr(order, "items", []) or []:
                p_id = item.product_id
                prod = product_map.get(p_id) or getattr(item, "product", None)

                p_name = prod.name if prod else f"Product {p_id[:8]}"
                p_sku = prod.sku if prod else "SKU-N/A"
                cat_name = (
                    prod.category.name
                    if prod and hasattr(prod, "category") and prod.category
                    else "Uncategorized"
                )
                cost_price = float(prod.cost_price) if prod and prod.cost_price else 0.0

                qty = float(item.qty)
                selling_price = float(item.unit_price)
                rev = qty * selling_price
                cost = qty * cost_price

                total_rev += rev
                total_cost += cost
                total_units += qty

                if p_id not in groups:
                    groups[p_id] = {
                        "id": p_id,
                        "name": p_name,
                        "secondary_info": f"SKU: {p_sku}",
                        "badge": cat_name,
                        "units_sold": 0.0,
                        "orders_set": set(),
                        "total_revenue": 0.0,
                        "total_cost": 0.0,
                    }

                g = groups[p_id]
                g["units_sold"] += qty
                g["orders_set"].add(order.id)
                g["total_revenue"] += rev
                g["total_cost"] += cost

        # Include products with 0 sales if they exist in catalog
        for p_id, prod in product_map.items():
            if p_id not in groups:
                cat_name = (
                    prod.category.name
                    if hasattr(prod, "category") and prod.category
                    else "Uncategorized"
                )
                groups[p_id] = {
                    "id": p_id,
                    "name": prod.name,
                    "secondary_info": f"SKU: {prod.sku}",
                    "badge": cat_name,
                    "units_sold": 0.0,
                    "orders_set": set(),
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                }

        items = []
        for g in groups.values():
            rev = g["total_revenue"]
            cost = g["total_cost"]
            margin_inr = rev - cost
            margin_pct = (margin_inr / rev * 100.0) if rev > 0 else 0.0

            items.append(
                ProfitabilityItem(
                    id=g["id"],
                    name=g["name"],
                    secondary_info=g["secondary_info"],
                    badge=g["badge"],
                    units_sold=round(g["units_sold"], 2),
                    orders_count=len(g["orders_set"]),
                    total_revenue=round(rev, 2),
                    total_cost=round(cost, 2),
                    gross_margin_inr=round(margin_inr, 2),
                    gross_margin_pct=round(margin_pct, 1),
                )
            )

        # Sort descending by gross margin INR, secondary by revenue
        items.sort(key=lambda x: (-x.gross_margin_inr, -x.total_revenue, x.name.lower()))

        total_margin_inr = total_rev - total_cost
        overall_pct = (total_margin_inr / total_rev * 100.0) if total_rev > 0 else 0.0

        summary = ProfitabilitySummary(
            total_revenue=round(total_rev, 2),
            total_cost=round(total_cost, 2),
            total_gross_margin_inr=round(total_margin_inr, 2),
            overall_margin_pct=round(overall_pct, 1),
            total_units_sold=round(total_units, 2),
            total_orders=len(order_ids_set),
        )

        return items, summary

    def _aggregate_by_category(
        self, orders: list, product_map: dict
    ) -> tuple[list[ProfitabilityItem], ProfitabilitySummary]:
        groups: dict[str, dict] = {}
        total_rev = 0.0
        total_cost = 0.0
        total_units = 0.0
        order_ids_set = set()

        for order in orders:
            order_ids_set.add(order.id)
            for item in getattr(order, "items", []) or []:
                p_id = item.product_id
                prod = product_map.get(p_id) or getattr(item, "product", None)

                cat_id = (
                    str(prod.category_id)
                    if prod and getattr(prod, "category_id", None)
                    else "uncategorized"
                )
                cat_name = (
                    prod.category.name
                    if prod and hasattr(prod, "category") and prod.category
                    else "Uncategorized"
                )
                cost_price = float(prod.cost_price) if prod and prod.cost_price else 0.0

                qty = float(item.qty)
                selling_price = float(item.unit_price)
                rev = qty * selling_price
                cost = qty * cost_price

                total_rev += rev
                total_cost += cost
                total_units += qty

                if cat_id not in groups:
                    groups[cat_id] = {
                        "id": cat_id,
                        "name": cat_name,
                        "products_set": set(),
                        "units_sold": 0.0,
                        "orders_set": set(),
                        "total_revenue": 0.0,
                        "total_cost": 0.0,
                    }

                g = groups[cat_id]
                g["products_set"].add(p_id)
                g["units_sold"] += qty
                g["orders_set"].add(order.id)
                g["total_revenue"] += rev
                g["total_cost"] += cost

        items = []
        for g in groups.values():
            rev = g["total_revenue"]
            cost = g["total_cost"]
            margin_inr = rev - cost
            margin_pct = (margin_inr / rev * 100.0) if rev > 0 else 0.0
            prod_count = len(g["products_set"])

            items.append(
                ProfitabilityItem(
                    id=g["id"],
                    name=g["name"],
                    secondary_info=f"{prod_count} Products",
                    badge="CATEGORY",
                    units_sold=round(g["units_sold"], 2),
                    orders_count=len(g["orders_set"]),
                    total_revenue=round(rev, 2),
                    total_cost=round(cost, 2),
                    gross_margin_inr=round(margin_inr, 2),
                    gross_margin_pct=round(margin_pct, 1),
                )
            )

        items.sort(key=lambda x: (-x.gross_margin_inr, -x.total_revenue, x.name.lower()))

        total_margin_inr = total_rev - total_cost
        overall_pct = (total_margin_inr / total_rev * 100.0) if total_rev > 0 else 0.0

        summary = ProfitabilitySummary(
            total_revenue=round(total_rev, 2),
            total_cost=round(total_cost, 2),
            total_gross_margin_inr=round(total_margin_inr, 2),
            overall_margin_pct=round(overall_pct, 1),
            total_units_sold=round(total_units, 2),
            total_orders=len(order_ids_set),
        )

        return items, summary

    def _aggregate_by_retailer(
        self, orders: list, product_map: dict, retailer_map: dict
    ) -> tuple[list[ProfitabilityItem], ProfitabilitySummary]:
        groups: dict[str, dict] = {}
        total_rev = 0.0
        total_cost = 0.0
        total_units = 0.0
        order_ids_set = set()

        for order in orders:
            order_ids_set.add(order.id)

            if order.retailer_id:
                ret_id = order.retailer_id
                ret = retailer_map.get(ret_id) or getattr(order, "retailer", None)
                ret_name = (
                    getattr(ret, "name", None)
                    or getattr(ret, "store_name", "")
                    or f"Retailer {ret_id[:8]}"
                )
                pricing_tier = (
                    getattr(ret, "pricing_tier", "standard") if ret else "standard"
                ).upper()
            elif order.customer_id or order.buyer_type == BuyerTypeEnum.CUSTOMER:
                cust = getattr(order, "customer", None)
                ret_id = order.customer_id or "direct-walkin"
                ret_name = getattr(cust, "name", "Direct Customer")
                pricing_tier = "WALK-IN"
            else:
                ret_id = "direct"
                ret_name = "Direct Wholesale Order"
                pricing_tier = "STANDARD"

            if ret_id not in groups:
                groups[ret_id] = {
                    "id": ret_id,
                    "name": ret_name,
                    "secondary_info": f"Tier: {pricing_tier}",
                    "badge": pricing_tier,
                    "units_sold": 0.0,
                    "orders_set": set(),
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                }

            g = groups[ret_id]
            g["orders_set"].add(order.id)

            for item in getattr(order, "items", []) or []:
                p_id = item.product_id
                prod = product_map.get(p_id) or getattr(item, "product", None)
                cost_price = float(prod.cost_price) if prod and prod.cost_price else 0.0

                qty = float(item.qty)
                selling_price = float(item.unit_price)
                rev = qty * selling_price
                cost = qty * cost_price

                total_rev += rev
                total_cost += cost
                total_units += qty

                g["units_sold"] += qty
                g["total_revenue"] += rev
                g["total_cost"] += cost

        items = []
        for g in groups.values():
            rev = g["total_revenue"]
            cost = g["total_cost"]
            margin_inr = rev - cost
            margin_pct = (margin_inr / rev * 100.0) if rev > 0 else 0.0

            items.append(
                ProfitabilityItem(
                    id=g["id"],
                    name=g["name"],
                    secondary_info=g["secondary_info"],
                    badge=g["badge"],
                    units_sold=round(g["units_sold"], 2),
                    orders_count=len(g["orders_set"]),
                    total_revenue=round(rev, 2),
                    total_cost=round(cost, 2),
                    gross_margin_inr=round(margin_inr, 2),
                    gross_margin_pct=round(margin_pct, 1),
                )
            )

        items.sort(key=lambda x: (-x.gross_margin_inr, -x.total_revenue, x.name.lower()))

        total_margin_inr = total_rev - total_cost
        overall_pct = (total_margin_inr / total_rev * 100.0) if total_rev > 0 else 0.0

        summary = ProfitabilitySummary(
            total_revenue=round(total_rev, 2),
            total_cost=round(total_cost, 2),
            total_gross_margin_inr=round(total_margin_inr, 2),
            overall_margin_pct=round(overall_pct, 1),
            total_units_sold=round(total_units, 2),
            total_orders=len(order_ids_set),
        )

        return items, summary
