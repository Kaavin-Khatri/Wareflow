"""Retailer request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class RetailerCreditLimitUpdateRequest(BaseModel):
    """Schema for updating retailer credit limits."""

    credit_limit: float = Field(..., ge=0, description="New authorized credit limit in INR")


class RetailerResponse(BaseModel):
    """Schema representing retailer details."""

    id: str
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    credit_limit: float
    credit_balance: float
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
