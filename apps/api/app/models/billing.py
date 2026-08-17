"""Billing, Invoicing, and Payment models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InvoiceStatusEnum(enum.StrEnum):
    """Invoice payment lifecycle status."""

    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentMethodEnum(enum.StrEnum):
    """Accepted payment methods."""

    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    UPI = "upi"


class Invoice(Base):
    """GST-compliant wholesale tax invoice."""

    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_order_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sales_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    invoice_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=18.00)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    status: Mapped[InvoiceStatusEnum] = mapped_column(
        Enum(InvoiceStatusEnum, name="invoice_status_enum", native_enum=False),
        nullable=False,
        default=InvoiceStatusEnum.UNPAID,
    )
    e_invoice_irn: Mapped[str | None] = mapped_column(String(100), nullable=True)
    e_invoice_ack_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    e_invoice_qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    e_way_bill_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    sales_order: Mapped["app.models.retailer.SalesOrder | None"] = relationship(  # noqa: F821
        "SalesOrder"
    )
    items: Mapped[list["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="invoice")


class InvoiceItem(Base):
    """
    Frozen snapshot line item on an invoice.

    Not live-linked to sales order items to preserve immutable accounting records.
    """

    __tablename__ = "invoice_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hsn_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qty: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=18.00)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    uom_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("units_of_measure.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821


class Payment(Base):
    """Payment record netting against invoices and updating retailer credit."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    retailer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("retailers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[PaymentMethodEnum] = mapped_column(
        Enum(PaymentMethodEnum, name="payment_method_enum", native_enum=False),
        nullable=False,
    )
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice | None"] = relationship("Invoice", back_populates="payments")
    retailer: Mapped["app.models.retailer.Retailer | None"] = relationship("Retailer")  # noqa: F821
    customer: Mapped["app.models.portal.Customer | None"] = relationship("Customer")  # noqa: F821
