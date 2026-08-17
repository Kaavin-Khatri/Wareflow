"""Product request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class ProductPriceUpdateRequest(BaseModel):
    """Schema for updating product prices."""

    wholesale_price: float = Field(..., ge=0, description="New wholesale unit selling price")
    cost_price: float | None = Field(None, ge=0, description="New purchase/cost price")


class ProductResponse(BaseModel):
    """Schema representing product details."""

    id: str
    sku: str
    name: str
    description: str | None = None
    unit: str | None = None
    wholesale_price: float
    cost_price: float
    reorder_point: int
    reorder_qty: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
