"""Admin Audit Log router."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.core.di import get_audit_service
from app.core.security import CurrentUser, require_permission
from app.schemas.audit import AuditLogListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin/audit-log", tags=["Admin Audit Log"])


@router.get(
    "",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List paginated admin action audit logs",
)
def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    entity_type: str | None = Query(
        None, description="Filter by entity type (product, retailer, etc.)"
    ),
    actor_id: str | None = Query(None, description="Filter by actor ID"),
    action: str | None = Query(None, description="Filter by specific action name"),
    start_date: datetime | None = Query(None, description="Start date filter (inclusive)"),
    end_date: datetime | None = Query(None, description="End date filter (inclusive)"),
    current_user: CurrentUser = Depends(require_permission("audit:view")),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditLogListResponse:
    """Retrieve filtered and human-readable administrator action logs."""
    return audit_service.list_logs(
        page=page,
        page_size=page_size,
        entity_type=entity_type,
        actor_id=actor_id,
        start_date=start_date,
        end_date=end_date,
        action=action,
    )
