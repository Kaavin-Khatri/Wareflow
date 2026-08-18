"""Pydantic schemas for Purchase Order lifecycle and goods receiving."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.supplier import POStatusEnum


class POItemCreateRequest(BaseModel):
    """Line item payload for creating a Purchase Order."""

    product_id: str = Field(..., description="Target product ID to order")
    qty_ordered: Annotated[float, Field(gt=0, description="Quantity to order in specified UoM")]
    unit_cost: Annotated[float, Field(ge=0, description="Cost per unit in specified UoM")]
    uom_id: str | None = Field(
        None, description="Optional unit of measure ID (defaults to product base UoM)"
    )


class POCreateRequest(BaseModel):
    """Payload for creating a new draft Purchase Order."""

    supplier_id: str = Field(..., description="Target supplier ID")
    expected_date: date | None = Field(None, description="Expected delivery date")
    items: list[POItemCreateRequest] = Field(
        ..., min_length=1, description="List of line items (at least one required)"
    )


class POItemUpdateRequest(BaseModel):
    """Line item payload for updating a draft Purchase Order."""

    id: str | None = Field(None, description="Existing line item ID if modifying, None if adding")
    product_id: str = Field(..., description="Target product ID")
    qty_ordered: Annotated[float, Field(gt=0, description="Quantity to order")]
    unit_cost: Annotated[float, Field(ge=0, description="Cost per unit")]
    uom_id: str | None = Field(None, description="Unit of measure ID")


class POUpdateRequest(BaseModel):
    """Payload for editing a draft Purchase Order."""

    supplier_id: str | None = Field(None, description="Updated supplier ID")
    expected_date: date | None = Field(None, description="Updated expected delivery date")
    items: list[POItemUpdateRequest] | None = Field(
        None, min_length=1, description="Updated list of line items"
    )


class POReceiveItemRequest(BaseModel):
    """Individual line item goods receipt payload."""

    po_item_id: str = Field(..., description="Purchase Order line item ID being received")
    qty_received: Annotated[float, Field(gt=0, description="Quantity received in this delivery")]
    uom_id: str | None = Field(
        None, description="UoM of received goods (defaults to PO item's ordered UoM)"
    )
    batch_no: str = Field(
        ..., min_length=1, max_length=100, description="Manufacturer/warehouse batch number"
    )
    expiry_date: date | None = Field(None, description="Batch expiration date (if applicable)")
    warehouse_id: str = Field(..., description="Destination warehouse ID storing the stock")


class POReceiveRequest(BaseModel):
    """Batch receiving payload for receiving full or partial goods on a Purchase Order."""

    items: list[POReceiveItemRequest] = Field(
        ..., min_length=1, description="List of items being received"
    )


class POItemResponse(BaseModel):
    """Structured response for a Purchase Order line item."""

    id: str
    po_id: str
    product_id: str
    product_name: str
    product_sku: str
    qty_ordered: float
    qty_received: float
    unit_cost: float
    uom_id: str | None = None
    uom_name: str | None = None
    base_uom_name: str | None = None
    line_total: float

    model_config = {"from_attributes": True}


class PurchaseOrderResponse(BaseModel):
    """Detailed response for a Purchase Order with supplier info and line items."""

    id: str
    po_number: str
    supplier_id: str
    supplier_name: str
    status: POStatusEnum
    order_date: datetime
    expected_date: date | None = None
    total_amount: float
    items_count: int
    items: list[POItemResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderListResponse(BaseModel):
    """Paginated list of purchase orders."""

    items: list[PurchaseOrderResponse]
    total: int
