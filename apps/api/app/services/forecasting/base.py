"""Base interface and dataclasses for pluggable Demand Forecasting strategies (OCP)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ForecastResult:
    """Standardized output produced by any Demand Forecasting strategy."""

    product_id: str
    strategy: str
    horizon_days: int
    predicted_daily_demand: float
    total_predicted_demand: float
    confidence_score: float
    trend_direction: str  # "increasing" | "stable" | "decreasing" | "insufficient_data"
    history_data_points: int
    status: str  # "calculated" | "insufficient_data"
    message: str | None = None
    weekly_averages: list[float] = field(default_factory=list)
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ForecastStrategy(ABC):
    """Abstract Strategy interface for statistical demand forecasting algorithms."""

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Unique identifier of the strategy (e.g., 'moving_average', 'exponential_smoothing')."""
        ...

    @abstractmethod
    def forecast(
        self,
        product_id: str,
        movements: list[Any],
        horizon_days: int = 30,
        current_stock: float = 0.0,
    ) -> ForecastResult:
        """
        Calculate predicted demand over the prediction horizon based on stock movements.

        Args:
            product_id: Target product identifier.
            movements: Trailing outbound stock movements.
            horizon_days: Prediction window in days (default: 30).
            current_stock: Current on-hand quantity for context.

        Returns:
            ForecastResult: Standardized calculation breakdown and confidence metrics.
        """
        ...
