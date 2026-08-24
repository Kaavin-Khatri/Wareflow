from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.di import (
    get_anomaly_detection_service,
    get_ar_aging_service,
    get_dead_stock_service,
    get_export_service,
    get_forecasting_service,
    get_insight_narrator_service,
    get_owner_dashboard_service,
    get_reorder_suggestion_service,
)
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.analytics import (
    ARAgingReportResponse,
    CreatePOFromSuggestionsRequest,
    DeadStockResponse,
    OrderAnomalyReportResponse,
    OwnerDashboardResponse,
    ReorderSuggestionsResponse,
    WeeklyInsightResponse,
)
from app.schemas.forecast import ForecastSummaryResponse
from app.schemas.purchase_orders import PurchaseOrderResponse
from app.services.anomaly_detection_service import AnomalyDetectionService
from app.services.ar_aging_service import ARAgingService
from app.services.dead_stock_service import DeadStockService
from app.services.export_service import ExportService
from app.services.forecasting_service import ForecastingService
from app.services.insight_narrator import InsightNarratorService
from app.services.owner_dashboard_service import OwnerDashboardService
from app.services.reorder_suggestion_service import ReorderSuggestionService

router = APIRouter(prefix="/analytics", tags=["Analytics & AI"])


@router.get(
    "/dashboard",
    response_model=OwnerDashboardResponse,
    summary="Get complete wholesale owner analytics dashboard metrics and 30d series in one call",
)
def get_owner_dashboard(
    service: OwnerDashboardService = Depends(get_owner_dashboard_service),
    _user: CurrentUser = Depends(get_current_user),
) -> OwnerDashboardResponse:
    """Aggregate executive KPIs, 30d movement trendline, low-stock quick items, and accounts receivable aging."""
    return service.get_owner_dashboard()


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


@router.get(
    "/anomalies/order/{order_id}",
    response_model=OrderAnomalyReportResponse,
    summary="Detect statistical quantity anomalies for a specific sales order",
)
def get_order_anomalies(
    order_id: str,
    service: AnomalyDetectionService = Depends(get_anomaly_detection_service),
    _user: CurrentUser = Depends(get_current_user),
) -> OrderAnomalyReportResponse:
    """Evaluate line items of a sales order against historical ordering patterns (3σ threshold)."""
    report = service.detect_anomalies_for_order_id(order_id=order_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sales order '{order_id}' not found.",
        )
    return report


@router.get(
    "/weekly-insight",
    response_model=WeeklyInsightResponse,
    summary="Get 7-day executive intelligence briefing summarizing sales velocity and inventory risks",
)
def get_weekly_insight(
    force_refresh: bool = Query(
        False, description="Force recalculation bypassing 7-day cache"
    ),
    service: InsightNarratorService = Depends(get_insight_narrator_service),
    _user: CurrentUser = Depends(get_current_user),
) -> WeeklyInsightResponse:
    """Synthesize demand forecasts, reorder alerts, dead stock, and sales into a grounded executive narrative."""
    return service.get_weekly_insight(force_refresh=force_refresh)


@router.get(
    "/ar-aging",
    response_model=ARAgingReportResponse,
    summary="Get accounts-receivable aging report across wholesale retailers in 30/60/90+ day buckets",
)
def get_ar_aging_report(
    include_zero_balance: bool = Query(
        True, description="Include active retailers with zero outstanding balance"
    ),
    service: ARAgingService = Depends(get_ar_aging_service),
    _user: CurrentUser = Depends(require_permission("invoices:view")),
) -> ARAgingReportResponse:
    """Compute aged receivables breakdown (Current, 1-30, 31-60, 61-90, 90+ days) per retailer."""
    return service.get_ar_aging_report(include_zero_balance=include_zero_balance)


@router.get(
    "/ar-aging.xlsx",
    status_code=status.HTTP_200_OK,
    summary="Download Accounts-Receivable aging report Excel workbook",
)
def download_ar_aging_excel(
    include_zero_balance: bool = Query(True, description="Include accounts with zero outstanding balance"),
    export_service: ExportService = Depends(get_export_service),
    _user: CurrentUser = Depends(require_permission("invoices:view")),
) -> Response:
    """Generate and download structured Accounts-Receivable Aging Excel spreadsheet."""
    xlsx_bytes = export_service.generate_ar_aging_excel(include_zero_balance=include_zero_balance)
    dt_str = datetime.now().strftime("%Y%m%d")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="ar_aging_{dt_str}.xlsx"'},
    )
