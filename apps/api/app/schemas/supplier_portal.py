"""Pydantic schemas for the Supplier Self-Service Portal (Magic Link)."""

from datetime import date, datetime
from pydantic import BaseModel, Field


class SupplierPortalPOItemResponse(BaseModel):
    """Line item representation for supplier view."""

    id: str
    product_name: str
    product_sku: str
    qty_ordered: float
    qty_received: float = 0.0
    unit_cost: float
    uom_name: str | None = None
    base_uom_name: str | None = None
    line_total: float

    model_config = {"from_attributes": True}


class SupplierPortalPOResponse(BaseModel):
    """Public read-only Purchase Order representation for supplier portal."""

    po_id: str
    po_number: str
    supplier_id: str
    supplier_name: str
    status: str
    order_date: datetime
    expected_date: date | None = None
    total_amount: float
    items: list[SupplierPortalPOItemResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ReadyForDispatchResponse(BaseModel):
    """Response returned when supplier marks PO ready for dispatch."""

    success: bool = True
    po_number: str
    status: str
    message: str
