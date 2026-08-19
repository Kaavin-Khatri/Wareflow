"""Notification repository protocol contract (DIP)."""

from typing import Protocol, runtime_checkable

from app.models.notification import Notification


@runtime_checkable
class NotificationRepositoryInterface(Protocol):
    """Protocol contract for notification persistence (DIP)."""

    def create(self, notification: Notification) -> Notification:
        """Persist a new notification record."""
        ...

    def get_by_id(self, notification_id: str) -> Notification | None:
        """Retrieve a notification by primary key ID."""
        ...

    def list_for_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        """List all notifications for a user."""
        ...

    def list_for_user_paginated(
        self, user_id: str, unread_only: bool = False, skip: int = 0, limit: int = 20
    ) -> tuple[list[Notification], int]:
        """List paginated notifications for a user, returning items and total count."""
        ...

    def count_unread(self, user_id: str) -> int:
        """Get the count of unread notifications for a user."""
        ...

    def mark_as_read(self, notification_id: str, user_id: str | None = None) -> bool:
        """Mark a specific notification as read."""
        ...

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all unread notifications for a user as read, returning count updated."""
        ...
