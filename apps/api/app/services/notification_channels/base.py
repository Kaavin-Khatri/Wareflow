"""Base interface and payload dataclass for Notification Channels (Strategy Pattern)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class NotificationPayload:
    """Standardized notification message payload dispatched across channels."""

    user_id: str
    type: str
    title: str
    body: str
    id: str | None = None
    recipient_email: str | None = None
    recipient_phone: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class BaseNotificationChannel(ABC):
    """Abstract Strategy interface for all notification delivery channels."""

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Unique identifier of the channel (e.g., 'in_app', 'email', 'sms')."""
        ...

    @abstractmethod
    def send(self, payload: NotificationPayload) -> bool:
        """
        Deliver the notification payload through this channel.

        Returns:
            bool: True if delivery succeeded, False otherwise.
        """
        ...
