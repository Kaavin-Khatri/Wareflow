"""Tests for Notification Engine and Strategy Pattern Channels (Step 13.1)."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.di import get_notification_service
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.services.notification_channels.base import BaseNotificationChannel, NotificationPayload
from app.services.notification_channels.email_channel import EmailChannel
from app.services.notification_channels.in_app_channel import InAppChannel
from app.services.notification_service import NotificationService


class StubSmsChannel(BaseNotificationChannel):
    """Stub SMS channel created externally to prove Open/Closed Principle (OCP)."""

    def __init__(self) -> None:
        self.dispatched_payloads: list[NotificationPayload] = []

    @property
    def channel_name(self) -> str:
        return "sms"

    def send(self, payload: NotificationPayload) -> bool:
        self.dispatched_payloads.append(payload)
        return True


def test_notification_fanout_to_inapp_and_email_channels():
    """A test notification arrives both in-app and by email when both channels are requested."""
    notif_repo = InMemoryNotificationRepository()
    in_app_ch = InAppChannel(notification_repo=notif_repo)

    # Mock email sender
    mock_email_ch = EmailChannel(api_key=None, from_email="alerts@wareflow.io")
    dispatched_emails: list[NotificationPayload] = []

    def mock_send(payload: NotificationPayload) -> bool:
        dispatched_emails.append(payload)
        return True

    mock_email_ch.send = mock_send  # type: ignore

    service = NotificationService(
        notification_repo=notif_repo,
        channels=[in_app_ch, mock_email_ch],
    )

    results = service.notify(
        user_id="user-ops-1",
        type="low_stock",
        title="Low Stock: Royal Basmati Rice 5kg",
        body="Warehouse stock (15 bags) is below reorder point (50 bags).",
        channels=["in_app", "email"],
        recipient_email="ops-manager@kiranamart.in",
    )

    # Delivery results indicate success across both channels
    assert results["in_app"] is True
    assert results["email"] is True

    # Check In-App persistence in repository
    in_app_items = notif_repo.list_for_user("user-ops-1")
    assert len(in_app_items) == 1
    assert in_app_items[0].title == "Low Stock: Royal Basmati Rice 5kg"
    assert in_app_items[0].is_read is False

    # Check Email dispatch
    assert len(dispatched_emails) == 1
    assert dispatched_emails[0].recipient_email == "ops-manager@kiranamart.in"
    assert dispatched_emails[0].type == "low_stock"


def test_open_closed_principle_extensibility_with_stub_sms_channel():
    """Adding a stub SmsChannel requires zero changes to NotificationService (OCP proof)."""
    notif_repo = InMemoryNotificationRepository()
    in_app_ch = InAppChannel(notification_repo=notif_repo)
    sms_ch = StubSmsChannel()

    service = NotificationService(
        notification_repo=notif_repo,
        channels=[in_app_ch, sms_ch],
    )

    results = service.notify(
        user_id="driver-42",
        type="delivery_assigned",
        title="New Delivery Dispatched",
        body="Sales order SO-2026-0099 is assigned to your vehicle.",
        channels=["in_app", "sms"],
        recipient_phone="+91 98200 99887",
    )

    assert results["in_app"] is True
    assert results["sms"] is True

    assert len(sms_ch.dispatched_payloads) == 1
    assert sms_ch.dispatched_payloads[0].recipient_phone == "+91 98200 99887"
    assert sms_ch.dispatched_payloads[0].title == "New Delivery Dispatched"


def test_inapp_channel_firestore_realtime_mirror():
    """InAppChannel mirrors notification payload to Firestore document under notifications/{uid}/items/{id}."""
    notif_repo = InMemoryNotificationRepository()
    mock_firestore = MagicMock()
    mock_doc = MagicMock()
    mock_firestore.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_doc

    in_app_ch = InAppChannel(notification_repo=notif_repo, firestore_client=mock_firestore)

    payload = NotificationPayload(
        id="notif-rt-1",
        user_id="user-rt-1",
        type="fssai_expiry",
        title="FSSAI License Expiring Soon",
        body="Supplier Shree Ganesh license expires in 5 days.",
    )

    success = in_app_ch.send(payload)
    assert success is True

    # Verify Firestore document write
    mock_firestore.collection.assert_called_with("notifications")
    mock_doc.set.assert_called_once()
    saved_doc = mock_doc.set.call_args[0][0]
    assert saved_doc["id"] == "notif-rt-1"
    assert saved_doc["user_id"] == "user-rt-1"
    assert saved_doc["title"] == "FSSAI License Expiring Soon"
    assert saved_doc["is_read"] is False


def test_unread_count_and_mark_all_as_read_lifecycle():
    """Unread badge count matches repository count exactly and mark_all_as_read updates state."""
    notif_repo = InMemoryNotificationRepository()
    service = NotificationService(notification_repo=notif_repo)

    user_id = "user-finance-1"

    # Send 3 notifications
    service.notify(user_id=user_id, type="invoice_overdue", title="Overdue INV-001", body="Payment pending 30 days")
    service.notify(user_id=user_id, type="invoice_overdue", title="Overdue INV-002", body="Payment pending 45 days")
    service.notify(user_id=user_id, type="payment_received", title="Payment Received", body="₹10,000 recorded")

    assert service.get_unread_count(user_id) == 3

    # Paginated listing
    items, total, unread = service.list_user_notifications(user_id=user_id, page=1, limit=2)
    assert total == 3
    assert unread == 3
    assert len(items) == 2

    # Mark single as read
    first_id = items[0].id
    service.mark_notification_read(notification_id=first_id, user_id=user_id)
    assert service.get_unread_count(user_id) == 2

    # Mark all remaining as read
    marked_count = service.mark_all_notifications_read(user_id=user_id)
    assert marked_count == 2
    assert service.get_unread_count(user_id) == 0


def test_notifications_http_api_endpoints():
    """FastAPI endpoints GET /notifications, PATCH /notifications/{id}/read, PATCH /notifications/read-all."""
    test_user = CurrentUser(
        id="user-http-notif",
        email="manager@wareflow.io",
        role="Manager",
        permissions=["orders:view"],
    )

    notif_repo = InMemoryNotificationRepository()
    service = NotificationService(notification_repo=notif_repo)

    # Seed notification
    n1 = service.send_notification(
        user_id="user-http-notif",
        type="order_confirmed",
        title="Sales Order SO-100 Confirmed",
        body="Stock batches deducted.",
    )

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_notification_service] = lambda: service

    client = TestClient(app)

    try:
        # 1. GET /notifications
        resp = client.get("/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["unread_count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Sales Order SO-100 Confirmed"

        # 2. PATCH /notifications/{id}/read
        resp_read = client.patch(f"/notifications/{n1.id}/read")
        assert resp_read.status_code == 200
        assert resp_read.json()["success"] is True

        # Check unread count is now 0
        resp_after = client.get("/notifications")
        assert resp_after.json()["unread_count"] == 0

        # 3. PATCH /notifications/read-all
        resp_all = client.patch("/notifications/read-all")
        assert resp_all.status_code == 200
        assert resp_all.json()["success"] is True

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_notification_service, None)
