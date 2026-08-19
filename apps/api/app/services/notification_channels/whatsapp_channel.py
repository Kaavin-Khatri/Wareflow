"""WhatsApp notification channel implementation using Meta Cloud API."""

import logging
from typing import Any

from app.services.notification_channels.base import BaseNotificationChannel, NotificationPayload
from app.services.whatsapp_client import WhatsAppClient

logger = logging.getLogger(__name__)


class WhatsAppChannel(BaseNotificationChannel):
    """
    WhatsApp notification channel powered by Meta's WhatsApp Business Cloud API.

    Implements Strategy pattern (OCP): maps incoming NotificationPayload events to pre-approved
    Meta Business message templates (e.g. wareflow_stock_available, wareflow_goods_ready).
    Gracefully simulates and no-ops when credentials are not configured.
    """

    STOCK_AVAILABLE_TEMPLATE = "wareflow_stock_available"
    GOODS_READY_TEMPLATE = "wareflow_goods_ready"

    def __init__(
        self,
        access_token: str | None = None,
        phone_number_id: str | None = None,
        api_version: str = "v21.0",
        whatsapp_client: WhatsAppClient | None = None,
    ) -> None:
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.client = whatsapp_client or WhatsAppClient(
            access_token=access_token,
            phone_number_id=phone_number_id,
            api_version=api_version,
        )

    @property
    def channel_name(self) -> str:
        return "whatsapp"

    def send(self, payload: NotificationPayload) -> bool:
        """
        Deliver notification via WhatsApp using pre-approved template message.

        Maps payload.type and metadata to the appropriate template and positional parameters.
        """
        # Resolve recipient phone number
        phone = (
            payload.recipient_phone
            or payload.metadata.get("phone")
            or payload.metadata.get("recipient_phone")
            or payload.metadata.get("customer_phone")
            or payload.metadata.get("retailer_phone")
        )

        if not phone:
            logger.info("Skipping WhatsApp dispatch: No recipient phone number provided for user %s", payload.user_id)
            return True

        if not self.client.is_configured:
            logger.info(
                "WhatsApp channel is not configured (WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID unset). "
                "Simulating WhatsApp message to %s: [%s] %s",
                phone,
                payload.title,
                payload.body,
            )
            return True

        template_name, parameters = self._resolve_template_and_params(payload)

        res = self.client.send_template_message(
            to_phone=phone,
            template_name=template_name,
            parameters=parameters,
        )

        if "error" in res:
            logger.error("Failed to send WhatsApp message to %s: %s", phone, res.get("error"))
            return False

        logger.info("Successfully dispatched WhatsApp template '%s' to %s", template_name, phone)
        return True

    def _resolve_template_and_params(self, payload: NotificationPayload) -> tuple[str, list[str]]:
        """
        Map notification type and metadata to approved template name and ordered parameters.

        Templates:
        1. wareflow_stock_available:
           Parameters: {{1}} Product Name, {{2}} Quantity Available, {{3}} UoM, {{4}} Action / Catalog Link
        2. wareflow_goods_ready:
           Parameters: {{1}} Order/Consignment Number, {{2}} Recipient Name, {{3}} Item/Package Summary, {{4}} Tracking Link
        """
        notif_type = (payload.type or "").lower()
        meta = payload.metadata or {}

        # 1. Back in stock / Restock / Low stock alerts
        if any(keyword in notif_type for keyword in ("stock", "restock", "inventory", "product", "batch")):
            product_name = str(meta.get("product_name") or meta.get("name") or payload.title)
            qty = str(meta.get("current_stock") or meta.get("quantity") or meta.get("suggested_reorder_qty") or "Available")
            uom = str(meta.get("uom") or meta.get("unit") or "units")
            link = str(meta.get("link") or "/portal/catalog")
            return self.STOCK_AVAILABLE_TEMPLATE, [product_name, qty, uom, link]

        # 2. Order Ready / Goods Ready / Dispatch / Delivery updates
        if any(keyword in notif_type for keyword in ("order", "goods", "ready", "dispatch", "delivery", "shipping", "rma")):
            order_number = str(meta.get("order_number") or meta.get("so_number") or meta.get("invoice_number") or meta.get("po_number") or payload.title)
            recipient_name = str(meta.get("retailer_name") or meta.get("customer_name") or meta.get("recipient_name") or "Valued Customer")
            summary = str(meta.get("summary") or meta.get("status") or meta.get("item_count") or (payload.body[:50] if payload.body else "Ready"))
            link = str(meta.get("link") or "/portal/orders")
            return self.GOODS_READY_TEMPLATE, [order_number, recipient_name, summary, link]

        # Default fallback: use stock/update template with title, body snippet, date, link
        title = payload.title or "WareFlow Alert"
        body_snippet = payload.body[:40] if payload.body else "Notification"
        date_str = str(payload.created_at.date() if hasattr(payload.created_at, "date") else "today")
        link = str(meta.get("link") or "/portal")
        return self.STOCK_AVAILABLE_TEMPLATE, [title, body_snippet, date_str, link]
