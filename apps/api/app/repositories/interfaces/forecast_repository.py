"""Demand forecast repository interface protocol."""

from typing import Any, Protocol

from app.models.forecast import Forecast
from app.models.inventory import StockMovement


class ForecastRepositoryInterface(Protocol):
    """Data access contract for cached forecast snapshots and historical movements."""

    def get_valid_cached_forecast(
        self, product_id: str, strategy: str, horizon_days: int
    ) -> Forecast | None:
        """Fetch non-expired cached forecast record for product and horizon."""
        ...

    def save_forecast(self, forecast: Forecast) -> Forecast:
        """Persist or update forecast record in database/cache."""
        ...

    def get_outbound_movements_by_product(
        self, product_id: str, trailing_days: int = 90
    ) -> list[StockMovement]:
        """Fetch historical outbound stock movements within the trailing day window."""
        ...

    def get_all_active_products(self) -> list[dict[str, Any]]:
        """Retrieve list of active product summaries (id, name, sku, category)."""
        ...

    def list_recent_forecasts(self, horizon_days: int = 30) -> list[Forecast]:
        """List latest cached forecast records across all active products."""
        ...
