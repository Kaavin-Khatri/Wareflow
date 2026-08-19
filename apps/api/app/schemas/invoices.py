"""Pydantic schemas for GST-compliant wholesale invoices."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InvoiceItemResponse(BaseModel):
    """Line item on an invoice."""

    id: str
    invoice_id: str
    product_id: str
    product_name: str
    hsn_code: str | None = None
    qty: float
    unit_price: float
    tax_rate: float
    tax_amount: float
    total: float
    uom_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(BaseModel):
    """Full GST tax invoice response."""

    id: str
    sales_order_id: str | None = None
    sales_order_number: str | None = None
    buyer_type: str | None = None
    buyer_id: str | None = None
    buyer_name: str | None = None
    buyer_gstin: str | None = None
    buyer_phone: str | None = None
    buyer_email: str | None = None
    buyer_address: str | None = None
    invoice_no: str
    invoice_date: datetime
    gst_rate: float
    subtotal: float
    tax_amount: float
    total_amount: float
    paid_amount: float = 0.0
    outstanding_balance: float = 0.0
    status: str
    e_invoice_irn: str | None = None
    e_invoice_ack_no: str | None = None
    e_invoice_qr_code: str | None = None
    e_way_bill_no: str | None = None
    created_at: datetime
    items: list[InvoiceItemResponse] = Field(default_factory=list)
    payments: list[dict[str, object]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class InvoiceListItemResponse(BaseModel):
    """Summary item for invoice list views."""

    id: str
    sales_order_id: str | None = None
    sales_order_number: str | None = None
    invoice_no: str
    invoice_date: datetime
    buyer_type: str | None = None
    buyer_name: str | None = None
    subtotal: float
    tax_amount: float
    total_amount: float
    paid_amount: float = 0.0
    outstanding_balance: float = 0.0
    status: str
    items_count: int = 0
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    """Paginated list of wholesale invoices."""

    items: list[InvoiceListItemResponse]
    total: int
    page: int
    page_size: int
    pages: int
