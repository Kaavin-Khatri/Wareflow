"""Pydantic schemas for the leads feature (request/response DTOs)."""

from datetime import datetime

from pydantic import BaseModel, Field


class LeadResponse(BaseModel):
    """Public representation of a discovered lead."""

    id: str
    place_id: str
    name: str
    category: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    phone: str | None = None
    google_maps_url: str | None = None
    first_seen_at: datetime | None = None
    is_new: bool = True
    contacted: bool = False
    contact_notes: str | None = None
    converted_retailer_id: str | None = None

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    """Paginated list of leads."""

    leads: list[LeadResponse]
    total: int
    page: int
    page_size: int


class ScanRunResponse(BaseModel):
    """Public representation of a completed scan run."""

    id: str
    run_at: datetime | None = None
    center_lat: float
    center_lng: float
    radius_m: int
    results_count: int = 0
    new_count: int = 0

    model_config = {"from_attributes": True}


class ScanRunListResponse(BaseModel):
    """Paginated list of scan runs."""

    runs: list[ScanRunResponse]
    total: int
    page: int
    page_size: int


class ScanNowRequest(BaseModel):
    """Request body for on-demand scan-now endpoint."""

    center_lat: float = Field(..., description="Latitude of scan center", ge=-90, le=90)
    center_lng: float = Field(..., description="Longitude of scan center", ge=-180, le=180)
    radius_km: float = Field(
        default=15.0,
        description="Search radius in kilometers",
        gt=0,
        le=50,
    )


class ScanNowResponse(BaseModel):
    """Response for on-demand scan-now endpoint."""

    scan_run_id: str
    results_count: int
    new_count: int
    message: str


from app.schemas.retailers import PricingTierEnum, RetailerResponse


class MarkContactedRequest(BaseModel):
    """Request body for marking a lead as contacted."""

    contacted: bool = Field(default=True, description="Contacted status flag")
    notes: str | None = Field(default=None, description="Optional contact notes", max_length=2000)


class ConvertLeadToRetailerRequest(BaseModel):
    """Request payload for converting a lead into a wholesale retailer account."""

    contact_person: str | None = Field(None, max_length=100, description="Contact person name")
    email: str | None = Field(None, max_length=100, description="Contact email address")
    gstin: str | None = Field(None, max_length=50, description="GSTIN tax identification number")
    pricing_tier: PricingTierEnum = Field(
        default=PricingTierEnum.STANDARD,
        description="Assigned wholesale pricing tier (standard/silver/gold)",
    )
    credit_limit: float = Field(
        default=0.0,
        ge=0,
        description="Authorized maximum credit limit in INR",
    )
    # Optional field overrides if the owner edited pre-filled fields
    name: str | None = Field(None, max_length=255, description="Override business name")
    phone: str | None = Field(None, max_length=50, description="Override phone number")
    address: str | None = Field(None, description="Override physical address")


class ConvertLeadToRetailerResponse(BaseModel):
    """Response payload returning both the updated lead and the created retailer."""

    lead: LeadResponse
    retailer: RetailerResponse
    message: str = "Lead successfully converted to wholesale retailer"

