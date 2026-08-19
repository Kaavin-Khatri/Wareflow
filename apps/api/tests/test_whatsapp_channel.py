"""Unit and integration tests for Step 13.3 WhatsApp Notification Channel & Client."""

from typing import Any

import httpx

from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.services.notification_channels.base import NotificationPayload
from app.services.notification_channels.in_app_channel import InAppChannel
from app.services.notification_channels.whatsapp_channel import WhatsAppChannel
from app.services.notification_service import NotificationService
from app.services.whatsapp_client import WhatsAppClient


class MockTransport(httpx.BaseTransport):
    """Mock HTTP transport to simulate Meta WhatsApp Cloud API responses."""

    def __init__(self, status_code: int = 200, json_response: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.json_response = json_response or {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
            "messages": [{"id": "wamid.HBgLMzkxOTg3NjU0MzIxMBUCMRIAFkExQzI4RDkxNEMzMzdCN0RGRTI4AA=="}],
        }
        self.last_request: httpx.Request | None = None
        self.last_json: dict[str, Any] | None = None

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.last_request = request
        import json
        try:
            self.last_json = json.loads(request.content.decode("utf-8"))
        except Exception:
            self.last_json = None
        return httpx.Response(
            status_code=self.status_code,
            json=self.json_response,
            request=request,
        )


def test_whatsapp_phone_number_normalization():
    """Phone numbers are normalized to international standard without '+', spaces, or dashes."""
    assert WhatsAppClient.normalize_phone_number("+91 98765-43210") == "919876543210"
    assert WhatsAppClient.normalize_phone_number("9876543210") == "919876543210"  # 10-digit India fallback
    assert WhatsAppClient.normalize_phone_number("+1 (555) 234-5678") == "15552345678"
    assert WhatsAppClient.normalize_phone_number("91-9876543210") == "919876543210"


def test_whatsapp_client_send_template_success():
    """WhatsAppClient properly formats Meta Graph API template request and parses message ID."""
    mock_transport = MockTransport(status_code=200)
    mock_http = httpx.Client(transport=mock_transport)

    client = WhatsAppClient(
        access_token="test_meta_token_xyz",
        phone_number_id="10029384756",
        api_version="v21.0",
        http_client=mock_http,
    )

    res = client.send_template_message(
        to_phone="+91 98765 43210",
        template_name="wareflow_stock_available",
        parameters=["Basmati Rice 25kg", "250", "bags", "https://wareflow.io/portal/catalog"],
    )

    assert "messages" in res
    assert res["messages"][0]["id"].startswith("wamid.")

    # Validate outgoing HTTP request payload structure
    req_json = mock_transport.last_json
    assert req_json is not None
    assert req_json["messaging_product"] == "whatsapp"
    assert req_json["to"] == "919876543210"
    assert req_json["type"] == "template"
    assert req_json["template"]["name"] == "wareflow_stock_available"
    assert len(req_json["template"]["components"][0]["parameters"]) == 4
    assert req_json["template"]["components"][0]["parameters"][0]["text"] == "Basmati Rice 25kg"
    assert req_json["template"]["components"][0]["parameters"][1]["text"] == "250"


def test_whatsapp_client_handles_meta_api_errors():
    """WhatsAppClient gracefully handles HTTP 400/401 errors from Meta Graph API."""
    mock_transport = MockTransport(
        status_code=400,
        json_response={"error": {"message": "(#100) Invalid parameter", "type": "OAuthException", "code": 100}},
    )
    mock_http = httpx.Client(transport=mock_transport)

    client = WhatsAppClient(
        access_token="invalid_token",
        phone_number_id="10029384756",
        http_client=mock_http,
    )

    res = client.send_template_message(
        to_phone="919876543210",
        template_name="wareflow_stock_available",
        parameters=["Test Product"],
    )

    assert "error" in res
    assert res["status_code"] == 400


def test_whatsapp_channel_maps_stock_available_template():
    """WhatsAppChannel maps stock/restock notifications to wareflow_stock_available template."""
    mock_transport = MockTransport(status_code=200)
    mock_http = httpx.Client(transport=mock_transport)
    client = WhatsAppClient(access_token="tok", phone_number_id="123", http_client=mock_http)
    channel = WhatsAppChannel(whatsapp_client=client)

    payload = NotificationPayload(
        user_id="usr-ret-1",
        type="stock_available",
        title="Item Back in Stock: Organic Moong Dal",
        body="Organic Moong Dal 1kg is replenished and available for wholesale dispatch.",
        recipient_phone="+91 98765 11111",
        metadata={
            "product_name": "Organic Moong Dal 1kg",
            "current_stock": 500,
            "uom": "kg",
            "link": "/portal/catalog/prod-moong-1",
        },
    )

    success = channel.send(payload)
    assert success is True

    req_json = mock_transport.last_json
    assert req_json is not None
    assert req_json["template"]["name"] == "wareflow_stock_available"
    assert req_json["to"] == "919876543210" or req_json["to"] == "919876511111"
    params = [p["text"] for p in req_json["template"]["components"][0]["parameters"]]
    assert params == ["Organic Moong Dal 1kg", "500", "kg", "/portal/catalog/prod-moong-1"]


def test_whatsapp_channel_maps_goods_ready_template():
    """WhatsAppChannel maps order/dispatch notifications to wareflow_goods_ready template."""
    mock_transport = MockTransport(status_code=200)
    mock_http = httpx.Client(transport=mock_transport)
    client = WhatsAppClient(access_token="tok", phone_number_id="123", http_client=mock_http)
    channel = WhatsAppChannel(whatsapp_client=client)

    payload = NotificationPayload(
        user_id="usr-ret-2",
        type="order_ready",
        title="Order Ready for Dispatch",
        body="Sales Order #SO-2026-0819 has been packed and scheduled for delivery.",
        recipient_phone="9876522222",
        metadata={
            "order_number": "SO-2026-0819",
            "retailer_name": "Metro Cash & Carry",
            "summary": "15 packages / 450 kg",
            "link": "/portal/orders/so-2026-0819",
        },
    )

    success = channel.send(payload)
    assert success is True

    req_json = mock_transport.last_json
    assert req_json is not None
    assert req_json["template"]["name"] == "wareflow_goods_ready"
    params = [p["text"] for p in req_json["template"]["components"][0]["parameters"]]
    assert params == ["SO-2026-0819", "Metro Cash & Carry", "15 packages / 450 kg", "/portal/orders/so-2026-0819"]


def test_whatsapp_channel_unconfigured_simulates_cleanly_without_raising():
    """With WHATSAPP_ACCESS_TOKEN unset, WhatsAppChannel logs clear notice and does not crash request."""
    # Unset credentials
    channel = WhatsAppChannel(access_token="", phone_number_id="")
    assert channel.client.is_configured is False

    payload = NotificationPayload(
        user_id="usr-ret-3",
        type="order_ready",
        title="Order Ready",
        body="Your goods are ready.",
        recipient_phone="+91 99999 88888",
    )

    # Must complete cleanly and return True (simulation successful)
    success = channel.send(payload)
    assert success is True


def test_whatsapp_channel_skips_when_no_phone_provided():
    """WhatsAppChannel safely skips without error when recipient has no phone number."""
    channel = WhatsAppChannel(access_token="test_tok", phone_number_id="123")
    payload = NotificationPayload(
        user_id="usr-ret-4",
        type="general_alert",
        title="System Notice",
        body="Notice without phone number",
        recipient_phone=None,
    )

    success = channel.send(payload)
    assert success is True


def test_notification_service_dispatches_to_whatsapp_ocp_proof():
    """Adding WhatsAppChannel requires zero changes to NotificationService (OCP compliance proof)."""
    mock_transport = MockTransport(status_code=200)
    mock_http = httpx.Client(transport=mock_transport)

    notif_repo = InMemoryNotificationRepository()
    in_app_ch = InAppChannel(notification_repo=notif_repo)
    whatsapp_ch = WhatsAppChannel(
        whatsapp_client=WhatsAppClient(
            access_token="valid_token",
            phone_number_id="10029384756",
            http_client=mock_http,
        )
    )

    service = NotificationService(
        notification_repo=notif_repo,
        channels=[in_app_ch, whatsapp_ch],
    )

    results = service.notify(
        user_id="usr-retailer-5",
        type="stock_available",
        title="Refined Sugar Back in Stock",
        body="Refined Sugar M-30 is now back in warehouse storage.",
        channels=["in_app", "whatsapp"],
        recipient_phone="+91 98765 43210",
        metadata={
            "product_name": "Refined Sugar M-30 50kg",
            "quantity": 1000,
            "uom": "bags",
        },
    )

    assert results.get("in_app") is True
    assert results.get("whatsapp") is True
    assert len(notif_repo._notifications) == 1

    # Verify Meta WhatsApp API was invoked with correct payload
    assert mock_transport.last_json is not None
    assert mock_transport.last_json["template"]["name"] == "wareflow_stock_available"
    assert mock_transport.last_json["to"] == "919876543210"
