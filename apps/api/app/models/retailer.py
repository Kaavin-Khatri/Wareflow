"""Retailer and Sales Order models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SOStatusEnum(enum.StrEnum):
    """Sales Order lifecycle status."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Retailer(Base):
    """B2B Retailer / Customer purchasing wholesale products."""

    __tablename__ = "retailers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pricing_tier: Mapped[str | None] = mapped_column(String(50), nullable=True, default="standard")
    credit_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    credit_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SalesOrder(Base):
    """Wholesale Sales Order placed by or for a retailer."""

    __tablename__ = "sales_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    so_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    retailer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("retailers.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[SOStatusEnum] = mapped_column(
        Enum(SOStatusEnum, name="so_status_enum", native_enum=False),
        nullable=False,
        default=SOStatusEnum.DRAFT,
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    retailer: Mapped["Retailer"] = relationship("Retailer")
    items: Mapped[list["SalesOrderItem"]] = relationship(
        "SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan"
    )


class SalesOrderItem(Base):
    """Individual line item in a Sales Order."""

    __tablename__ = "sales_order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    so_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    qty: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    uom_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("units_of_measure.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="items")
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821
    uom: Mapped["app.models.uom.UnitOfMeasure | None"] = relationship(  # noqa: F821
        "UnitOfMeasure"
    )
