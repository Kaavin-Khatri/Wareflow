"""Stock movement append-only ledger model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StockMovementTypeEnum(enum.StrEnum):
    """Types of stock movements recorded in the ledger."""

    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RETURN_IN = "return_in"
    RETURN_OUT = "return_out"


class StockMovement(Base):
    """
    Append-only inventory movement ledger.

    Every inventory change (receiving, sales shipment, shrinkage adjustment,
    inter-warehouse transfer, customer return, vendor return) writes an immutable
    record here. On-hand quantity is the aggregated sum of movements.
    """

    __tablename__ = "stock_movements"
    __table_args__ = (Index("ix_stock_movements_created_at", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("stock_batches.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[StockMovementTypeEnum] = mapped_column(
        Enum(StockMovementTypeEnum, name="stock_movement_type_enum", native_enum=False),
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["app.models.catalog.Product"] = relationship("Product")  # noqa: F821
    warehouse: Mapped["app.models.warehouse.Warehouse"] = relationship("Warehouse")  # noqa: F821
    batch: Mapped["app.models.warehouse.StockBatch | None"] = relationship(  # noqa: F821
        "StockBatch"
    )
