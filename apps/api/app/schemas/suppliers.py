"""Supplier request and response schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SupplierCreateRequest(BaseModel):
    """Payload for creating a new goods supplier/vendor."""

    name: str = Field(..., min_length=2, max_length=255, description="Supplier company name")
    contact_person: str | None = Field(None, max_length=100, description="Primary contact name")
    phone: str | None = Field(None, max_length=50, description="Primary contact phone number")
    email: str | None = Field(None, max_length=100, description="Primary contact email address")
    address: str | None = Field(None, description="Physical billing / dispatch address")
    gstin: str | None = Field(
        None, max_length=50, description="15-character Indian Goods & Services Tax ID"
    )
    fssai_license_no: str | None = Field(
        None, max_length=50, description="14-digit FSSAI food license"
    )
    fssai_expiry_date: date | None = Field(None, description="FSSAI certificate expiration date")
    is_active: bool = Field(True, description="Active status for procurement operations")

    @field_validator("gstin", mode="before")
    @classmethod
    def normalize_gstin(cls, v: str | None) -> str | None:
        """Strip whitespace and convert GSTIN to uppercase if provided."""
        if v is None:
            return None
        cleaned = v.strip().upper()
        return cleaned if cleaned else None

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Clean name string."""
        if isinstance(v, str):
            return v.strip()
        return v


class SupplierUpdateRequest(BaseModel):
    """Payload for updating an existing supplier record."""

    name: str | None = Field(None, min_length=2, max_length=255)
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    gstin: str | None = None
    fssai_license_no: str | None = None
    fssai_expiry_date: date | None = None
    is_active: bool | None = None

    @field_validator("gstin", mode="before")
    @classmethod
    def normalize_gstin(cls, v: str | None) -> str | None:
        """Strip whitespace and convert GSTIN to uppercase if provided."""
        if v is None:
            return None
        cleaned = v.strip().upper()
        return cleaned if cleaned else None

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: str | None) -> str | None:
        """Clean name string if provided."""
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v


class SupplierResponse(BaseModel):
    """Schema representing complete supplier details."""

    id: str
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    gstin: str | None = None
    fssai_license_no: str | None = None
    fssai_expiry_date: date | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
