"""Pydantic V2 schemas for Payments, AR Ledger, and Overdue Invoice Detection."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.billing import PaymentMethodEnum


class PaymentCreateRequest(BaseModel):
    """Payload for recording a payment against an invoice."""

    amount: float = Field(..., gt=0, description="Payment amount in INR (must be positive)")
    method: PaymentMethodEnum = Field(
        ..., description="Payment method: cash, bank_transfer, cheque, upi"
    )
    paid_at: datetime | None = Field(default=None, description="Date and time payment was received")
    note: str | None = Field(
        default=None, max_length=500, description="Optional payment reference or remarks"
    )


class PaymentResponse(BaseModel):
    """Response representation of a recorded payment."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str | None
    invoice_no: str | None = None
    retailer_id: str | None
    retailer_name: str | None = None
    customer_id: str | None
    amount: float
    method: PaymentMethodEnum
    paid_at: datetime
    note: str | None
    created_at: datetime


class LedgerEntryResponse(BaseModel):
    """Single debit or credit entry in a retailer's accounts-receivable statement."""

    id: str
    date: datetime
    entry_type: Literal["invoice", "payment"] = Field(
        ..., description="'invoice' charges AR (+), 'payment' settles AR (-)"
    )
    reference_no: str = Field(..., description="Invoice # or Payment Ref")
    description: str
    debit_amount: float = Field(
        default=0.0, description="Billed invoice amount (increases balance owed)"
    )
    credit_amount: float = Field(
        default=0.0, description="Payment received (decreases balance owed)"
    )
    running_balance: float = Field(
        ..., description="Cumulative balance owed after this transaction"
    )
    status: str | None = None


class RetailerLedgerResponse(BaseModel):
    """Chronological Accounts-Receivable statement for a wholesale retailer."""

    retailer_id: str
    retailer_name: str
    gstin: str | None = None
    credit_limit: float
    current_credit_balance: float = Field(
        ..., description="Total outstanding balance currently owed"
    )
    available_credit: float = Field(
        ..., description="Remaining credit buffer before orders are gated"
    )
    total_invoiced: float
    total_paid: float
    entries: list[LedgerEntryResponse]


class OverdueDetectionResponse(BaseModel):
    """Result of running the overdue invoice detection job."""

    due_window_days: int
    scanned_count: int
    overdue_count: int
    overdue_invoice_ids: list[str]
    overdue_invoices: list[dict[str, str | float]]


class EInvoiceGenerateResponse(BaseModel):
    """Response returned when generating or fetching an E-Invoice IRN."""

    invoice_id: str
    invoice_no: str
    irn: str = Field(..., description="64-character statutory Invoice Reference Number (IRN)")
    ack_no: str = Field(..., description="Government IRP Acknowledgment Number")
    ack_date: datetime = Field(..., description="IRP Acknowledgment Timestamp")
    qr_code: str = Field(
        ..., description="Signed QR code string containing statutory invoice summary"
    )
    is_sandbox: bool = Field(default=True, description="True if generated via sandbox/simulator")
    status: str = Field(default="GENERATED", description="IRN Generation Status")


class EWayBillGenerateRequest(BaseModel):
    """Payload for generating an E-Way Bill for an invoice."""

    vehicle_no: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="Vehicle registration number (e.g. DL01AB1234, HR26DQ9988)",
    )
    transporter_id: str | None = Field(
        default=None, max_length=50, description="Transporter ID or GSTIN"
    )
    transporter_name: str | None = Field(
        default=None, max_length=150, description="Transporter Business Name"
    )
    distance_km: int = Field(
        default=50, ge=1, le=5000, description="Transit distance in kilometers"
    )


class EWayBillResponse(BaseModel):
    """Response returned after E-Way Bill generation."""

    invoice_id: str
    invoice_no: str
    e_way_bill_no: str = Field(..., description="12-digit statutory E-Way Bill Number")
    e_way_bill_date: datetime = Field(..., description="E-Way Bill Generation Timestamp")
    valid_until: datetime = Field(..., description="E-Way Bill Validity Expiry")
    vehicle_no: str
    transporter_name: str | None = None
    distance_km: int = 50
    is_sandbox: bool = True


class EInvoiceConfigResponse(BaseModel):
    """Current E-Invoice and E-Way Bill configuration and statutory threshold status."""

    enabled: bool
    gsp_provider: str
    eway_bill_threshold_inr: float
    is_sandbox: bool
    turnover_threshold_notice: str
