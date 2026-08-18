"""Unit of Measure and packaging conversion Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UOMCreateRequest(BaseModel):
    """Payload for creating a unit of measure."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full UoM name (e.g. Piece, Box, Case, Kilogram)",
    )
    abbreviation: str = Field(
        ..., min_length=1, max_length=20, description="Unique short code (e.g. pcs, box, case, kg)"
    )


class UOMUpdateRequest(BaseModel):
    """Payload for modifying a unit of measure."""

    name: str | None = Field(None, min_length=1, max_length=100)
    abbreviation: str | None = Field(None, min_length=1, max_length=20)


class UOMResponse(BaseModel):
    """Response representing a unit of measure."""

    id: str
    name: str
    abbreviation: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductUOMConversionCreateRequest(BaseModel):
    """Payload for defining a packaging ratio for a specific product."""

    from_uom_id: str = Field(..., description="Source Unit of Measure UUID (e.g. Case)")
    to_uom_id: str = Field(..., description="Target Unit of Measure UUID (e.g. Piece)")
    factor: float = Field(
        ..., gt=0, description="Conversion ratio (e.g. 1 Case = 24 Pieces -> factor 24.0)"
    )


class ProductUOMConversionResponse(BaseModel):
    """Response representing a product packaging conversion rule."""

    id: str
    product_id: str
    from_uom_id: str
    to_uom_id: str
    factor: float
    created_at: datetime | None = None
    from_uom: UOMResponse | None = None
    to_uom: UOMResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class UOMConvertRequest(BaseModel):
    """Payload for requesting a conversion calculation."""

    qty: float = Field(..., description="Quantity to convert")
    from_uom_id: str = Field(..., description="Source Unit of Measure UUID")
    to_uom_id: str = Field(..., description="Target Unit of Measure UUID")


class UOMConvertResponse(BaseModel):
    """Response containing calculated conversion output."""

    product_id: str
    original_qty: float
    from_uom_id: str
    to_uom_id: str
    converted_qty: float
