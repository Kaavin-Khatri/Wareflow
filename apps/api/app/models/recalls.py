"""Batch recall and defect traceability models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecallSeverityEnum(enum.StrEnum):
    """Severity classification of product batch recall."""

    LOW = "low"
    MEDIUM = "medium"
    CRITICAL = "critical"


class RecallStatusEnum(enum.StrEnum):
    """Batch recall lifecycle status."""

    INITIATED = "initiated"
    NOTIFYING = "notifying"
    RESOLVED = "resolved"


class BatchRecall(Base):
    """Product batch recall record for quality and safety compliance."""

    __tablename__ = "batch_recalls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stock_batches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[RecallSeverityEnum] = mapped_column(
        Enum(RecallSeverityEnum, name="recall_severity_enum", native_enum=False),
        nullable=False,
        default=RecallSeverityEnum.MEDIUM,
    )
    status: Mapped[RecallStatusEnum] = mapped_column(
        Enum(RecallStatusEnum, name="recall_status_enum", native_enum=False),
        nullable=False,
        default=RecallStatusEnum.INITIATED,
    )
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    batch: Mapped["app.models.warehouse.StockBatch"] = relationship("StockBatch")  # noqa: F821
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821
    affected_orders: Mapped[list["RecallAffectedOrder"]] = relationship(
        "RecallAffectedOrder", back_populates="recall", cascade="all, delete-orphan"
    )


class RecallAffectedOrder(Base):
    """Traceability mapping of orders and buyers affected by a batch recall."""

    __tablename__ = "recall_affected_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recall_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batch_recalls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    retailer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("retailers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    recall: Mapped["BatchRecall"] = relationship("BatchRecall", back_populates="affected_orders")
    sales_order: Mapped["app.models.retailer.SalesOrder"] = relationship("SalesOrder")  # noqa: F821
    retailer: Mapped["app.models.retailer.Retailer | None"] = relationship("Retailer")  # noqa: F821
    customer: Mapped["app.models.portal.Customer | None"] = relationship("Customer")  # noqa: F821
