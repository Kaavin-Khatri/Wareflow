"""Alert engine and compliance monitoring API router."""

from fastapi import APIRouter, Depends

from app.core.di import get_alert_engine_service
from app.core.security import CurrentUser, get_current_user
from app.schemas.alerts import AlertItemResponse, ComplianceSummaryResponse
from app.services.alert_engine_service import AlertEngineService

router = APIRouter(prefix="/alerts", tags=["Alerts & Compliance"])


@router.get(
    "/compliance",
    response_model=ComplianceSummaryResponse,
    summary="Get comprehensive compliance summary and active regulatory alerts",
)
def get_compliance_summary(
    alert_engine: AlertEngineService = Depends(get_alert_engine_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> ComplianceSummaryResponse:
    """Evaluate and return active FSSAI license compliance metrics and active alerts."""
    return alert_engine.get_compliance_summary()


@router.post(
    "/evaluate",
    response_model=list[AlertItemResponse],
    summary="Trigger alert engine evaluation across all registered rules",
)
def evaluate_alerts(
    alert_engine: AlertEngineService = Depends(get_alert_engine_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[AlertItemResponse]:
    """Execute all active AlertRule strategies and return fired alerts."""
    return alert_engine.evaluate_all()
