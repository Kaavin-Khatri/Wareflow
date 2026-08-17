"""Pydantic schemas for the administrator audit log."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogEntryResponse(BaseModel):
    """Schema representing an individual human-readable audit entry."""

    id: str
    actor_id: str | None = None
    actor_email: str | None = None
    actor_name: str | None = None
    action: str
    entity_type: str
    entity_id: str
    description: str
    before_value: dict[str, Any] | None = None
    after_value: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Paginated list response for audit log entries."""

    items: list[AuditLogEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
