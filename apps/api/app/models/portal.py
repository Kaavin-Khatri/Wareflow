"""Self-service portal, magic links, walk-in customers, and inquiries."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChannelPreferenceEnum(enum.StrEnum):
    """Back-in-stock notification channel preference."""

    WHATSAPP = "whatsapp"
    EMAIL = "email"
    BOTH = "both"


class InquiryStatusEnum(enum.StrEnum):
    """Product inquiry status."""

    OPEN = "open"
    RESPONDED = "responded"
    CLOSED = "closed"


class Customer(Base):
    """
    Direct walk-in or small buyer account.

    Separate from wholesale Retailer accounts (no credit limit or pricing tiers).
    """

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StockSubscription(Base):
    """Retailer's standing back-in-stock alert subscription."""

    __tablename__ = "stock_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    retailer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("retailers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_preference: Mapped[ChannelPreferenceEnum] = mapped_column(
        Enum(ChannelPreferenceEnum, name="channel_preference_enum", native_enum=False),
        nullable=False,
        default=ChannelPreferenceEnum.BOTH,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    retailer: Mapped["app.models.retailer.Retailer"] = relationship("Retailer")  # noqa: F821
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821


class SupplierAccessToken(Base):
    """
    Short-lived, single-purpose magic link token.

    Allows a supplier/manufacturer to mark a Purchase Order 'ready_for_dispatch'
    from mobile without creating a supplier login account.
    """

    __tablename__ = "supplier_access_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purchase_order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    supplier: Mapped["app.models.supplier.Supplier"] = relationship("Supplier")  # noqa: F821
    purchase_order: Mapped["app.models.supplier.PurchaseOrder"] = relationship(  # noqa: F821
        "PurchaseOrder"
    )


class ProductInquiry(Base):
    """Customer or retailer inquiry/quote request from catalog portal."""

    __tablename__ = "product_inquiries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    retailer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("retailers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InquiryStatusEnum] = mapped_column(
        Enum(InquiryStatusEnum, name="inquiry_status_enum", native_enum=False),
        nullable=False,
        default=InquiryStatusEnum.OPEN,
    )
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821
    retailer: Mapped["app.models.retailer.Retailer | None"] = relationship("Retailer")  # noqa: F821
    customer: Mapped["Customer | None"] = relationship("Customer")
