"""User profile model bound to Firebase Authentication UID."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Profile(Base):
    """
    Staff / Admin User profile tied to Firebase Auth UID.

    Holds the role assignment, user status, and display metadata.
    """

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # Firebase UID
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    totp_secret_encrypted: Mapped[str | None] = mapped_column(String(500), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    backup_codes_encrypted: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    totp_enrolled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    theme_preference: Mapped[str] = mapped_column(
        String(20), nullable=False, default="system", server_default="system"
    )
    accent_color: Mapped[str] = mapped_column(
        String(30), nullable=False, default="violet", server_default="violet"
    )

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
    role: Mapped["app.models.auth_rbac.Role"] = relationship("Role")  # noqa: F821
