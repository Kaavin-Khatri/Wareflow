"""General analytics, demand forecasting, reorder suggestions, and dead-stock detection router."""

from fastapi import APIRouter, Depends, Query, status

from app.core.di import (
    get_dead_stock_service,
    get_forecasting_service,
    get_reorder_suggestion_service,
)
from app.core.security import CurrentUser, require_permission
from app.schemas.analytics import (
    CreatePOFromSuggestionsRequest,
    DeadStockResponse,
    ReorderSuggestionsResponse,
)
from app.schemas.forecast import ForecastSummaryResponse
from app.schemas.purchase_orders import PurchaseOrderResponse
from app.services.dead_stock_service import DeadStockService
from app.services.forecasting_service import ForecastingService
from app.services.reorder_suggestion_service import ReorderSuggestionService

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


@router.get(
    "/reorder-suggestions",
    response_model=ReorderSuggestionsResponse,
    summary="Get automated reorder suggestions for low and depleted inventory items",
)
def get_reorder_suggestions(
    supplier_id: str | None = Query(None, description="Filter suggestions by primary supplier"),
    urgency: str | None = Query(None, description="Filter by urgency: critical, high, medium"),
    lead_time_buffer_days: int = Query(
        14, ge=1, le=90, description="Supplier lead time buffer in days"
    ),
    service: ReorderSuggestionService = Depends(get_reorder_suggestion_service),
    _user: CurrentUser = Depends(require_permission("inventory:view")),
) -> ReorderSuggestionsResponse:
    """Calculate actionable replenishment suggestions matching configured thresholds and AI demand forecasts."""
    return service.get_reorder_suggestions(
        supplier_id=supplier_id,
        urgency=urgency,
        lead_time_buffer_days=lead_time_buffer_days,
    )


@router.post(
    "/reorder-suggestions/create-po",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft Purchase Order from one or more reorder suggestions",
)
def create_po_from_reorder_suggestions(
    request: CreatePOFromSuggestionsRequest,
    service: ReorderSuggestionService = Depends(get_reorder_suggestion_service),
    user: CurrentUser = Depends(require_permission("inventory:create")),
) -> PurchaseOrderResponse:
    """Create and persist a draft Purchase Order pre-filled from recommended reorder items."""
    return service.create_po_from_suggestions(
        request=request,
        created_by_name=user.email or "AI Reorder Engine",
    )


@router.get(
    "/dead-stock",
    response_model=DeadStockResponse,
    summary="Detect dead stock items with zero outbound movements in the trailing window",
)
def get_dead_stock(
    window_days: int = Query(
        90, ge=1, le=730, description="Trailing observation window in days (e.g., 60, 90, 180)"
    ),
    category_id: str | None = Query(None, description="Filter by product category ID"),
    service: DeadStockService = Depends(get_dead_stock_service),
    _user: CurrentUser = Depends(require_permission("inventory:view")),
) -> DeadStockResponse:
    """Detect inactive items holding tied-up working capital and recommend mitigation actions."""
    return service.get_dead_stock(
        window_days=window_days,
        category_id=category_id,
    )
