"""Notification repository protocol."""

from typing import Protocol, runtime_checkable

from app.models.notification import Notification


@runtime_checkable
class NotificationRepositoryInterface(Protocol):
    """Protocol contract for notification persistence (DIP)."""

    def create(self, notification: Notification) -> Notification:
        """Persist a new notification record."""
        ...

    def list_for_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        """List notifications for a user."""
        ...

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        ...
