"""Pydantic schemas for Purchase Returns (RMA Out) management."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.returns import PurchaseReturnStatusEnum


class PurchaseReturnItemCreateRequest(BaseModel):
    """Schema for adding an item line to a purchase return request."""

    product_id: str = Field(..., description="UUID of the product being returned")
    batch_id: str = Field(..., description="UUID of the specific stock batch being returned from")
    qty: float = Field(..., gt=0, description="Quantity to return in base UoM")
    reason: str | None = Field(None, max_length=255, description="Specific defect or return reason")


class PurchaseReturnCreateRequest(BaseModel):
    """Schema for initiating an outbound supplier return."""

    purchase_order_id: str = Field(..., description="UUID of the original purchase order")
    reason: str | None = Field(None, description="General reason for the return")
    items: list[PurchaseReturnItemCreateRequest] = Field(
        ..., min_length=1, description="List of items and batches being returned"
    )


class PurchaseReturnStatusUpdateRequest(BaseModel):
    """Schema for transitioning purchase return lifecycle status."""

    status: PurchaseReturnStatusEnum = Field(..., description="Target status: shipped or credited")
    credit_note_ref: str | None = Field(
        None,
        max_length=100,
        description="Vendor credit note reference number (required if status is credited)",
    )


class PurchaseReturnItemResponse(BaseModel):
    """Response schema for a single returned item line."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    return_id: str
    product_id: str
    product_name: str = "Unknown Product"
    product_sku: str = "N/A"
    qty: float
    batch_id: str | None = None
    batch_no: str | None = "N/A"
    reason: str | None = None


class PurchaseReturnResponse(BaseModel):
    """Detailed response schema for a Purchase Return."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    purchase_order_id: str
    po_number: str = "N/A"
    supplier_id: str
    supplier_name: str = "Unknown Supplier"
    status: PurchaseReturnStatusEnum
    reason: str | None = None
    credit_note_ref: str | None = None
    requested_at: datetime
    items_count: int = 0
    total_qty: float = 0.0
    items: list[PurchaseReturnItemResponse] = Field(default_factory=list)
