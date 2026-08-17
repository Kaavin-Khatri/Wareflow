"""Audit repository interface definition."""

from datetime import datetime
from typing import Any, Protocol

from app.models.audit_and_settings import AdminAuditLog


class AuditRepository(Protocol):
    """Data access contract for general administrator audit logging."""

    def create_log(
        self,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        before_value: dict[str, Any] | None = None,
        after_value: dict[str, Any] | None = None,
    ) -> AdminAuditLog:
        """Persist an immutable audit log record."""
        ...

    def list_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        entity_type: str | None = None,
        actor_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        action: str | None = None,
    ) -> tuple[list[AdminAuditLog], int]:
        """Fetch filtered and paginated audit records with total count."""
        ...
