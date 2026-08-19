"""Alert Log repository implementations (SQLAlchemy and InMemory)."""

from datetime import UTC, datetime, timedelta
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.notification import AlertLog
from app.repositories.interfaces.alert_log_repository import AlertLogRepositoryInterface


class SQLAlchemyAlertLogRepository(AlertLogRepositoryInterface):
    """PostgreSQL / SQLAlchemy implementation of alert deduplication logs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def has_recent_alert(
        self, rule_name: str, entity_type: str, entity_id: str, window_hours: int = 24
    ) -> bool:
        """Check if an alert was already logged within the last window_hours."""
        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
        query = (
            select(func.count(AlertLog.id))
            .where(
                AlertLog.rule_name == rule_name,
                AlertLog.entity_type == entity_type,
                AlertLog.entity_id == str(entity_id),
                AlertLog.created_at >= cutoff,
            )
        )
        count = self.db.execute(query).scalar_one_or_none() or 0
        return count > 0

    def record_alert(self, rule_name: str, entity_type: str, entity_id: str) -> AlertLog:
        """Record an alert firing in PostgreSQL."""
        log = AlertLog(
            id=str(uuid.uuid4()),
            rule_name=rule_name,
            entity_type=entity_type,
            entity_id=str(entity_id),
            created_at=datetime.now(UTC),
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def cleanup_old_logs(self, older_than_days: int = 30) -> int:
        """Delete alert logs older than specified days."""
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        stmt = delete(AlertLog).where(AlertLog.created_at < cutoff)
        res = self.db.execute(stmt)
        self.db.commit()
        return res.rowcount or 0


class InMemoryAlertLogRepository(AlertLogRepositoryInterface):
    """In-memory alert log repository for fast isolated unit testing."""

    def __init__(self) -> None:
        self._logs: list[AlertLog] = []

    def has_recent_alert(
        self, rule_name: str, entity_type: str, entity_id: str, window_hours: int = 24
    ) -> bool:
        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
        for log in self._logs:
            if (
                log.rule_name == rule_name
                and log.entity_type == entity_type
                and log.entity_id == str(entity_id)
            ):
                log_time = log.created_at
                if log_time.tzinfo is None:
                    log_time = log_time.replace(tzinfo=UTC)
                if log_time >= cutoff:
                    return True
        return False

    def record_alert(self, rule_name: str, entity_type: str, entity_id: str) -> AlertLog:
        log = AlertLog(
            id=str(uuid.uuid4()),
            rule_name=rule_name,
            entity_type=entity_type,
            entity_id=str(entity_id),
            created_at=datetime.now(UTC),
        )
        self._logs.append(log)
        return log

    def cleanup_old_logs(self, older_than_days: int = 30) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        initial_len = len(self._logs)
        self._logs = [
            log
            for log in self._logs
            if (log.created_at.replace(tzinfo=UTC) if log.created_at.tzinfo is None else log.created_at)
            >= cutoff
        ]
        return initial_len - len(self._logs)
