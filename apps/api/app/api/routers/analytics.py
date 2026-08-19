"""General analytics and demand forecasting API router."""

from fastapi import APIRouter, Depends, Query

from app.core.di import get_forecasting_service
from app.core.security import CurrentUser, require_permission
from app.schemas.forecast import ForecastSummaryResponse
from app.services.forecasting_service import ForecastingService

router = APIRouter(prefix="/analytics", tags=["Analytics & AI"])


@router.get(
    "/forecast-summary",
    response_model=ForecastSummaryResponse,
    summary="Get catalog-wide demand forecast summary including top and slow movers",
)
def get_forecast_summary(
    horizon_days: int = Query(30, ge=1, le=365, description="Prediction horizon in days"),
    limit: int = Query(10, ge=1, le=50, description="Max products in top/slow movers lists"),
    service: ForecastingService = Depends(get_forecasting_service),
    _user: CurrentUser = Depends(require_permission("inventory:view")),
) -> ForecastSummaryResponse:
    """Aggregate demand forecast analytics and ranking across active catalog products."""
    return service.get_forecast_summary(horizon_days=horizon_days, limit=limit)
