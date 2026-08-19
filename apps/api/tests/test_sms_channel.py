"""Tests for Step 13.6 SMS Notification Channel (Fallback & Opt-in Preferences)."""

from typing import Any
import pytest
from fastapi.testclient import TestClient

from app.core.di import (
    get_notification_preference_service,
    get_notification_service,
)
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.notification import NotificationPreference
from app.repositories.impl.notification_preference_repository import (
    InMemoryNotificationPreferenceRepository,
)
from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.schemas.notification import NotificationPreferenceUpdateRequest
from app.services.notification_channels.base import NotificationPayload
from app.services.notification_channels.sms_channel import SmsChannel
from app.services.notification_preference_service import NotificationPreferenceService
from app.services.notification_service import NotificationService
from app.services.sms_client import SmsClient, normalize_phone_number, truncate_sms_text


class MockSmsClient(SmsClient):
    """Mock SMS client recording sent messages."""

    def __init__(self) -> None:
        super().__init__(account_sid="mock_sid", auth_token="mock_tok", from_number="+15005550006")
        self.sent_messages: list[dict[str, Any]] = []

    def send_sms(self, to_phone: str, message: str) -> dict[str, Any]:
        record = {
            "to": normalize_phone_number(to_phone),
            "body": truncate_sms_text(message, 160),
            "length": len(truncate_sms_text(message, 160)),
        }
        self.sent_messages.append(record)
        return {"status": "sent", "record": record}


def test_sms_client_phone_normalization_and_truncation():
    """Verify phone formatting and strict 160-char length discipline."""
    # 10 digit Indian mobile number gets +91 prepended
    assert normalize_phone_number("9876543210") == "+919876543210"
    # International number preserved
    assert normalize_phone_number("+1 (415) 555-0199") == "+14155550199"

    # Short message stays intact
    short_text = "WareFlow: Order #SO-101 confirmed."
    assert truncate_sms_text(short_text) == short_text

    # Excessively long text is truncated strictly to 160 characters
    long_text = "WareFlow Critical Alert: " + "A" * 200
    truncated = truncate_sms_text(long_text, max_chars=160)
    assert len(truncated) <= 160
    assert truncated.endswith("...")


def test_sms_channel_unconfigured_graceful_simulation():
    """Unconfigured SMS client degrades gracefully to simulation mode without failing."""
    unconfigured_client = SmsClient()  # No keys provided
    channel = SmsChannel(sms_client=unconfigured_client)

    payload = NotificationPayload(
        user_id="user-owner-1",
        type="low_stock",
        title="Low Stock Alert: Basmati Rice",
        body="Stock for Basmati Rice is below reorder point.",
        recipient_phone="+919876543210",
        metadata={"product_name": "Basmati Rice 25kg", "current_stock": "5", "uom": "bags"},
    )

    success = channel.send(payload)
    assert success is True


def test_sms_channel_formats_critical_events():
    """Verify short-message formatting for low stock, orders, and dispatch signals."""
    mock_client = MockSmsClient()
    channel = SmsChannel(sms_client=mock_client)

    # 1. Low stock alert
    stock_payload = NotificationPayload(
        user_id="user-owner-1",
        type="low_stock_critical",
        title="Critical Stock Warning",
        body="Tata Salt 1kg has 12 packets remaining.",
        recipient_phone="+919876543210",
        metadata={"product_name": "Tata Salt 1kg", "current_stock": "12", "uom": "pkts"},
    )
    assert channel.send(stock_payload) is True
    assert len(mock_client.sent_messages) == 1
    assert "Low stock on Tata Salt 1kg (12 pkts remaining)" in mock_client.sent_messages[0]["body"]
    assert mock_client.sent_messages[0]["length"] <= 160

    # 2. Order confirmed alert
    order_payload = NotificationPayload(
        user_id="ret-buyer-1",
        type="order_confirmed",
        title="Order Confirmation",
        body="Your sales order has been confirmed.",
        recipient_phone="+919988776655",
        metadata={"so_number": "SO-2026-0042", "total_amount": "45000.00"},
    )
    assert channel.send(order_payload) is True
    assert len(mock_client.sent_messages) == 2
    assert "Order #SO-2026-0042 confirmed for Rs.45000.00" in mock_client.sent_messages[1]["body"]
    assert mock_client.sent_messages[1]["length"] <= 160

    # 3. Goods ready / PO dispatch alert
    dispatch_payload = NotificationPayload(
        user_id="user-owner-1",
        type="goods_ready_dispatch",
        title="Consignment Ready",
        body="Tata Consumer has packed PO-101.",
        recipient_phone="+919876543210",
        metadata={"po_number": "PO-101", "supplier_name": "Tata Consumer Ltd"},
    )
    assert channel.send(dispatch_payload) is True
    assert len(mock_client.sent_messages) == 3
    assert "PO #PO-101 from Tata Consumer Ltd is ready" in mock_client.sent_messages[2]["body"]
    assert mock_client.sent_messages[2]["length"] <= 160


