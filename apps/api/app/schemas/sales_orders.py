"""Sales Order request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.retailer import BuyerTypeEnum, SOStatusEnum


class SalesOrderItemCreateRequest(BaseModel):
    """Schema for adding an item line when creating a Sales Order."""

    product_id: str = Field(..., description="Target product ID")
    qty: float = Field(..., gt=0, description="Quantity in ordered UoM")
    uom_id: str | None = Field(None, description="Optional custom UoM ID")
    unit_price: float | None = Field(
        None,
        ge=0,
        description="Optional price override; if omitted, computed from retailer pricing tier",
    )


class SalesOrderCreateRequest(BaseModel):
    """Schema for creating a new draft Sales Order."""

    buyer_type: BuyerTypeEnum = Field(
        default=BuyerTypeEnum.RETAILER,
        description="Buyer type discriminator ('retailer' or 'customer')",
    )
    retailer_id: str | None = Field(
        None, description="Retailer ID (required if buyer_type='retailer')"
    )
    customer_id: str | None = Field(
        None, description="Customer ID (required if buyer_type='customer')"
    )
    items: list[SalesOrderItemCreateRequest] = Field(
        ..., min_length=1, description="List of line items in the sales order"
    )


class SalesOrderStatusUpdateRequest(BaseModel):
    """Schema for updating a Sales Order's fulfillment lifecycle status."""

    status: SOStatusEnum = Field(..., description="New target status")
    notes: str | None = Field(
        None, max_length=500, description="Optional transition notes or tracking info"
    )


class SalesOrderItemResponse(BaseModel):
    """Schema for a line item in a Sales Order response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    so_id: str
    product_id: str
    product_name: str | None = None
    product_sku: str | None = None
    qty: float
    unit_price: float
    line_total: float = 0.0
    uom_id: str | None = None
    uom_code: str | None = None
    is_unusual: bool = False
    anomaly_reason: str | None = None
    historical_mean: float | None = None
    historical_stddev: float | None = None


class SalesOrderResponse(BaseModel):
    """Comprehensive schema for a Sales Order response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    so_number: str
    buyer_type: BuyerTypeEnum
    retailer_id: str | None = None
    retailer_name: str | None = None
    retailer_pricing_tier: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    status: SOStatusEnum
    order_date: datetime
    total_amount: float
    created_at: datetime
    items: list[SalesOrderItemResponse] = []
    has_unusual_items: bool = False
    unusual_items_count: int = 0
    anomaly_warnings: list[str] = []


class SalesOrderListResponse(BaseModel):
    """Paginated list of sales orders."""

    items: list[SalesOrderResponse]
    total: int
    skip: int
    limit: int
