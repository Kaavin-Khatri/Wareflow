"""Stock analytics and inventory composition API router (Step 6.1)."""

from fastapi import APIRouter, Depends, Query

from app.core.di import get_stock_analytics_service
from app.core.security import CurrentUser, require_permission
from app.schemas.stock_analytics import (
    ExpiryTimelineResponse,
    StockHealthDistributionResponse,
    StockValueSummaryResponse,
    TopProductsResponse,
)
from app.services.stock_analytics_service import StockAnalyticsService

router = APIRouter(prefix="/analytics/stock", tags=["Stock Analytics"])


@router.get(
    "/value-summary",
    response_model=StockValueSummaryResponse,
    summary="Get total current stock value and breakdown by category and warehouse",
)
def get_stock_value_summary(
    service: StockAnalyticsService = Depends(get_stock_analytics_service),
    _user: CurrentUser = Depends(require_permission("inventory:view")),
) -> StockValueSummaryResponse:
    """Calculate aggregate inventory valuation across all storage nodes."""
    return service.get_value_summary()


@router.get(
    "/health-distribution",
    response_model=StockHealthDistributionResponse,
    summary="Get product distribution across stock health bands",
)
def get_stock_health_distribution(
    service: StockAnalyticsService = Depends(get_stock_analytics_service),
    _user: CurrentUser = Depends(require_permission("inventory:view")),
) -> StockHealthDistributionResponse:
    """Classify products into healthy, low, critical, and out-of-stock bands."""
    return service.get_health_distribution()


@router.get(
    "/top-value-products",
    response_model=TopProductsResponse,
    summary="Get top products by capital allocation and volume",
)
def get_top_value_products(
    limit: int = Query(default=10, ge=1, le=50, description="Max products to return"),
    service: StockAnalyticsService = Depends(get_stock_analytics_service),
    _user: CurrentUser = Depends(require_permission("inventory:view")),
) -> TopProductsResponse:
    """Retrieve top ranking products by monetary value and unit stock."""
    return service.get_top_products(limit=limit)


@router.get(
    "/expiry-timeline",
    response_model=ExpiryTimelineResponse,
    summary="Get forward-looking batch expiration horizon timeline",
)
def get_expiry_timeline(
    service: StockAnalyticsService = Depends(get_stock_analytics_service),
    _user: CurrentUser = Depends(require_permission("inventory:view")),
) -> ExpiryTimelineResponse:
    """Group active stock batches into temporal expiration windows."""
    return service.get_expiry_timeline()