def test_notification_service_ocp_integration_with_sms_channel():
    """Verify NotificationService routes to SmsChannel (Strategy pattern / OCP proof)."""
    notif_repo = InMemoryNotificationRepository()
    mock_client = MockSmsClient()
    sms_channel = SmsChannel(sms_client=mock_client)

    # Plug in SmsChannel as one of the channels
    service = NotificationService(
        notification_repo=notif_repo,
        channels=[sms_channel],
    )

    results = service.notify(
        user_id="user-123",
        type="low_stock",
        title="Low Stock: Sunflower Oil 1L",
        body="Only 8 bottles left in warehouse.",
        channels=["sms"],
        recipient_phone="+919811223344",
        metadata={"product_name": "Fortune Sunflower Oil 1L", "current_stock": "8", "uom": "bottles"},
    )

    assert results.get("sms") is True
    assert len(mock_client.sent_messages) == 1
    assert mock_client.sent_messages[0]["to"] == "+919811223344"
    assert "Low stock on Fortune Sunflower Oil 1L" in mock_client.sent_messages[0]["body"]


def test_notification_preference_service_and_opt_in_policy():
    """Verify default opt-in policy (SMS disabled by default) and updates."""
    repo = InMemoryNotificationPreferenceRepository()
    service = NotificationPreferenceService(pref_repo=repo)

    # 1. Default preferences
    default_pref = service.get_preferences(entity_type="user", entity_id="user-staff-1")
    assert default_pref.in_app_enabled is True
    assert default_pref.email_enabled is True
    assert default_pref.whatsapp_enabled is True
    assert default_pref.sms_enabled is False  # SMS is strict opt-in

    # By default, SMS is blocked
    assert service.is_channel_enabled("user-staff-1", "sms", "low_stock") is False
    assert service.is_channel_enabled("user-staff-1", "whatsapp") is True

    # 2. User opts in to SMS for critical stock alerts
    updated = service.update_preferences(
        entity_type="user",
        entity_id="user-staff-1",
        payload=NotificationPreferenceUpdateRequest(
            sms_enabled=True,
            critical_stock_sms=True,
            order_updates_sms=False,
        ),
    )
    assert updated.sms_enabled is True
    assert updated.critical_stock_sms is True

    # Check rule queries
    assert service.is_channel_enabled("user-staff-1", "sms", "low_stock") is True
    assert service.is_channel_enabled("user-staff-1", "sms", "order_confirmed") is False


def test_notification_preference_http_endpoints():
    """Verify HTTP router endpoints for notification preference management."""
    repo = InMemoryNotificationPreferenceRepository()
    pref_service = NotificationPreferenceService(pref_repo=repo)
    notif_repo = InMemoryNotificationRepository()
    notif_service = NotificationService(notification_repo=notif_repo)

    fake_user = CurrentUser(
        id="user-tester-1",
        email="tester@wareflow.io",
        display_name="Tester",
        role="Owner",
        permissions={"settings:manage", "inventory:manage"},
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_notification_preference_service] = lambda: pref_service
    app.dependency_overrides[get_notification_service] = lambda: notif_service

    client = TestClient(app)

    try:
        # 1. GET /notifications/preferences
        get_res = client.get("/notifications/preferences")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["entity_id"] == "user-tester-1"
        assert data["sms_enabled"] is False

        # 2. PUT /notifications/preferences
        put_res = client.put(
            "/notifications/preferences",
            json={
                "sms_enabled": True,
                "critical_stock_sms": True,
                "order_updates_sms": True,
            },
        )
        assert put_res.status_code == 200
        put_data = put_res.json()
        assert put_data["sms_enabled"] is True
        assert put_data["critical_stock_sms"] is True

        # 3. GET /notifications/preferences/retailer/ret-abc-123
        ret_get = client.get("/notifications/preferences/retailer/ret-abc-123")
        assert ret_get.status_code == 200
        assert ret_get.json()["entity_id"] == "ret-abc-123"

        # 4. PUT /notifications/preferences/retailer/ret-abc-123
        ret_put = client.put(
            "/notifications/preferences/retailer/ret-abc-123",
            json={"sms_enabled": True, "order_updates_sms": True},
        )
        assert ret_put.status_code == 200
        assert ret_put.json()["sms_enabled"] is True
    finally:
        app.dependency_overrides.clear()
