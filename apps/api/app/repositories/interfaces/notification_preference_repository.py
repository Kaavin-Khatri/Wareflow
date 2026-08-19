"""Notification preference repository interface protocol."""

from typing import Protocol

from app.models.notification import NotificationPreference


class NotificationPreferenceRepositoryInterface(Protocol):
    """Data access contract for user and retailer notification channel preferences."""

    def get_by_entity(self, entity_type: str, entity_id: str) -> NotificationPreference | None:
        """Fetch preference record by entity type ('user' | 'retailer') and ID."""
        ...

    def save_or_update(self, preference: NotificationPreference) -> NotificationPreference:
        """Persist or update preference record in storage."""
        ...

    def is_channel_enabled(
        self, entity_id: str, channel: str, alert_type: str | None = None
    ) -> bool:
        """Determine if a channel is opted in for a given entity and alert category."""
        ...
