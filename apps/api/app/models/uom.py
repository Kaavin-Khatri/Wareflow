"""Units of Measure and conversion models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UnitOfMeasure(Base):
    """Unit of measure (e.g., Piece, Box, Case, Kilogram)."""

    __tablename__ = "units_of_measure"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProductUOMConversion(Base):
    """Conversion factor between UOMs for a specific product (e.g. 1 Case = 24 Pieces)."""

    __tablename__ = "product_uom_conversions"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "from_uom_id",
            "to_uom_id",
            name="uq_product_uom_conversion",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    from_uom_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("units_of_measure.id"), nullable=False
    )
    to_uom_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("units_of_measure.id"), nullable=False
    )
    factor: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    from_uom: Mapped["UnitOfMeasure"] = relationship("UnitOfMeasure", foreign_keys=[from_uom_id])
    to_uom: Mapped["UnitOfMeasure"] = relationship("UnitOfMeasure", foreign_keys=[to_uom_id])
