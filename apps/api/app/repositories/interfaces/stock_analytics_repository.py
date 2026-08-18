"""Stock Analytics repository interface contract (Step 6.1)."""

from typing import Any, Protocol


class StockAnalyticsRepositoryInterface(Protocol):
    """Protocol contract for querying aggregated stock valuation and composition data."""

    def get_stock_valuation_data(self) -> list[dict[str, Any]]:
        """Fetch joined data of products, categories, warehouses, and batches with on-hand quantities and costs."""
        ...

    def get_health_distribution_data(self) -> list[dict[str, Any]]:
        """Fetch product records with reorder_point and total on-hand quantity sums."""
        ...

    def get_top_products_data(self) -> list[dict[str, Any]]:
        """Fetch active products with total on-hand, cost_price, base_uom, and category info."""
        ...

    def get_batch_expiry_data(self) -> list[dict[str, Any]]:
        """Fetch all stock batches with quantity > 0, expiry_date, and associated product cost_price."""
        ...

    # --- Step 6.2: Purchasing Spend Contracts ---

    def get_spend_trend_data(self, months: int = 12) -> list[dict[str, Any]]:
        """Fetch received purchase order line items aggregated over the last N months."""
        ...

    def get_spend_by_supplier_data(self, months: int = 12) -> list[dict[str, Any]]:
        """Fetch procurement spend grouped by supplier over the last N months."""
        ...

    def get_spend_by_category_data(self, months: int = 12) -> list[dict[str, Any]]:
        """Fetch procurement spend grouped by product category over the last N months."""
        ...

    def get_product_cost_history_data(
        self, product_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch historical purchase order unit costs and baseline costs per product."""
        ...
