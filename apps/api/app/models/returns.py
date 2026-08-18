"""Returns management models for sales and purchase orders."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SalesReturnStatusEnum(enum.StrEnum):
    """Sales Return lifecycle status."""

    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ReturnItemConditionEnum(enum.StrEnum):
    """Condition of returned item for inventory restocking or write-off."""

    RESELLABLE = "resellable"
    DAMAGED = "damaged"


class PurchaseReturnStatusEnum(enum.StrEnum):
    """Purchase Return lifecycle status with vendor."""

    REQUESTED = "requested"
    SHIPPED = "shipped"
    CREDITED = "credited"


class SalesReturn(Base):
    """Goods return request from a retailer."""

    __tablename__ = "sales_returns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    retailer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("retailers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[SalesReturnStatusEnum] = mapped_column(
        Enum(SalesReturnStatusEnum, name="sales_return_status_enum", native_enum=False),
        nullable=False,
        default=SalesReturnStatusEnum.REQUESTED,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    sales_order: Mapped["app.models.retailer.SalesOrder"] = relationship("SalesOrder")  # noqa: F821
    retailer: Mapped["app.models.retailer.Retailer"] = relationship("Retailer")  # noqa: F821
    items: Mapped[list["SalesReturnItem"]] = relationship(
        "SalesReturnItem", back_populates="sales_return", cascade="all, delete-orphan"
    )


class SalesReturnItem(Base):
    """Individual line item in a Sales Return."""

    __tablename__ = "sales_return_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sales_returns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    qty: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("stock_batches.id", ondelete="SET NULL"), nullable=True
    )
    condition: Mapped[ReturnItemConditionEnum] = mapped_column(
        Enum(ReturnItemConditionEnum, name="return_item_condition_enum", native_enum=False),
        nullable=False,
        default=ReturnItemConditionEnum.RESELLABLE,
    )

    # Relationships
    sales_return: Mapped["SalesReturn"] = relationship("SalesReturn", back_populates="items")
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821
    batch: Mapped["app.models.warehouse.StockBatch | None"] = relationship(  # noqa: F821
        "StockBatch"
    )


class PurchaseReturn(Base):
    """Goods return request to a supplier/manufacturer."""

    __tablename__ = "purchase_returns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[PurchaseReturnStatusEnum] = mapped_column(
        Enum(PurchaseReturnStatusEnum, name="purchase_return_status_enum", native_enum=False),
        nullable=False,
        default=PurchaseReturnStatusEnum.REQUESTED,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    credit_note_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


    # Relationships
    purchase_order: Mapped["app.models.supplier.PurchaseOrder"] = relationship(  # noqa: F821
        "PurchaseOrder"
    )
    supplier: Mapped["app.models.supplier.Supplier"] = relationship("Supplier")  # noqa: F821
    items: Mapped[list["PurchaseReturnItem"]] = relationship(
        "PurchaseReturnItem", back_populates="purchase_return", cascade="all, delete-orphan"
    )


class PurchaseReturnItem(Base):
    """Individual line item in a Purchase Return."""

    __tablename__ = "purchase_return_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_returns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    qty: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("stock_batches.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    purchase_return: Mapped["PurchaseReturn"] = relationship(
        "PurchaseReturn", back_populates="items"
    )
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821
    batch: Mapped["app.models.warehouse.StockBatch | None"] = relationship(  # noqa: F821
        "StockBatch"
    )
