"""Pydantic schemas for Demand Forecasting API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductForecastResponse(BaseModel):
    """Demand forecast response for a single product."""

    model_config = ConfigDict(from_attributes=True)

    product_id: str = Field(..., description="Unique product ID")
    product_name: str | None = Field(None, description="Product display name")
    product_sku: str | None = Field(None, description="Product SKU code")
    strategy: str = Field(..., description="Applied forecasting strategy name")
    horizon_days: int = Field(30, description="Forecast time horizon in days")
    predicted_daily_demand: float = Field(..., description="Estimated daily demand rate")
    total_predicted_demand: float = Field(..., description="Total forecasted units for horizon")
    confidence_score: float = Field(..., description="Statistical confidence (0.0 to 1.0)")
    trend_direction: str = Field(
        ..., description="Trend: 'increasing', 'stable', 'decreasing', or 'insufficient_data'"
    )
    history_data_points: int = Field(..., description="Number of historical movements evaluated")
    status: str = Field(..., description="'calculated' or 'insufficient_data'")
    message: str | None = Field(None, description="Optional diagnostic or warning message")
    is_cached: bool = Field(False, description="Whether result was served from 24h cache")
    computed_at: datetime = Field(..., description="Timestamp forecast was calculated")
    expires_at: datetime = Field(..., description="Cache expiration timestamp")


class ForecastSummaryItem(BaseModel):
    """Single item summary within aggregated forecast rankings."""

    product_id: str
    product_name: str
    sku: str
    category: str
    predicted_daily_demand: float
    total_predicted_demand: float
    confidence_score: float
    trend_direction: str
    status: str


class ForecastSummaryResponse(BaseModel):
    """Aggregate demand forecast analytics and mover rankings."""

    horizon_days: int = Field(..., description="Forecast horizon in days")
    strategy: str = Field(..., description="Configured forecasting strategy")
    total_products_analyzed: int = Field(..., description="Number of active catalog products")
    total_projected_demand: float = Field(..., description="Sum of projected units across catalog")
    top_movers: list[ForecastSummaryItem] = Field(..., description="Highest projected volume items")
    slow_movers: list[ForecastSummaryItem] = Field(
        ..., description="Lowest / stagnant demand items"
    )
    generated_at: datetime = Field(..., description="Timestamp summary was compiled")
