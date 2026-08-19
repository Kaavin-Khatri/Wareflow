"""Exponential Smoothing demand forecasting strategy."""

import logging
from datetime import UTC, datetime
from typing import Any

from app.services.forecasting.base import ForecastResult, ForecastStrategy

logger = logging.getLogger(__name__)


class ExponentialSmoothingForecast(ForecastStrategy):
    """
    Single Exponential Smoothing demand forecasting strategy.

    Applies smoothing factor alpha to weigh recent consumption exponentially
    against recursive prior estimations.
    """

    def __init__(self, alpha: float = 0.35) -> None:
        self.alpha = max(0.01, min(0.99, alpha))

    @property
    def strategy_name(self) -> str:
        return "exponential_smoothing"

    def forecast(
        self,
        product_id: str,
        movements: list[Any],
        horizon_days: int = 30,
        current_stock: float = 0.0,
    ) -> ForecastResult:
        """Calculate smoothed demand using recursive exponential smoothing."""
        outbound = [m for m in movements if self._is_outbound(m)]
        if not outbound:
            return self._build_insufficient_result(product_id, horizon_days)

        weekly_buckets = self._aggregate_weekly_buckets(outbound, num_weeks=4)
        if sum(weekly_buckets) == 0.0:
            return self._build_insufficient_result(product_id, horizon_days)

        smoothed_level = self._apply_exponential_smoothing(weekly_buckets)
        daily_demand = round(smoothed_level / 7.0, 4)
        total_demand = round(daily_demand * horizon_days, 2)

        trend = self._determine_trend(weekly_buckets)
        confidence = self._calculate_confidence(weekly_buckets, len(outbound))

        return ForecastResult(
            product_id=product_id,
            strategy=self.strategy_name,
            horizon_days=horizon_days,
            predicted_daily_demand=daily_demand,
            total_predicted_demand=total_demand,
            confidence_score=confidence,
            trend_direction=trend,
            history_data_points=len(outbound),
            status="calculated",
            weekly_averages=weekly_buckets,
        )

    def _is_outbound(self, movement: Any) -> bool:
        """Check if stock movement represents outgoing demand."""
        m_type = getattr(movement, "type", "")
        if hasattr(m_type, "value"):
            m_type = m_type.value
        qty = float(getattr(movement, "quantity", 0.0) or 0.0)
        return m_type in ("out", "sales_shipment", "sale") and qty > 0

    def _aggregate_weekly_buckets(self, movements: list[Any], num_weeks: int = 4) -> list[float]:
        """Bucket movement quantities into chronological weekly slots (oldest -> newest)."""
        now = datetime.now(UTC)
        buckets = [0.0] * num_weeks
        for m in movements:
            created_at = getattr(m, "created_at", None)
            if not created_at:
                continue
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            age_days = (now - created_at).total_seconds() / 86400.0
            week_idx = int(age_days // 7)
            if 0 <= week_idx < num_weeks:
                target_slot = num_weeks - 1 - week_idx
                buckets[target_slot] += float(getattr(m, "quantity", 0.0) or 0.0)
        return [round(b, 2) for b in buckets]

    def _apply_exponential_smoothing(self, buckets: list[float]) -> float:
        """Compute final smoothed expectation across chronological points."""
        smoothed = buckets[0]
        for val in buckets[1:]:
            smoothed = self.alpha * val + (1.0 - self.alpha) * smoothed
        return smoothed

    def _determine_trend(self, buckets: list[float]) -> str:
        """Infer directional trajectory comparing recent to smoothed expectations."""
        if len(buckets) < 2:
            return "stable"
        recent = buckets[-1]
        older_avg = sum(buckets[:-1]) / len(buckets[:-1])
        if older_avg == 0.0:
            return "increasing" if recent > 0 else "stable"
        ratio = recent / older_avg
        if ratio > 1.15:
            return "increasing"
        if ratio < 0.85:
            return "decreasing"
        return "stable"

    def _calculate_confidence(self, buckets: list[float], point_count: int) -> float:
        """Compute statistical confidence score."""
        active_weeks = sum(1 for b in buckets if b > 0)
        base = active_weeks / float(len(buckets)) * 0.70
        volume_boost = min(point_count / 10.0, 1.0) * 0.20
        return round(min(base + volume_boost, 0.90), 3)

    def _build_insufficient_result(self, product_id: str, horizon_days: int) -> ForecastResult:
        """Return honest insufficient data forecast response."""
        return ForecastResult(
            product_id=product_id,
            strategy=self.strategy_name,
            horizon_days=horizon_days,
            predicted_daily_demand=0.0,
            total_predicted_demand=0.0,
            confidence_score=0.0,
            trend_direction="insufficient_data",
            history_data_points=0,
            status="insufficient_data",
            message="Insufficient movement history to project demand accurately",
        )
