"""Notification Preference domain service managing user & retailer channel opt-in."""

import logging
import uuid

from app.models.notification import NotificationPreference
from app.repositories.interfaces.notification_preference_repository import (
    NotificationPreferenceRepositoryInterface,
)
from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
)

logger = logging.getLogger(__name__)


class NotificationPreferenceService:
    """Domain service for managing opt-in delivery channels and alert categories."""

    def __init__(self, pref_repo: NotificationPreferenceRepositoryInterface) -> None:
        self._pref_repo = pref_repo

    def get_preferences(self, entity_type: str, entity_id: str) -> NotificationPreferenceResponse:
        """Fetch active preferences or return default policy."""
        pref = self._pref_repo.get_by_entity(entity_type, entity_id)
        if not pref:
            return NotificationPreferenceResponse(
                entity_type=entity_type,
                entity_id=entity_id,
                in_app_enabled=True,
                email_enabled=True,
                whatsapp_enabled=True,
                sms_enabled=False,
                critical_stock_sms=False,
                order_updates_sms=False,
                dispatch_ready_sms=False,
            )
        return NotificationPreferenceResponse.model_validate(pref)

    def update_preferences(
        self,
        entity_type: str,
        entity_id: str,
        payload: NotificationPreferenceUpdateRequest,
    ) -> NotificationPreferenceResponse:
        """Upsert notification preferences for the entity."""
        existing = self._pref_repo.get_by_entity(entity_type, entity_id)
        if not existing:
            existing = NotificationPreference(
                id=str(uuid.uuid4()),
                entity_type=entity_type,
                entity_id=entity_id,
                in_app_enabled=payload.in_app_enabled if payload.in_app_enabled is not None else True,
                email_enabled=payload.email_enabled if payload.email_enabled is not None else True,
                whatsapp_enabled=payload.whatsapp_enabled if payload.whatsapp_enabled is not None else True,
                sms_enabled=payload.sms_enabled if payload.sms_enabled is not None else False,
                critical_stock_sms=payload.critical_stock_sms if payload.critical_stock_sms is not None else False,
                order_updates_sms=payload.order_updates_sms if payload.order_updates_sms is not None else False,
                dispatch_ready_sms=payload.dispatch_ready_sms if payload.dispatch_ready_sms is not None else False,
            )
        else:
            self._apply_updates(existing, payload)

        saved = self._pref_repo.save_or_update(existing)
        return NotificationPreferenceResponse.model_validate(saved)

    def _apply_updates(
        self, existing: NotificationPreference, payload: NotificationPreferenceUpdateRequest
    ) -> None:
        """Apply patch changes to existing entity."""
        if payload.in_app_enabled is not None:
            existing.in_app_enabled = payload.in_app_enabled
        if payload.email_enabled is not None:
            existing.email_enabled = payload.email_enabled
        if payload.whatsapp_enabled is not None:
            existing.whatsapp_enabled = payload.whatsapp_enabled
        if payload.sms_enabled is not None:
            existing.sms_enabled = payload.sms_enabled
        if payload.critical_stock_sms is not None:
            existing.critical_stock_sms = payload.critical_stock_sms
        if payload.order_updates_sms is not None:
            existing.order_updates_sms = payload.order_updates_sms
        if payload.dispatch_ready_sms is not None:
            existing.dispatch_ready_sms = payload.dispatch_ready_sms

    def is_channel_enabled(
        self, entity_id: str, channel: str, alert_type: str | None = None
    ) -> bool:
        """Check if delivery channel is opted-in for a given entity."""
        return self._pref_repo.is_channel_enabled(entity_id, channel, alert_type)
