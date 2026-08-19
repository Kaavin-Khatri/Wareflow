"""In-App Notification Channel writing to Postgres and Firestore for realtime push."""

import logging
import uuid
from typing import Any

from app.models.notification import Notification
from app.repositories.interfaces.notification_repository import NotificationRepositoryInterface
from app.services.notification_channels.base import BaseNotificationChannel, NotificationPayload

logger = logging.getLogger(__name__)


class InAppChannel(BaseNotificationChannel):
    """
    In-App notification channel.

    Writes to:
    1. PostgreSQL `notifications` table: System of record for paginated history and read tracking.
    2. Firestore `notifications/{user_id}/items/{id}`: Realtime push for instant Topbar bell updates.
    """

    def __init__(
        self,
        notification_repo: NotificationRepositoryInterface,
        firestore_client: Any | None = None,
    ) -> None:
        self.notification_repo = notification_repo
        self._firestore_client = firestore_client

    @property
    def channel_name(self) -> str:
        return "in_app"

    def _get_firestore_client(self) -> Any | None:
        """Lazily initialize or return Firestore client instance."""
        if self._firestore_client is not None:
            return self._firestore_client
        try:
            import firebase_admin
            from firebase_admin import firestore

            if firebase_admin._apps:
                return firestore.client()
        except Exception as exc:
            logger.debug("Firestore client not available: %s", exc)
        return None

    def _write_to_firestore(self, payload: NotificationPayload) -> None:
        """Write lightweight real-time document to Firestore."""
        client = self._get_firestore_client()
        if client is None:
            return

        try:
            doc_ref = (
                client.collection("notifications")
                .document(payload.user_id)
                .collection("items")
                .document(payload.id)
            )
            doc_ref.set({
                "id": payload.id,
                "user_id": payload.user_id,
                "type": payload.type,
                "title": payload.title,
                "body": payload.body,
                "is_read": False,
                "metadata": payload.metadata,
                "created_at": payload.created_at.isoformat(),
            })
            logger.debug("Pushed realtime notification to Firestore: doc=%s", payload.id)
        except Exception as exc:
            logger.warning("Failed to write notification to Firestore realtime mirror: %s", exc)

    def send(self, payload: NotificationPayload) -> bool:
        """Persist to PostgreSQL system of record and mirror to Firestore."""
        if not payload.id:
            payload.id = str(uuid.uuid4())

        try:
            notification = Notification(
                id=payload.id,
                user_id=payload.user_id,
                type=payload.type,
                title=payload.title,
                body=payload.body,
                is_read=False,
                created_at=payload.created_at,
            )
            self.notification_repo.create(notification)

            # Mirror to Firestore for real-time Topbar listener
            self._write_to_firestore(payload)
            return True
        except Exception as exc:
            logger.error("Failed to persist in-app notification: %s", exc)
            return False
