"""SMS Client handling outbound short-message delivery via Twilio/generic SMS gateway."""

import base64
import logging
from typing import Any
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to international E.164 format (defaults to +91 if 10 digits)."""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned.startswith("+"):
        if len(cleaned) == 10:
            cleaned = f"+91{cleaned}"
        else:
            cleaned = f"+{cleaned}"
    return cleaned


def truncate_sms_text(text: str, max_chars: int = 160) -> str:
    """Discipline SMS message length strictly to standard 160-character single segment."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


class SmsClient:
    """Client for dispatching SMS messages via Twilio REST API with graceful degradation."""

    def __init__(
        self,
        account_sid: str | None = None,
        auth_token: str | None = None,
        from_number: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.account_sid = (account_sid or "").strip()
        self.auth_token = (auth_token or "").strip()
        self.from_number = (from_number or "").strip()
        self.api_key = (api_key or "").strip()

    @property
    def is_configured(self) -> bool:
        """Return True if required credentials are present."""
        has_twilio = bool(self.account_sid and self.auth_token and self.from_number)
        has_api_key = bool(self.api_key and self.from_number)
        return has_twilio or has_api_key

    def send_sms(self, to_phone: str, message: str) -> dict[str, Any]:
        """Deliver standard 160-character single-segment SMS message."""
        recipient = normalize_phone_number(to_phone)
        body_text = truncate_sms_text(message, max_chars=160)

        if not self.is_configured:
            logger.info("SMS Client not configured. Simulating SMS to %s: %s", recipient, body_text)
            return {"status": "simulated", "to": recipient, "body": body_text}

        return self._dispatch_twilio_request(recipient, body_text)

    def _dispatch_twilio_request(self, recipient: str, body_text: str) -> dict[str, Any]:
        """Execute HTTP POST request to Twilio Messages endpoint."""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        data = urllib.parse.urlencode({"To": recipient, "From": self.from_number, "Body": body_text}).encode("utf-8")
        auth_header = "Basic " + base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode("utf-8")).decode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", auth_header)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.getcode()
                return {"status": "sent", "code": status_code, "to": recipient, "body": body_text}
        except Exception as exc:
            logger.error("Twilio SMS dispatch failed to %s: %s", recipient, exc)
            return {"error": str(exc), "status": "failed", "to": recipient}
