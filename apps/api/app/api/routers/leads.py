"""Leads API router — Google Places lead scanner endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.di import get_lead_service
from app.core.security import CurrentUser, require_permission
from app.schemas.leads import (
    LeadListResponse,
    LeadResponse,
    MarkContactedRequest,
    ScanNowRequest,
    ScanNowResponse,
    ScanRunListResponse,
)
from app.services.places_lead_scanner import GooglePlacesLeadService

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post(
    "/scan-now",
    response_model=ScanNowResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger an on-demand lead scan",
)
def scan_now(
    request: ScanNowRequest,
    current_user: CurrentUser = Depends(require_permission("leads.scan")),
    lead_service: GooglePlacesLeadService = Depends(get_lead_service),
) -> ScanNowResponse:
    """Execute an immediate Google Places lead scan and return results summary."""
    scan_run = lead_service.scan(
        center_lat=request.center_lat,
        center_lng=request.center_lng,
        radius_km=request.radius_km,
    )
    plural = "shop" if scan_run.new_count == 1 else "shops"
    message = (
        f"Scan complete: {scan_run.results_count} total results, "
        f"{scan_run.new_count} new {plural} discovered."
    )
    return ScanNowResponse(
        scan_run_id=scan_run.id,
        results_count=scan_run.results_count,
        new_count=scan_run.new_count,
        message=message,
    )


@router.get(
    "",
    response_model=LeadListResponse,
    summary="List discovered leads (paginated, filterable)",
)
def list_leads(
    current_user: CurrentUser = Depends(require_permission("leads.view")),
    lead_service: GooglePlacesLeadService = Depends(get_lead_service),
    is_new: bool | None = Query(None, description="Filter by new status"),
    contacted: bool | None = Query(None, description="Filter by contacted status"),
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search by name or address"),
    min_lat: float | None = Query(None, description="Minimum latitude bounding box"),
    max_lat: float | None = Query(None, description="Maximum latitude bounding box"),
    min_lng: float | None = Query(None, description="Minimum longitude bounding box"),
    max_lng: float | None = Query(None, description="Maximum longitude bounding box"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> LeadListResponse:
    """Return paginated list of leads with optional filters, text search, and map bounds."""
    leads, total = lead_service._lead_repo.list_leads(
        is_new=is_new,
        contacted=contacted,
        category=category,
        search=search,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
        page=page,
        page_size=page_size,
    )
    return LeadListResponse(
        leads=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{lead_id}/contacted",
    response_model=LeadResponse,
    summary="Mark a lead as contacted",
)
def mark_contacted(
    lead_id: str,
    request: MarkContactedRequest,
    current_user: CurrentUser = Depends(require_permission("leads.manage")),
    lead_service: GooglePlacesLeadService = Depends(get_lead_service),
) -> LeadResponse:
    """Mark a discovered lead as contacted, with optional notes."""
    lead = lead_service._lead_repo.mark_lead_contacted(lead_id, request.notes)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead '{lead_id}' not found.",
        )
    return LeadResponse.model_validate(lead)


@router.get(
    "/scan-history",
    response_model=ScanRunListResponse,
    summary="List scan run history",
)
def list_scan_runs(
    current_user: CurrentUser = Depends(require_permission("leads.view")),
    lead_service: GooglePlacesLeadService = Depends(get_lead_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ScanRunListResponse:
    """Return paginated history of lead scan runs."""
    runs, total = lead_service._lead_repo.list_scan_runs(page=page, page_size=page_size)
    return ScanRunListResponse(
        runs=[
            {
                "id": run.id,
                "run_at": run.run_at,
                "center_lat": run.center_lat,
                "center_lng": run.center_lng,
                "radius_m": run.radius_m,
                "results_count": run.results_count,
                "new_count": run.new_count,
            }
            for run in runs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
