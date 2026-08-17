"""Delivery dispatch and fulfillment models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DeliveryStatusEnum(enum.StrEnum):
    """Delivery dispatch status."""

    ASSIGNED = "assigned"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"


class Delivery(Base):
    """Logistics dispatch and delivery tracking for sales orders."""

    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    driver_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vehicle_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[DeliveryStatusEnum] = mapped_column(
        Enum(DeliveryStatusEnum, name="delivery_status_enum", native_enum=False),
        nullable=False,
        default=DeliveryStatusEnum.ASSIGNED,
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    sales_order: Mapped["app.models.retailer.SalesOrder"] = relationship("SalesOrder")  # noqa: F821
