"""Alert Log repository interface for deduplication windows."""

from abc import ABC, abstractmethod

from app.models.notification import AlertLog


class AlertLogRepositoryInterface(ABC):
    """Interface for managing alert firing audit logs and deduplication."""

    @abstractmethod
    def has_recent_alert(
        self, rule_name: str, entity_type: str, entity_id: str, window_hours: int = 24
    ) -> bool:
        """Check if an alert was already fired for this rule and entity within window_hours."""
        raise NotImplementedError

    @abstractmethod
    def record_alert(self, rule_name: str, entity_type: str, entity_id: str) -> AlertLog:
        """Record that an alert has been fired."""
        raise NotImplementedError

    @abstractmethod
    def cleanup_old_logs(self, older_than_days: int = 30) -> int:
        """Delete alert logs older than specified days."""
        raise NotImplementedError
