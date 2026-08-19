"""Meta WhatsApp Business Cloud API Client."""

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """
    Dedicated client for Meta's WhatsApp Business Cloud API.

    The ONLY place in the codebase where Meta Graph API calls are dispatched.
    Requires pre-approved message templates for business-initiated outbound alerts.
    """

    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        access_token: str | None = None,
        phone_number_id: str | None = None,
        api_version: str = "v21.0",
        http_client: httpx.Client | None = None,
    ) -> None:
        self.access_token = access_token.strip() if access_token else ""
        self.phone_number_id = phone_number_id.strip() if phone_number_id else ""
        self.api_version = api_version.strip() if api_version else "v21.0"
        self._http_client = http_client

    @property
    def is_configured(self) -> bool:
        """Check whether valid credentials are provided."""
        return bool(self.access_token and self.phone_number_id)

    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """
        Normalize phone numbers to international standard without '+', spaces, dashes, or parentheses.

        e.g. '+91 98765-43210' -> '919876543210'
             '9876543210' (10 digits) -> '919876543210'
        """
        cleaned = re.sub(r"[^\d]", "", str(phone or ""))
        # If 10 digits (standard India local mobile), prepend 91 default country code
        if len(cleaned) == 10:
            cleaned = f"91{cleaned}"
        return cleaned

    def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        parameters: list[str] | None = None,
        language_code: str = "en",
    ) -> dict[str, Any]:
        """
        Send a pre-approved template message via Meta Cloud API.

        Args:
            to_phone: Recipient phone number (normalized)
            template_name: Approved template name (e.g. 'wareflow_stock_available', 'wareflow_goods_ready')
            parameters: Ordered positional text parameters for template body variables {{1}}, {{2}}, etc.
            language_code: Template language code (e.g. 'en', 'en_US', 'hi')

        Returns:
            Dict containing Meta API response or structured error object.
        """
        normalized_phone = self.normalize_phone_number(to_phone)
        if not normalized_phone:
            logger.warning("Cannot send WhatsApp template '%s': Empty recipient phone number.", template_name)
            return {"error": "Invalid recipient phone number", "status_code": 400}

        if not self.is_configured:
            logger.info(
                "WhatsApp client is not configured. Simulating template dispatch: to=%s, template=%s, params=%s",
                normalized_phone,
                template_name,
                parameters,
            )
            return {
                "status": "simulated",
                "template": template_name,
                "recipient": normalized_phone,
                "messages": [{"id": f"sim_wamid_{normalized_phone}"}],
            }

        url = f"{self.BASE_URL}/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Format body parameters
        params_list = parameters or []
        body_parameters = [{"type": "text", "text": str(p)} for p in params_list]
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }

        if body_parameters:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": body_parameters,
                }
            ]

        try:
            if self._http_client:
                response = self._http_client.post(url, headers=headers, json=payload, timeout=10.0)
            else:
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(url, headers=headers, json=payload)

            if response.status_code in (200, 201):
                res_data = response.json()
                msg_id = (res_data.get("messages") or [{}])[0].get("id", "unknown")
                logger.info(
                    "WhatsApp template '%s' sent successfully to %s (message_id: %s)",
                    template_name,
                    normalized_phone,
                    msg_id,
                )
                return res_data

            logger.error(
                "WhatsApp Cloud API error [%d] for %s: %s",
                response.status_code,
                normalized_phone,
                response.text,
            )
            return {"error": response.text, "status_code": response.status_code}
        except Exception as exc:
            logger.error("Exception dispatching WhatsApp template to %s: %s", normalized_phone, exc)
            return {"error": str(exc), "status_code": 500}

    def send_text_message(self, to_phone: str, text: str) -> dict[str, Any]:
        """
        Send a freeform text message (within 24-hour service conversation window).

        Args:
            to_phone: Recipient phone number
            text: Message body text
        """
        normalized_phone = self.normalize_phone_number(to_phone)
        if not normalized_phone:
            logger.warning("Cannot send WhatsApp text message: Empty recipient phone number.")
            return {"error": "Invalid recipient phone number", "status_code": 400}

        if not self.is_configured:
            logger.info("WhatsApp client is not configured. Simulating text dispatch to %s: %s", normalized_phone, text)
            return {
                "status": "simulated",
                "recipient": normalized_phone,
                "text": text,
                "messages": [{"id": f"sim_wamid_text_{normalized_phone}"}],
            }

        url = f"{self.BASE_URL}/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_phone,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        try:
            if self._http_client:
                response = self._http_client.post(url, headers=headers, json=payload, timeout=10.0)
            else:
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(url, headers=headers, json=payload)

            if response.status_code in (200, 201):
                res_data = response.json()
                logger.info("WhatsApp text message sent to %s", normalized_phone)
                return res_data

            logger.error("WhatsApp text API error [%d]: %s", response.status_code, response.text)
            return {"error": response.text, "status_code": response.status_code}
        except Exception as exc:
            logger.error("Exception sending WhatsApp text to %s: %s", normalized_phone, exc)
            return {"error": str(exc), "status_code": 500}
