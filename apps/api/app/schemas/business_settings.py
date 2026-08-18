"""Business settings and distributor profile schemas."""

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
FSSAI_REGEX = re.compile(r"^\d{14}$")
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


class BusinessSettingsUpdateRequest(BaseModel):
    """Payload for updating distributor business settings & compliance profile."""

    business_name: str = Field(
        ..., min_length=2, max_length=255, description="Legal business / entity name"
    )
    gstin: str | None = Field(None, max_length=50, description="15-character Indian GSTIN")
    fssai_license_no: str | None = Field(
        None, max_length=50, description="14-digit FSSAI food license number"
    )
    fssai_expiry_date: date | None = Field(None, description="FSSAI certificate expiration date")
    address: str | None = Field(None, description="Registered business / warehouse address")
    phone: str | None = Field(None, max_length=50, description="Contact phone number")
    email: str | None = Field(None, max_length=100, description="Official contact email")

    @field_validator("gstin", mode="before")
    @classmethod
    def normalize_gstin(cls, v: str | None) -> str | None:
        """Clean and uppercase GSTIN if provided."""
        if v is None:
            return None
        cleaned = v.strip().upper()
        return cleaned if cleaned else None

    @field_validator("fssai_license_no", mode="before")
    @classmethod
    def normalize_fssai(cls, v: str | None) -> str | None:
        """Clean FSSAI license number if provided."""
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned if cleaned else None


class BusinessSettingsResponse(BaseModel):
    """Schema representing distributor business settings and compliance profile."""

    id: str
    business_name: str
    gstin: str | None = None
    fssai_license_no: str | None = None
    fssai_expiry_date: date | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    updated_at: datetime | None = None

    # Computed compliance helper fields
    fssai_status: str = "unknown"  # "valid" | "expiring_soon" | "expired" | "missing"
    days_until_fssai_expiry: int | None = None

    model_config = ConfigDict(from_attributes=True)
