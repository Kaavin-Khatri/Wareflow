"""SQLAlchemy implementation of the AuditRepository."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.audit_and_settings import AdminAuditLog
from app.repositories.interfaces.audit_repository import AuditRepository


class SqlAlchemyAuditRepository(AuditRepository):
    """Concrete repository persisting and querying AdminAuditLog records via SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_log(
        self,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        before_value: dict[str, Any] | None = None,
        after_value: dict[str, Any] | None = None,
    ) -> AdminAuditLog:
        """Persist an immutable audit record to the database."""
        entry = AdminAuditLog(
            id=str(uuid.uuid4()),
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_value=before_value,
            after_value=after_value,
        )
        self._session.add(entry)
        self._session.commit()
        self._session.refresh(entry)
        return entry

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
        stmt = select(AdminAuditLog)
        count_stmt = select(func.count(AdminAuditLog.id))

        if entity_type:
            stmt = stmt.where(AdminAuditLog.entity_type == entity_type)
            count_stmt = count_stmt.where(AdminAuditLog.entity_type == entity_type)

        if actor_id:
            stmt = stmt.where(AdminAuditLog.actor_id == actor_id)
            count_stmt = count_stmt.where(AdminAuditLog.actor_id == actor_id)

        if action:
            stmt = stmt.where(AdminAuditLog.action == action)
            count_stmt = count_stmt.where(AdminAuditLog.action == action)

        if start_date:
            stmt = stmt.where(AdminAuditLog.created_at >= start_date)
            count_stmt = count_stmt.where(AdminAuditLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(AdminAuditLog.created_at <= end_date)
            count_stmt = count_stmt.where(AdminAuditLog.created_at <= end_date)

        total = self._session.scalar(count_stmt) or 0
        items = list(
            self._session.scalars(
                stmt.order_by(desc(AdminAuditLog.created_at)).offset(skip).limit(limit)
            ).all()
        )

        return items, total


class InMemoryAuditRepository(AuditRepository):
    """In-memory implementation of AuditRepository for unit tests."""

    def __init__(self) -> None:
        self.logs: list[AdminAuditLog] = []

    def create_log(
        self,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        before_value: dict[str, Any] | None = None,
        after_value: dict[str, Any] | None = None,
    ) -> AdminAuditLog:
        entry = AdminAuditLog(
            id=str(uuid.uuid4()),
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_value=before_value,
            after_value=after_value,
        )
        self.logs.append(entry)
        return entry

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
        filtered = list(self.logs)
        if entity_type:
            filtered = [log for log in filtered if log.entity_type == entity_type]
        if actor_id:
            filtered = [log for log in filtered if log.actor_id == actor_id]
        if action:
            filtered = [log for log in filtered if log.action == action]
        if start_date:
            filtered = [log for log in filtered if log.created_at and log.created_at >= start_date]
        if end_date:
            filtered = [log for log in filtered if log.created_at and log.created_at <= end_date]

        total = len(filtered)
        paged = filtered[skip : skip + limit]
        return paged, total

