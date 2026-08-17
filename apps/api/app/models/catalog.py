"""Catalog models: Category and Product."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Category(Base):
    """Product hierarchical category."""

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side=[id], backref="children"
    )


class Product(Base):
    """Core product entity for wholesale catalog and inventory tracking."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hsn_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    base_uom_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("units_of_measure.id", ondelete="SET NULL"), nullable=True
    )
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cost_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    wholesale_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    reorder_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    category: Mapped["Category | None"] = relationship("Category")
    base_uom: Mapped["app.models.uom.UnitOfMeasure | None"] = relationship(  # noqa: F821
        "UnitOfMeasure"
    )
