"""
Notification delivery service.

Provides centralized in-app and simulated multi-channel (email/WhatsApp) alert
delivery for system events (FSSAI licenses, stock alerts, inquiry responses).
"""

import logging
from datetime import datetime, timezone

from app.models.notification import Notification
from app.repositories.interfaces.notification_repository import NotificationRepositoryInterface
from app.repositories.interfaces.retailer_user_repository import RetailerUserRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Centralized notification dispatch and logging service."""

    def __init__(
        self,
        notification_repo: NotificationRepositoryInterface,
        retailer_user_repo: RetailerUserRepository | None = None,
    ) -> None:
        self._notif_repo = notification_repo
        self._retailer_user_repo = retailer_user_repo

    def send_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
    ) -> Notification:
        """Create an in-app notification and emit simulated channel log."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            created_at=datetime.now(timezone.utc),
        )
        saved = self._notif_repo.create(notification)
        logger.info(
            "Dispatched notification id=%s to user=%s: [%s] %s",
            saved.id,
            user_id,
            title,
            body,
        )
        return saved

    def notify_retailer_inquiry_responded(
        self,
        retailer_id: str,
        product_name: str,
        response_text: str,
    ) -> list[Notification]:
        """Dispatch notification to retailer users when staff responds to an inquiry."""
        notifications: list[Notification] = []
        user_ids = [retailer_id]

        if self._retailer_user_repo:
            users = self._retailer_user_repo.get_users_by_retailer_id(retailer_id)
            if users:
                user_ids = [u.id for u in users]

        title = f"Inquiry Answered: {product_name}"
        body = f"Staff responded to your question about '{product_name}': {response_text}"

        for uid in user_ids:
            notif = self.send_notification(
                user_id=uid,
                type="inquiry_response",
                title=title,
                body=body,
            )
            notifications.append(notif)

        return notifications
