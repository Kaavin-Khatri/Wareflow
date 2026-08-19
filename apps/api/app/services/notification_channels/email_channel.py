"""Email Notification Channel using Resend API."""

import logging
from typing import Any

from app.services.notification_channels.base import BaseNotificationChannel, NotificationPayload

logger = logging.getLogger(__name__)


class EmailChannel(BaseNotificationChannel):
    """
    Email notification channel powered by Resend.

    Dispatches transactional HTML emails for critical alerts (low-stock, FSSAI expiry,
    delivery failures, order status updates). Gracefully simulates when API key is unconfigured.
    """

    def __init__(
        self,
        api_key: str | None = None,
        from_email: str = "WareFlow Alerts <alerts@wareflow.io>",
        resend_client: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.from_email = from_email
        self._resend_client = resend_client

    @property
    def channel_name(self) -> str:
        return "email"

    def send(self, payload: NotificationPayload) -> bool:
        """Send email alert via Resend API or simulate in development/test."""
        recipient = payload.recipient_email
        if not recipient:
            logger.info("Skipping email dispatch: No recipient email provided for user %s", payload.user_id)
            return True

        subject = f"[WareFlow] {payload.title}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #E2E8F0; border-radius: 8px;">
            <div style="background-color: #7C3AED; padding: 12px 20px; border-radius: 6px; margin-bottom: 20px;">
                <h2 style="color: #FFFFFF; margin: 0; font-size: 18px;">WareFlow Notification</h2>
            </div>
            <h3 style="color: #0F172A; font-size: 16px; margin-top: 0;">{payload.title}</h3>
            <p style="color: #334155; font-size: 14px; line-height: 1.5;">{payload.body}</p>
            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #E2E8F0; font-size: 12px; color: #64748B;">
                Sent by WareFlow Wholesale ERP &bull; Type: {payload.type}
            </div>
        </div>
        """

        if self.api_key:
            try:
                import resend

                resend.api_key = self.api_key
                resend.Emails.send({
                    "from": self.from_email,
                    "to": [recipient],
                    "subject": subject,
                    "html": html_content,
                })
                logger.info("Dispatched Resend email to %s: %s", recipient, payload.title)
                return True
            except Exception as exc:
                logger.error("Failed to send Resend email to %s: %s", recipient, exc)
                return False
        else:
            logger.info(
                "Simulated email dispatch to %s (API key unconfigured): [%s] %s",
                recipient,
                subject,
                payload.body,
            )
            return True
