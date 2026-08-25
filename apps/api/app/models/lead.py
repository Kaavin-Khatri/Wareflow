"""Lead discovery and scan tracking models for Google Places lead scanner."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LeadCategoryEnum(enum.StrEnum):
    """Category classification for discovered retail leads."""

    GRUH_UDYOG = "gruh_udyog"
    SNACK_STORE = "snack_store"
    GROCERY_KIRANA = "grocery_kirana"
    OTHER = "other"


class Lead(Base):
    """A retail shop lead discovered via Google Places API scanning."""

    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_place_id", "place_id", unique=True),
        Index("ix_leads_category", "category"),
        Index("ix_leads_is_new", "is_new"),
        Index("ix_leads_first_seen_at", "first_seen_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    place_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[LeadCategoryEnum] = mapped_column(
        Enum(LeadCategoryEnum, name="lead_category_enum", native_enum=False),
        nullable=False,
        default=LeadCategoryEnum.OTHER,
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_new: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    contacted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contact_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    converted_retailer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("retailers.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    converted_retailer: Mapped["app.models.retailer.Retailer"] = relationship(  # noqa: F821
        "Retailer", lazy="select"
    )

    def __init__(
        self,
        id: str | None = None,
        place_id: str | None = None,
        name: str | None = None,
        category: LeadCategoryEnum = LeadCategoryEnum.OTHER,
        address: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        phone: str | None = None,
        google_maps_url: str | None = None,
        first_seen_at: datetime | None = None,
        is_new: bool = True,
        contacted: bool = False,
        contact_notes: str | None = None,
        converted_retailer_id: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            id=id or str(uuid.uuid4()),
            place_id=place_id,
            name=name,
            category=category,
            address=address,
            lat=lat,
            lng=lng,
            phone=phone,
            google_maps_url=google_maps_url,
            first_seen_at=first_seen_at or datetime.now(),
            is_new=is_new,
            contacted=contacted,
            contact_notes=contact_notes,
            converted_retailer_id=converted_retailer_id,
            **kwargs,
        )


class LeadScanRun(Base):
    """Audit log of each lead scan execution."""

    __tablename__ = "lead_scan_runs"
    __table_args__ = (Index("ix_lead_scan_runs_run_at", "run_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    center_lat: Mapped[float] = mapped_column(Float, nullable=False)
    center_lng: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[int] = mapped_column(Integer, nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __init__(
        self,
        id: str | None = None,
        run_at: datetime | None = None,
        center_lat: float = 0.0,
        center_lng: float = 0.0,
        radius_m: int = 15000,
        results_count: int = 0,
        new_count: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            id=id or str(uuid.uuid4()),
            run_at=run_at or datetime.now(),
            center_lat=center_lat,
            center_lng=center_lng,
            radius_m=radius_m,
            results_count=results_count,
            new_count=new_count,
            **kwargs,
        )
