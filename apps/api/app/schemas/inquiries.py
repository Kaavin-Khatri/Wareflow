"""Product inquiry schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CreateInquiryRequest(BaseModel):
    """Payload for submitting a product inquiry from the retailer portal."""

    product_id: str = Field(..., description="Target product ID")
    message: str = Field(..., min_length=1, max_length=2000, description="Inquiry question or quote request")


class RespondInquiryRequest(BaseModel):
    """Payload for staff responding to an inquiry."""

    response: str = Field(..., min_length=1, max_length=2000, description="Staff answer or response text")


class ProductInquiryResponse(BaseModel):
    """Response payload for a product inquiry."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    product_name: str = "Unknown Product"
    product_sku: str = "N/A"
    retailer_id: str | None = None
    retailer_name: str | None = None
    customer_id: str | None = None
    message: str
    status: str
    response: str | None = None
    created_at: datetime
    responded_at: datetime | None = None
