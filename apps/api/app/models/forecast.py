"""Demand forecast snapshot and caching model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Forecast(Base):
    """
    Cached demand forecast output for a product over a specific prediction horizon.

    Enables 24-hour cache invalidation and provides historical trend telemetry.
    """

    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecasts_product_strategy_horizon", "product_id", "strategy", "horizon_days"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    strategy: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    predicted_daily_demand: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False, default=0.0
    )
    total_predicted_demand: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.0)
    trend_direction: Mapped[str] = mapped_column(
        String(30), nullable=False, default="stable"
    )  # "increasing" | "stable" | "decreasing" | "insufficient_data"
    history_data_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="calculated"
    )  # "calculated" | "insufficient_data"
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821
