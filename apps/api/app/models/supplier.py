"""Supplier and Purchase Order models."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class POStatusEnum(enum.StrEnum):
    """Purchase Order lifecycle status."""

    DRAFT = "draft"
    ORDERED = "ordered"
    READY_FOR_DISPATCH = "ready_for_dispatch"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class Supplier(Base):
    """Goods manufacturer or vendor."""

    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fssai_license_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fssai_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PurchaseOrder(Base):
    """Purchase Order placed with a supplier."""

    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[POStatusEnum] = mapped_column(
        Enum(POStatusEnum, name="po_status_enum", native_enum=False),
        nullable=False,
        default=POStatusEnum.DRAFT,
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier")
    items: Mapped[list["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan"
    )


class PurchaseOrderItem(Base):
    """Individual line item in a Purchase Order."""

    __tablename__ = "purchase_order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    po_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    qty_ordered: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    qty_received: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    uom_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("units_of_measure.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="items")
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821
    uom: Mapped["app.models.uom.UnitOfMeasure | None"] = relationship(  # noqa: F821
        "UnitOfMeasure"
    )
