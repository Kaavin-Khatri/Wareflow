"""SMS Notification Channel implementing Strategy pattern for critical text alerts."""

import logging

from app.services.notification_channels.base import BaseNotificationChannel, NotificationPayload
from app.services.sms_client import SmsClient, truncate_sms_text

logger = logging.getLogger(__name__)


class SmsChannel(BaseNotificationChannel):
    """
    SMS Notification Channel for short, urgent alerts (low stock, order confirmed, dispatch ready).

    Adheres to the Strategy Pattern (OCP): integrates seamlessly into NotificationService
    without requiring any modifications to the core dispatch engine.
    Strictly disciplines message length to 160 characters (single-segment SMS).
    """

    def __init__(
        self,
        account_sid: str | None = None,
        auth_token: str | None = None,
        from_number: str | None = None,
        api_key: str | None = None,
        sms_client: SmsClient | None = None,
    ) -> None:
        self.client = sms_client or SmsClient(
            account_sid=account_sid,
            auth_token=auth_token,
            from_number=from_number,
            api_key=api_key,
        )

    @property
    def channel_name(self) -> str:
        return "sms"

    def send(self, payload: NotificationPayload) -> bool:
        """Deliver short-message SMS notification with 160-char discipline."""
        phone = self._resolve_recipient_phone(payload)
        if not phone:
            logger.info("Skipping SMS dispatch: No recipient phone provided for user %s", payload.user_id)
            return True

        message_body = self._format_concise_sms(payload)
        res = self.client.send_sms(to_phone=phone, message=message_body)

        if "error" in res:
            logger.error("Failed to send SMS to %s: %s", phone, res.get("error"))
            return False

        logger.info("Successfully dispatched SMS to %s", phone)
        return True

    def _resolve_recipient_phone(self, payload: NotificationPayload) -> str | None:
        """Resolve recipient phone number from payload fields or metadata."""
        meta = payload.metadata or {}
        return (
            payload.recipient_phone
            or meta.get("phone")
            or meta.get("recipient_phone")
            or meta.get("retailer_phone")
            or meta.get("customer_phone")
            or meta.get("supplier_phone")
        )

    def _format_concise_sms(self, payload: NotificationPayload) -> str:
        """Construct short, high-priority SMS body within 160-character budget."""
        notif_type = (payload.type or "").lower()
        meta = payload.metadata or {}

        # 1. Low stock / stock depletion alerts for owner/managers
        if any(k in notif_type for k in ("stock", "depletion", "reorder", "inventory")):
            prod = str(meta.get("product_name") or meta.get("name") or payload.title)
            qty = str(meta.get("current_stock") or meta.get("quantity") or "0")
            uom = str(meta.get("uom") or meta.get("unit") or "units")
            msg = f"WareFlow Alert: Low stock on {prod} ({qty} {uom} remaining). Reorder needed."
            return truncate_sms_text(msg, 160)

        # 2. Order confirmed alerts for retailers
        if any(k in notif_type for k in ("order_confirmed", "order_placed", "order")):
            so_num = str(meta.get("so_number") or meta.get("order_number") or payload.title)
            amt = str(meta.get("total_amount") or meta.get("amount") or "")
            amt_str = f" for Rs.{amt}" if amt else ""
            msg = f"WareFlow: Order #{so_num} confirmed{amt_str}. Log in to portal to track."
            return truncate_sms_text(msg, 160)

        # 3. Goods ready / PO dispatch alerts
        if any(k in notif_type for k in ("goods_ready", "dispatch", "ready")):
            po_num = str(meta.get("po_number") or meta.get("order_number") or payload.title)
            sup = str(meta.get("supplier_name") or "Supplier")
            msg = f"WareFlow: PO #{po_num} from {sup} is ready for pickup/dispatch."
            return truncate_sms_text(msg, 160)

        # 4. Generic fallback
        fallback = f"WareFlow: {payload.title}. {payload.body}"
        return truncate_sms_text(fallback, 160)
