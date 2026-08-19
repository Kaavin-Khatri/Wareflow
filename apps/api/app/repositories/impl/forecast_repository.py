"""Demand forecast repository implementations (SQLAlchemy & InMemory)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import Category, Product
from app.models.forecast import Forecast
from app.models.inventory import StockMovement, StockMovementTypeEnum


class SqlAlchemyForecastRepository:
    """SQLAlchemy-backed repository for caching forecasts and reading stock history."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_valid_cached_forecast(
        self, product_id: str, strategy: str, horizon_days: int
    ) -> Forecast | None:
        """Fetch non-expired cached forecast record."""
        now = datetime.now(UTC)
        stmt = (
            select(Forecast)
            .where(
                Forecast.product_id == product_id,
                Forecast.strategy == strategy,
                Forecast.horizon_days == horizon_days,
                Forecast.expires_at > now,
            )
            .order_by(Forecast.computed_at.desc())
        )
        return self._session.execute(stmt).scalars().first()

    def save_forecast(self, forecast: Forecast) -> Forecast:
        """Persist or update forecast snapshot in database."""
        existing = (
            self._session.execute(
                select(Forecast).where(
                    Forecast.product_id == forecast.product_id,
                    Forecast.strategy == forecast.strategy,
                    Forecast.horizon_days == forecast.horizon_days,
                )
            )
            .scalars()
            .first()
        )
        if existing:
            existing.predicted_daily_demand = forecast.predicted_daily_demand
            existing.total_predicted_demand = forecast.total_predicted_demand
            existing.confidence_score = forecast.confidence_score
            existing.trend_direction = forecast.trend_direction
            existing.history_data_points = forecast.history_data_points
            existing.status = forecast.status
            existing.computed_at = forecast.computed_at
            existing.expires_at = forecast.expires_at
            self._session.commit()
            self._session.refresh(existing)
            return existing

        self._session.add(forecast)
        self._session.commit()
        self._session.refresh(forecast)
        return forecast

    def get_outbound_movements_by_product(
        self, product_id: str, trailing_days: int = 90
    ) -> list[StockMovement]:
        """Fetch historical outbound stock movements within the trailing day window."""
        cutoff = datetime.now(UTC) - timedelta(days=trailing_days)
        stmt = (
            select(StockMovement)
            .where(
                StockMovement.product_id == product_id,
                StockMovement.type == StockMovementTypeEnum.OUT,
                StockMovement.created_at >= cutoff,
            )
            .order_by(StockMovement.created_at.asc())
        )
        return list(self._session.execute(stmt).scalars().all())

    def get_all_active_products(self) -> list[dict[str, Any]]:
        """Retrieve list of active products joined with category details."""
        stmt = (
            select(Product, Category.name.label("category_name"))
            .outerjoin(Category, Product.category_id == Category.id)
            .where(Product.is_active.is_(True))
            .order_by(Product.name.asc())
        )
        results = self._session.execute(stmt).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "category": cat_name or "Uncategorized",
                "min_stock_level": p.min_stock_level,
                "reorder_point": p.reorder_point,
            }
            for p, cat_name in results
        ]

    def list_recent_forecasts(self, horizon_days: int = 30) -> list[Forecast]:
        """List cached forecasts matching horizon."""
        stmt = (
            select(Forecast)
            .where(Forecast.horizon_days == horizon_days)
            .order_by(Forecast.total_predicted_demand.desc())
        )
        return list(self._session.execute(stmt).scalars().all())


class InMemoryForecastRepository:
    """In-memory mock repository for forecasting unit tests."""

    def __init__(
        self,
        initial_movements: list[Any] | None = None,
        initial_products: list[dict[str, Any]] | None = None,
    ) -> None:
        self._movements: list[Any] = list(initial_movements or [])
        self._products: list[dict[str, Any]] = list(initial_products or [])
        self._forecasts: dict[str, Forecast] = {}

    def get_valid_cached_forecast(
        self, product_id: str, strategy: str, horizon_days: int
    ) -> Forecast | None:
        key = f"{product_id}:{strategy}:{horizon_days}"
        forecast = self._forecasts.get(key)
        if not forecast:
            return None
        now = datetime.now(UTC)
        exp = forecast.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp > now:
            return forecast
        return None

    def save_forecast(self, forecast: Forecast) -> Forecast:
        key = f"{forecast.product_id}:{forecast.strategy}:{forecast.horizon_days}"
        self._forecasts[key] = forecast
        return forecast

    def get_outbound_movements_by_product(
        self, product_id: str, trailing_days: int = 90
    ) -> list[Any]:
        cutoff = datetime.now(UTC) - timedelta(days=trailing_days)
        results = []
        for m in self._movements:
            m_pid = getattr(m, "product_id", "")
            m_type = getattr(m, "type", "")
            if hasattr(m_type, "value"):
                m_type = m_type.value
            c_at = getattr(m, "created_at", None)
            if (
                m_pid == product_id
                and m_type in ("out", "sales_shipment", "sale")
                and (not c_at or c_at >= cutoff)
            ):
                results.append(m)
        return results

    def get_all_active_products(self) -> list[dict[str, Any]]:
        return list(self._products)

    def list_recent_forecasts(self, horizon_days: int = 30) -> list[Forecast]:
        return [f for f in self._forecasts.values() if f.horizon_days == horizon_days]
