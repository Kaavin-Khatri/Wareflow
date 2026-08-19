"""Notification repository implementation."""

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

    def list_for_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        """List notifications for a user."""
        query = self._session.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        return query.order_by(Notification.created_at.desc()).all()

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        notif = self._session.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            return False
        notif.is_read = True
        self._session.flush()
        return True


class InMemoryNotificationRepository(NotificationRepositoryInterface):
    """In-memory implementation for unit testing."""

    def __init__(self) -> None:
        self._notifications: list[Notification] = []

    def create(self, notification: Notification) -> Notification:
        """Persist a new notification record."""
        if not notification.id:
            import uuid
            notification.id = str(uuid.uuid4())
        if not getattr(notification, "created_at", None):
            from datetime import datetime, timezone
            notification.created_at = datetime.now(timezone.utc)
        self._notifications.append(notification)
        return notification

    def list_for_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        """List notifications for a user."""
        res = [n for n in self._notifications if n.user_id == user_id]
        if unread_only:
            res = [n for n in res if not n.is_read]
        return sorted(res, key=lambda n: n.created_at, reverse=True)

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        for n in self._notifications:
            if n.id == notification_id:
                n.is_read = True
                return True
        return False
