"""Product request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.categories import CategoryResponse


class ProductPriceUpdateRequest(BaseModel):
    """Schema for updating product prices."""

    wholesale_price: float = Field(..., ge=0, description="New wholesale unit selling price")
    cost_price: float | None = Field(None, ge=0, description="New purchase/cost price")


class ProductCreateRequest(BaseModel):
    """Payload for creating a new product in the wholesale catalog."""

    sku: str = Field(..., min_length=2, max_length=100, description="Unique SKU code")
    name: str = Field(..., min_length=2, max_length=255, description="Product display name")
    description: str | None = Field(None, description="Detailed product description")
    content_details: str | None = Field(
        None, description="Ingredients, composition, or nutritional details"
    )
    category_id: str | None = Field(None, description="Category UUID")
    base_uom_id: str | None = Field(None, description="Base Unit of Measure UUID")
    unit: str | None = Field(None, max_length=50, description="Primary unit (e.g. Bag, Box, Kg)")
    cost_price: float = Field(0.0, ge=0, description="Standard procurement cost price")
    wholesale_price: float = Field(0.0, ge=0, description="Standard wholesale selling price")
    reorder_point: int = Field(10, ge=0, description="Threshold quantity triggering reorder alert")
    reorder_qty: int = Field(50, ge=1, description="Default reorder batch quantity")
    barcode: str | None = Field(None, max_length=100, description="EAN/UPC barcode number")
    hsn_code: str | None = Field(None, max_length=50, description="GST HSN code")
    image_url: str | None = Field(None, max_length=500, description="Public product image URL")


class ProductUpdateRequest(BaseModel):
    """Payload for updating product catalog metadata."""

    sku: str | None = Field(None, min_length=2, max_length=100)
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    content_details: str | None = None
    category_id: str | None = None
    base_uom_id: str | None = None
    unit: str | None = None
    cost_price: float | None = Field(None, ge=0)
    wholesale_price: float | None = Field(None, ge=0)
    reorder_point: int | None = Field(None, ge=0)
    reorder_qty: int | None = Field(None, ge=1)
    barcode: str | None = None
    hsn_code: str | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    """Schema representing complete product details."""

    id: str
    sku: str
    name: str
    description: str | None = None
    content_details: str | None = None
    image_url: str | None = None
    hsn_code: str | None = None
    category_id: str | None = None
    base_uom_id: str | None = None
    unit: str | None = None
    cost_price: float
    wholesale_price: float
    reorder_point: int
    reorder_qty: int
    barcode: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    category: CategoryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductImageUploadResponse(BaseModel):
    """Response returned after successful product image upload."""

    product_id: str
    image_url: str
