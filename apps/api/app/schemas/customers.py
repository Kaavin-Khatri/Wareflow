"""Customer request and response schemas for direct walk-in buyers."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreateRequest(BaseModel):
    """Schema for registering a direct/walk-in end-customer."""

    name: str = Field(..., min_length=2, max_length=255, description="Customer name")
    phone: str | None = Field(None, max_length=50, description="Contact phone number")
    email: EmailStr | None = Field(None, description="Contact email address")
    address: str | None = Field(
        None, max_length=1000, description="Customer billing/delivery address"
    )
    notes: str | None = Field(None, max_length=1000, description="Internal customer notes")


class CustomerUpdateRequest(BaseModel):
    """Schema for updating a direct customer record."""

    name: str | None = Field(None, min_length=2, max_length=255)
    phone: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=1000)


class CustomerResponse(BaseModel):
    """Schema for customer entity in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    notes: str | None = None
    created_at: datetime
    total_orders_count: int = 0
    total_spend: float = 0.0


class CustomerListResponse(BaseModel):
    """Paginated list of direct customers."""

    items: list[CustomerResponse]
    total: int
    skip: int
    limit: int
