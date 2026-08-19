"""Forecasting package exposing pluggable strategies and result dataclasses."""

from app.services.forecasting.base import ForecastResult, ForecastStrategy
from app.services.forecasting.exponential_smoothing import ExponentialSmoothingForecast
from app.services.forecasting.moving_average import MovingAverageForecast

__all__ = [
    "ForecastResult",
    "ForecastStrategy",
    "MovingAverageForecast",
    "ExponentialSmoothingForecast",
]
