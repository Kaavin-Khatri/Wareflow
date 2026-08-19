"""
Notification delivery service adhering to the Strategy Pattern (Open/Closed Principle).

Provides centralized multi-channel notification dispatch (In-App, Email, SMS, WhatsApp)
and paginated notification management.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.models.notification import Notification
from app.repositories.interfaces.notification_repository import NotificationRepositoryInterface
from app.repositories.interfaces.retailer_user_repository import RetailerUserRepository
from app.services.notification_channels.base import BaseNotificationChannel, NotificationPayload
from app.services.notification_channels.in_app_channel import InAppChannel

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Centralized notification dispatch and logging service.

    Strategy Pattern (OCP): Channels can be registered dynamically. New channels
    (such as SMS or WhatsApp) can be plugged in without modifying NotificationService.
    """

    def __init__(
        self,
        notification_repo: NotificationRepositoryInterface,
        channels: list[BaseNotificationChannel] | dict[str, BaseNotificationChannel] | None = None,
        retailer_user_repo: RetailerUserRepository | None = None,
    ) -> None:
        self._notif_repo = notification_repo
        self._retailer_user_repo = retailer_user_repo
        self._channels: dict[str, BaseNotificationChannel] = {}

        if channels:
            if isinstance(channels, dict):
                self._channels = dict(channels)
            else:
                for ch in channels:
                    self.register_channel(ch)
        else:
            # Default to built-in InAppChannel if none explicitly supplied
            in_app = InAppChannel(notification_repo=self._notif_repo)
            self.register_channel(in_app)

    def register_channel(self, channel: BaseNotificationChannel) -> None:
        """Register a new notification delivery channel (Open/Closed Principle)."""
        self._channels[channel.channel_name] = channel
        logger.debug("Registered notification channel: %s", channel.channel_name)

    def get_registered_channels(self) -> list[str]:
        """Return list of currently registered channel names."""
        return list(self._channels.keys())

    def notify(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        channels: list[str] | None = None,
        recipient_email: str | None = None,
        recipient_phone: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, bool]:
        """
        Fan out notification to all requested channels and log delivery outcomes.

        Args:
            user_id: Target recipient user ID.
            type: Notification category / event type.
            title: Notification headline.
            body: Detailed notification message.
            channels: Target channel names (e.g. ['in_app', 'email']). Defaults to ['in_app'].
            recipient_email: Optional email address for email channel.
            recipient_phone: Optional phone number for SMS/WhatsApp channels.
            metadata: Optional contextual metadata dict.

        Returns:
            dict[str, bool]: Mapping of channel name to delivery success status.
        """
        target_channel_names = channels if channels is not None else ["in_app"]
        notif_id = str(uuid.uuid4())
        created_at = datetime.now(UTC)

        payload = NotificationPayload(
            id=notif_id,
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            metadata=metadata or {},
            created_at=created_at,
        )

        delivery_results: dict[str, bool] = {}

        for ch_name in target_channel_names:
            channel = self._channels.get(ch_name)
            if not channel:
                logger.warning(
                    "Requested notification channel '%s' is not registered. Skipping.",
                    ch_name,
                )
                delivery_results[ch_name] = False
                continue

            try:
                success = channel.send(payload)
                delivery_results[ch_name] = success
                if success:
                    logger.info(
                        "Notification id=%s [%s] successfully sent via channel '%s' to user=%s",
                        notif_id,
                        title,
                        ch_name,
                        user_id,
                    )
                else:
                    logger.warning(
                        "Notification id=%s [%s] failed delivery via channel '%s' to user=%s",
                        notif_id,
                        title,
                        ch_name,
                        user_id,
                    )
            except Exception as exc:
                logger.error(
                    "Unexpected error delivering notification id=%s via channel '%s': %s",
                    notif_id,
                    ch_name,
                    exc,
                )
                delivery_results[ch_name] = False

        return delivery_results

    def send_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        channels: list[str] | None = None,
        recipient_email: str | None = None,
    ) -> Notification:
        """
        Legacy-compatible helper creating an in-app notification and returning the persisted model.
        """
        target_channels = channels or ["in_app"]
        self.notify(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            channels=target_channels,
            recipient_email=recipient_email,
        )
        # Fetch or construct the in-app notification model
        notif = self._notif_repo.list_for_user(user_id=user_id, unread_only=False)
        if notif:
            return notif[0]

        # Fallback if in-app wasn't among target channels
        return Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            is_read=False,
            created_at=datetime.now(UTC),
        )

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

    def list_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Notification], int, int]:
        """
        Retrieve paginated notifications for a user.

        Returns:
            tuple[items, total_count, unread_count]
        """
        skip = (page - 1) * limit
        items, total = self._notif_repo.list_for_user_paginated(
            user_id=user_id,
            unread_only=unread_only,
            skip=skip,
            limit=limit,
        )
        unread_count = self._notif_repo.count_unread(user_id=user_id)
        return items, total, unread_count

    def get_unread_count(self, user_id: str) -> int:
        """Get the count of unread notifications for a user."""
        return self._notif_repo.count_unread(user_id=user_id)

    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read for the user."""
        return self._notif_repo.mark_as_read(notification_id=notification_id, user_id=user_id)

    def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all unread notifications as read for the user."""
        return self._notif_repo.mark_all_as_read(user_id=user_id)
