"""Pydantic schemas for Profile and Authentication responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileBootstrapRequest(BaseModel):
    """Optional metadata payload when bootstrapping a new profile."""

    display_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None


class AppearancePreferencesRequest(BaseModel):
    """User request payload to update appearance theme mode and accent color."""

    theme_preference: str = "system"  # 'light' | 'dark' | 'system'
    accent_color: str = (
        "violet"  # 'violet' | 'indigo' | 'emerald' | 'cyan' | 'rose' | 'amber' | 'cobalt'
    )


class ProfileResponse(BaseModel):
    """Authenticated user profile with role and resolved permissions list."""

    id: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    role_id: str
    role_name: str
    permissions: list[str]
    is_active: bool
    theme_preference: str = "system"
    accent_color: str = "violet"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
