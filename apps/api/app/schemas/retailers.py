"""Retailer request and response schemas with bulk pricing tiers."""

import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PricingTierEnum(enum.StrEnum):
    """Wholesale pricing tiers for bulk buyers."""

    STANDARD = "standard"
    SILVER = "silver"
    GOLD = "gold"


class RetailerCreateRequest(BaseModel):
    """Schema for registering a wholesale retailer."""

    name: str = Field(..., min_length=1, max_length=255, description="Business / Retailer name")
    contact_person: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=100)
    address: str | None = None
    gstin: str | None = Field(None, max_length=50)
    pricing_tier: PricingTierEnum = Field(
        default=PricingTierEnum.STANDARD,
        description="Assigned wholesale pricing tier (standard/silver/gold)",
    )
    credit_limit: float = Field(
        default=0.0,
        ge=0,
        description="Authorized maximum credit limit in INR",
    )
    is_active: bool = Field(default=True)


class RetailerUpdateRequest(BaseModel):
    """Schema for updating an existing wholesale retailer."""

    name: str | None = Field(None, min_length=1, max_length=255)
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    gstin: str | None = None
    pricing_tier: PricingTierEnum | None = None
    credit_limit: float | None = Field(None, ge=0)
    is_active: bool | None = None


class RetailerCreditLimitUpdateRequest(BaseModel):
    """Schema for specifically updating retailer credit limits."""

    credit_limit: float = Field(..., ge=0, description="New authorized credit limit in INR")


class RetailerResponse(BaseModel):
    """Schema representing full retailer account details."""

    id: str
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    gstin: str | None = None
    pricing_tier: str = "standard"
    credit_limit: float
    credit_balance: float
    is_active: bool
    created_at: datetime | None = None

    @property
    def available_credit(self) -> float:
        """Computed available credit remaining."""
        return max(0.0, float(self.credit_limit) - float(self.credit_balance))

    model_config = ConfigDict(from_attributes=True)
