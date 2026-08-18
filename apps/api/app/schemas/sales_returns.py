"""Sales Return (RMA In) request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.returns import ReturnItemConditionEnum, SalesReturnStatusEnum


class SalesReturnItemCreateRequest(BaseModel):
    """Schema for returning a specific product item from a sales order."""

    product_id: str = Field(..., description="ID of the product being returned")
    qty: float = Field(..., gt=0, description="Quantity to return")
    batch_id: str | None = Field(
        None, description="Specific batch ID returned from original order line"
    )
    condition: ReturnItemConditionEnum = Field(
        default=ReturnItemConditionEnum.RESELLABLE,
        description="Condition: 'resellable' (restocked) or 'damaged' (written off)",
    )
    reason: str | None = Field(None, max_length=500, description="Reason for line return")


class SalesReturnCreateRequest(BaseModel):
    """Schema for initiating an inbound retailer sales return (RMA In)."""

    sales_order_id: str = Field(..., description="Original Sales Order ID")
    retailer_id: str | None = Field(
        None, description="Retailer ID (derived from sales order if omitted)"
    )
    reason: str | None = Field(None, max_length=1000, description="Reason for return request")
    items: list[SalesReturnItemCreateRequest] = Field(
        ..., min_length=1, description="List of items being returned"
    )


class SalesReturnStatusUpdateRequest(BaseModel):
    """Schema for transitioning return status (e.g. approve or reject)."""

    status: SalesReturnStatusEnum = Field(..., description="Next status for the return")
    rejection_reason: str | None = Field(
        None, max_length=500, description="Reason required when rejecting"
    )


class SalesReturnItemResponse(BaseModel):
    """Schema for an individual returned line item in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    return_id: str
    product_id: str
    product_name: str | None = None
    product_sku: str | None = None
    qty: float
    batch_id: str | None = None
    batch_no: str | None = None
    condition: ReturnItemConditionEnum
    unit_price: float = 0.0
    refund_amount: float = 0.0


class SalesReturnResponse(BaseModel):
    """Schema for a Sales Return record in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    sales_order_id: str
    so_number: str | None = None
    retailer_id: str
    retailer_name: str | None = None
    status: SalesReturnStatusEnum
    reason: str | None = None
    credit_adjustment_amount: float = 0.0
    requested_at: datetime
    items: list[SalesReturnItemResponse] = Field(default_factory=list)


class SalesReturnListResponse(BaseModel):
    """Paginated list schema for Sales Return records."""

    items: list[SalesReturnResponse]
    total: int
    skip: int
    limit: int
