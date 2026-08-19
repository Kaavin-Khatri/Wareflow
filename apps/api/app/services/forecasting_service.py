"""Forecasting domain service coordinating pluggable strategies and 24h caching (OCP)."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.models.forecast import Forecast
from app.repositories.interfaces.forecast_repository import ForecastRepositoryInterface
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.schemas.forecast import (
    ForecastSummaryItem,
    ForecastSummaryResponse,
    ProductForecastResponse,
)
from app.services.forecasting.base import ForecastResult, ForecastStrategy

logger = logging.getLogger(__name__)


class ForecastingService:
    """
    Central Demand Forecasting orchestration service.

    Strategy Pattern (OCP): Algorithmic strategies (Moving Average, Exponential Smoothing)
    are injected and swappable dynamically via configuration without altering callers.
    Maintains 24-hour cached snapshots to guarantee ultra-fast response times.
    """

    def __init__(
        self,
        forecast_repo: ForecastRepositoryInterface,
        stock_repo: StockRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        strategies: list[ForecastStrategy] | dict[str, ForecastStrategy],
        default_strategy: str = "moving_average",
        cache_ttl_hours: int = 24,
    ) -> None:
        self._forecast_repo = forecast_repo
        self._stock_repo = stock_repo
        self._product_repo = product_repo
        self._cache_ttl_hours = cache_ttl_hours
        self._default_strategy_name = default_strategy
        self._strategies: dict[str, ForecastStrategy] = {}

        if isinstance(strategies, dict):
            self._strategies = dict(strategies)
        else:
            for s in strategies:
                self._strategies[s.strategy_name] = s

    def get_product_forecast(
        self,
        product_id: str,
        horizon_days: int = 30,
        strategy_name: str | None = None,
        force_refresh: bool = False,
    ) -> ProductForecastResponse:
        """Calculate or retrieve cached demand forecast for a single product."""
        product = self._product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' was not found",
            )

        strategy = self._resolve_strategy(strategy_name)
        p_name = getattr(product, "name", None) or (
            product.get("name") if isinstance(product, dict) else ""
        )
        p_sku = getattr(product, "sku", None) or (
            product.get("sku") if isinstance(product, dict) else ""
        )

        if not force_refresh:
            cached = self._forecast_repo.get_valid_cached_forecast(
                product_id=product_id,
                strategy=strategy.strategy_name,
                horizon_days=horizon_days,
            )
            if cached:
                return self._build_response_from_model(cached, p_name, p_sku, is_cached=True)

        return self._compute_and_cache_forecast(product_id, p_name, p_sku, strategy, horizon_days)

    def get_forecast_summary(
        self,
        horizon_days: int = 30,
        limit: int = 10,
    ) -> ForecastSummaryResponse:
        """Aggregate catalog-wide forecast statistics into top and slow movers."""
        products = self._forecast_repo.get_all_active_products()
        items: list[ForecastSummaryItem] = []
        total_demand = 0.0

        for p in products:
            res = self.get_product_forecast(product_id=p["id"], horizon_days=horizon_days)
            item = ForecastSummaryItem(
                product_id=p["id"],
                product_name=p["name"],
                sku=p["sku"],
                category=p["category"],
                predicted_daily_demand=res.predicted_daily_demand,
                total_predicted_demand=res.total_predicted_demand,
                confidence_score=res.confidence_score,
                trend_direction=res.trend_direction,
                status=res.status,
            )
            items.append(item)
            total_demand += res.total_predicted_demand

        # Sort top movers (descending) and slow movers (ascending)
        sorted_by_demand = sorted(items, key=lambda x: x.total_predicted_demand, reverse=True)
        top_movers = sorted_by_demand[:limit]
        slow_movers = sorted(items, key=lambda x: x.total_predicted_demand)[:limit]

        return ForecastSummaryResponse(
            horizon_days=horizon_days,
            strategy=self._default_strategy_name,
            total_products_analyzed=len(products),
            total_projected_demand=round(total_demand, 2),
            top_movers=top_movers,
            slow_movers=slow_movers,
            generated_at=datetime.now(UTC),
        )

    def _resolve_strategy(self, strategy_name: str | None) -> ForecastStrategy:
        """Resolve requested strategy or fall back to configured default."""
        target = strategy_name or self._default_strategy_name
        strategy = self._strategies.get(target)
        if not strategy:
            # Fallback to first registered strategy
            if self._strategies:
                return next(iter(self._strategies.values()))
            raise RuntimeError("No Demand Forecasting strategy registered in system")
        return strategy

    def _compute_and_cache_forecast(
        self,
        product_id: str,
        product_name: str,
        sku: str,
        strategy: ForecastStrategy,
        horizon_days: int,
    ) -> ProductForecastResponse:
        """Run statistical calculation and persist to 24h cache table."""
        movements = self._forecast_repo.get_outbound_movements_by_product(
            product_id, trailing_days=90
        )
        on_hand = self._stock_repo.get_on_hand(product_id)

        calc: ForecastResult = strategy.forecast(
            product_id=product_id,
            movements=movements,
            horizon_days=horizon_days,
            current_stock=on_hand,
        )

        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=self._cache_ttl_hours)

        model = Forecast(
            id=str(uuid.uuid4()),
            product_id=product_id,
            strategy=strategy.strategy_name,
            horizon_days=horizon_days,
            predicted_daily_demand=calc.predicted_daily_demand,
            total_predicted_demand=calc.total_predicted_demand,
            confidence_score=calc.confidence_score,
            trend_direction=calc.trend_direction,
            history_data_points=calc.history_data_points,
            status=calc.status,
            computed_at=now,
            expires_at=expires_at,
        )

        saved = self._forecast_repo.save_forecast(model)
        return self._build_response_from_model(
            saved, product_name, sku, is_cached=False, message=calc.message
        )

    def _build_response_from_model(
        self,
        m: Forecast,
        product_name: str,
        sku: str,
        is_cached: bool,
        message: str | None = None,
    ) -> ProductForecastResponse:
        """Map database model to public schema."""
        return ProductForecastResponse(
            product_id=m.product_id,
            product_name=product_name,
            product_sku=sku,
            strategy=m.strategy,
            horizon_days=m.horizon_days,
            predicted_daily_demand=float(m.predicted_daily_demand),
            total_predicted_demand=float(m.total_predicted_demand),
            confidence_score=float(m.confidence_score),
            trend_direction=m.trend_direction,
            history_data_points=m.history_data_points,
            status=m.status,
            message=message,
            is_cached=is_cached,
            computed_at=m.computed_at,
            expires_at=m.expires_at,
        )
