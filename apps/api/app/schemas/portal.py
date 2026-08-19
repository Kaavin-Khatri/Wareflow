"""Pydantic schemas for the Retailer Self-Service Portal."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PortalBootstrapRequest(BaseModel):
    """Schema for retailer portal signup or first login."""

    invite_token: str | None = Field(None, description="Invite token received via email/link")
    display_name: str | None = None
    phone: str | None = None


class RetailerPortalMeResponse(BaseModel):
    """Authenticated retailer identity and account status."""

    id: str = Field(..., description="Firebase UID of caller")
    email: str
    retailer_id: str
    retailer_name: str
    contact_person: str | None = None
    phone: str | None = None
    address: str | None = None
    gstin: str | None = None
    pricing_tier: str = "standard"
    credit_limit: float
    credit_balance: float
    is_active: bool
    account_type: str = "retailer"

    @property
    def available_credit(self) -> float:
        """Remaining available credit."""
        return max(0.0, float(self.credit_limit) - float(self.credit_balance))

    model_config = ConfigDict(from_attributes=True)


class PortalOrderListItemResponse(BaseModel):
    """Order summary for retailer portal view."""

    id: str
    so_number: str
    status: str
    order_date: datetime | None = None
    total_amount: float
    items_count: int = 0
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PortalInvoiceListItemResponse(BaseModel):
    """Invoice summary for retailer portal view."""

    id: str
    invoice_number: str
    sales_order_id: str
    status: str
    issue_date: datetime | None = None
    due_date: datetime | None = None
    total_amount: float
    paid_amount: float = 0.0
    outstanding_balance: float = 0.0
    e_invoice_irn: str | None = None
    e_way_bill_no: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PortalCatalogProductResponse(BaseModel):
    """Tier-priced product entity with privacy-preserving availability band."""

    id: str
    sku: str
    name: str
    description: str | None = None
    content_details: str | None = None
    image_url: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    unit: str = "Piece"
    base_price: float = Field(..., description="Standard wholesale unit price before tier discount")
    effective_price: float = Field(..., description="Retailer-specific tier-discounted unit price")
    discount_percentage: float = 0.0
    pricing_tier: str = "standard"
    availability: str = Field(..., description="Privacy-preserving stock status: Available, Low, or Out")
    hsn_code: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PortalCategoryResponse(BaseModel):
    """Category lookup for portal filter dropdowns."""

    id: str
    name: str

    model_config = ConfigDict(from_attributes=True)
