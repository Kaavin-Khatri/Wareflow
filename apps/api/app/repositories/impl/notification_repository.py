"""Notification repository implementation."""

from datetime import UTC, datetime
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.interfaces.notification_repository import NotificationRepositoryInterface


class NotificationRepository(NotificationRepositoryInterface):
    """SQLAlchemy implementation of notification repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, notification: Notification) -> Notification:
        """Persist a new notification record."""
        self._session.add(notification)
        self._session.flush()
        self._session.refresh(notification)
        return notification

    def get_by_id(self, notification_id: str) -> Notification | None:
        """Retrieve a notification by ID."""
        return self._session.query(Notification).filter(Notification.id == notification_id).first()

    def list_for_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        """List notifications for a user."""
        query = self._session.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        return query.order_by(Notification.created_at.desc()).all()

    def list_for_user_paginated(
        self, user_id: str, unread_only: bool = False, skip: int = 0, limit: int = 20
    ) -> tuple[list[Notification], int]:
        """List paginated notifications for a user, returning (items, total_count)."""
        base_query = self._session.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            base_query = base_query.filter(Notification.is_read.is_(False))

        total_count = base_query.count()
        items = (
            base_query.order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total_count

    def count_unread(self, user_id: str) -> int:
        """Get the total count of unread notifications for a user."""
        return (
            self._session.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .scalar()
            or 0
        )

    def mark_as_read(self, notification_id: str, user_id: str | None = None) -> bool:
        """Mark a notification as read."""
        query = self._session.query(Notification).filter(Notification.id == notification_id)
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        notif = query.first()
        if not notif:
            return False
        notif.is_read = True
        self._session.flush()
        return True

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all unread notifications for a user as read."""
        unread_notifs = (
            self._session.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .all()
        )
        count = 0
        for n in unread_notifs:
            n.is_read = True
            count += 1
        self._session.flush()
        return count


class InMemoryNotificationRepository(NotificationRepositoryInterface):
    """In-memory implementation for unit testing."""

    def __init__(self) -> None:
        self._notifications: list[Notification] = []

    def create(self, notification: Notification) -> Notification:
        """Persist a new notification record."""
        if not notification.id:
            notification.id = str(uuid.uuid4())
        if not getattr(notification, "created_at", None):
            notification.created_at = datetime.now(UTC)
        self._notifications.append(notification)
        return notification

    def get_by_id(self, notification_id: str) -> Notification | None:
        """Retrieve a notification by ID."""
        for n in self._notifications:
            if n.id == notification_id:
                return n
        return None

    def list_for_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        """List notifications for a user."""
        res = [n for n in self._notifications if n.user_id == user_id]
        if unread_only:
            res = [n for n in res if not n.is_read]
        return sorted(res, key=lambda n: n.created_at, reverse=True)

    def list_for_user_paginated(
        self, user_id: str, unread_only: bool = False, skip: int = 0, limit: int = 20
    ) -> tuple[list[Notification], int]:
        """List paginated notifications for a user."""
        all_items = self.list_for_user(user_id=user_id, unread_only=unread_only)
        total_count = len(all_items)
        return all_items[skip : skip + limit], total_count

    def count_unread(self, user_id: str) -> int:
        """Get the total count of unread notifications for a user."""
        return len([n for n in self._notifications if n.user_id == user_id and not n.is_read])

    def mark_as_read(self, notification_id: str, user_id: str | None = None) -> bool:
        """Mark a notification as read."""
        for n in self._notifications:
            if n.id == notification_id:
                if user_id and n.user_id != user_id:
                    return False
                n.is_read = True
                return True
        return False

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all unread notifications for a user as read."""
        count = 0
        for n in self._notifications:
            if n.user_id == user_id and not n.is_read:
                n.is_read = True
                count += 1
        return count
