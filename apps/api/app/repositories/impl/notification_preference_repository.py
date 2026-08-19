"""Notification preference repository implementations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import NotificationPreference


class SqlAlchemyNotificationPreferenceRepository:
    """Database-backed repository for notification channel preferences."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_entity(self, entity_type: str, entity_id: str) -> NotificationPreference | None:
        """Fetch preference record by entity type and ID."""
        return self._session.execute(
            select(NotificationPreference).where(
                NotificationPreference.entity_type == entity_type,
                NotificationPreference.entity_id == entity_id,
            )
        ).scalar_one_or_none()

    def save_or_update(self, preference: NotificationPreference) -> NotificationPreference:
        """Persist or update preference record in database."""
        existing = self.get_by_entity(preference.entity_type, preference.entity_id)
        if existing:
            existing.in_app_enabled = preference.in_app_enabled
            existing.email_enabled = preference.email_enabled
            existing.whatsapp_enabled = preference.whatsapp_enabled
            existing.sms_enabled = preference.sms_enabled
            existing.critical_stock_sms = preference.critical_stock_sms
            existing.order_updates_sms = preference.order_updates_sms
            existing.dispatch_ready_sms = preference.dispatch_ready_sms
            self._session.commit()
            self._session.refresh(existing)
            return existing

        self._session.add(preference)
        self._session.commit()
        self._session.refresh(preference)
        return preference

    def is_channel_enabled(
        self, entity_id: str, channel: str, alert_type: str | None = None
    ) -> bool:
        """Check if delivery channel is opted-in for the entity."""
        pref = self._session.execute(
            select(NotificationPreference).where(NotificationPreference.entity_id == entity_id)
        ).scalar_one_or_none()

        if not pref:
            # Default policy: In-app, email, and WhatsApp are opt-out; SMS is STRICT OPT-IN
            return channel != "sms"

        if channel == "sms":
            if not pref.sms_enabled:
                return False
            if alert_type and "stock" in alert_type:
                return pref.critical_stock_sms
            if alert_type and "order" in alert_type:
                return pref.order_updates_sms
            if alert_type and ("dispatch" in alert_type or "ready" in alert_type):
                return pref.dispatch_ready_sms
            return True

        if channel == "email":
            return pref.email_enabled
        if channel == "whatsapp":
            return pref.whatsapp_enabled
        return pref.in_app_enabled


class InMemoryNotificationPreferenceRepository:
    """In-memory mock repository for notification preference unit testing."""

    def __init__(self, initial_preferences: list[NotificationPreference] | None = None) -> None:
        self._prefs: dict[str, NotificationPreference] = {}
        if initial_preferences:
            for p in initial_preferences:
                key = f"{p.entity_type}:{p.entity_id}"
                self._prefs[key] = p

    def get_by_entity(self, entity_type: str, entity_id: str) -> NotificationPreference | None:
        key = f"{entity_type}:{entity_id}"
        return self._prefs.get(key)

    def save_or_update(self, preference: NotificationPreference) -> NotificationPreference:
        key = f"{preference.entity_type}:{preference.entity_id}"
        self._prefs[key] = preference
        return preference

    def is_channel_enabled(
        self, entity_id: str, channel: str, alert_type: str | None = None
    ) -> bool:
        pref = None
        for p in self._prefs.values():
            if p.entity_id == entity_id:
                pref = p
                break

        if not pref:
            return channel != "sms"

        if channel == "sms":
            if not pref.sms_enabled:
                return False
            if alert_type and "stock" in alert_type:
                return pref.critical_stock_sms
            if alert_type and "order" in alert_type:
                return pref.order_updates_sms
            if alert_type and ("dispatch" in alert_type or "ready" in alert_type):
                return pref.dispatch_ready_sms
            return True

        if channel == "email":
            return pref.email_enabled
        if channel == "whatsapp":
            return pref.whatsapp_enabled
        return pref.in_app_enabled
