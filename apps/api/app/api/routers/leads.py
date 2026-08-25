"""Leads API router — Google Places lead scanner endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.di import get_lead_service, get_retailer_service
from app.core.security import CurrentUser, require_permission
from app.schemas.leads import (
    ConvertLeadToRetailerRequest,
    ConvertLeadToRetailerResponse,
    LeadListResponse,
    LeadResponse,
    MarkContactedRequest,
    ScanNowRequest,
    ScanNowResponse,
    ScanRunListResponse,
)
from app.schemas.retailers import RetailerCreateRequest, RetailerResponse
from app.services.places_lead_scanner import GooglePlacesLeadService
from app.services.retailer_service import RetailerService

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
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Update lead contact status and notes",
)
@router.patch(
    "/{lead_id}/contacted",
    response_model=LeadResponse,
    summary="Mark a lead as contacted",
)
def update_lead_contact(
    lead_id: str,
    request: MarkContactedRequest,
    current_user: CurrentUser = Depends(require_permission("leads.manage")),
    lead_service: GooglePlacesLeadService = Depends(get_lead_service),
) -> LeadResponse:
    """Mark a discovered lead as contacted (clearing is_new highlight) with optional notes."""
    lead = lead_service._lead_repo.mark_lead_contacted(
        lead_id=lead_id, notes=request.notes, contacted=request.contacted
    )
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead '{lead_id}' not found.",
        )
    return LeadResponse.model_validate(lead)


@router.post(
    "/{lead_id}/convert-to-retailer",
    response_model=ConvertLeadToRetailerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Convert a lead into a wholesale retailer account",
)
def convert_lead_to_retailer(
    lead_id: str,
    request: ConvertLeadToRetailerRequest,
    current_user: CurrentUser = Depends(require_permission("leads.manage")),
    lead_service: GooglePlacesLeadService = Depends(get_lead_service),
    retailer_service: RetailerService = Depends(get_retailer_service),
) -> ConvertLeadToRetailerResponse:
    """
    Convert a discovered lead into an active wholesale retailer account.

    Pre-fills business name, phone, and address from the lead.
    Sets lead.converted_retailer_id, lead.contacted = True, lead.is_new = False.
    Prevents duplicate conversion if lead has already been converted.
    """
    lead = lead_service._lead_repo.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead '{lead_id}' not found.",
        )

    if lead.converted_retailer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead has already been converted to a retailer.",
        )

    # Pre-fill retailer create request using lead details with optional overrides
    retailer_payload = RetailerCreateRequest(
        name=request.name or lead.name,
        contact_person=request.contact_person,
        phone=request.phone or lead.phone,
        email=request.email,
        address=request.address or lead.address,
        gstin=request.gstin,
        pricing_tier=request.pricing_tier,
        credit_limit=request.credit_limit,
        is_active=True,
    )

    # Create retailer record through standard RetailerService (applies validation & audit logs)
    created_retailer = retailer_service.create_retailer(
        payload=retailer_payload, actor_id=current_user.id
    )

    # Link lead to created retailer and clear is_new highlight
    updated_lead = lead_service._lead_repo.link_converted_retailer(
        lead_id=lead_id, retailer_id=created_retailer.id
    )
    if not updated_lead:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead conversion link.",
        )

    return ConvertLeadToRetailerResponse(
        lead=LeadResponse.model_validate(updated_lead),
        retailer=RetailerResponse.model_validate(created_retailer),
        message=f"Shop '{created_retailer.name}' successfully converted to wholesale retailer account.",
    )



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
