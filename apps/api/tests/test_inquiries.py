"""Tests for product inquiries, staff responses, and notification triggers."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.security import CurrentUser
from app.main import app
from app.models.catalog import Category, Product
from app.models.portal import InquiryStatusEnum, ProductInquiry, RetailerUser
from app.models.retailer import Retailer
from app.repositories.impl.inquiry_repository import InMemoryInquiryRepository
from app.repositories.impl.notification_repository import InMemoryNotificationRepository
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.retailer_user_repository import InMemoryRetailerUserRepository
from app.schemas.inquiries import CreateInquiryRequest, RespondInquiryRequest
from app.services.inquiry_service import InquiryService
from app.services.notification_service import NotificationService


def setup_inquiry_environment():
    """Create in-memory dependencies and mock records for testing."""
    inquiry_repo = InMemoryInquiryRepository()
    retailer_repo = InMemoryRetailerRepository()
    retailer_user_repo = InMemoryRetailerUserRepository()
    notif_repo = InMemoryNotificationRepository()

    # Seed Category & Product
    cat = Category(id="cat-rice", name="Rice & Grains")
    product = Product(
        id="prod-rice-1",
        sku="RIC-BAS-001",
        name="Royal Basmati Rice 25kg",
        category_id=cat.id,
        base_uom_id="uom-bag",
        wholesale_price=1000.0,
        cost_price=800.0,
        is_active=True,
    )
    product.category = cat
    product_repo = InMemoryProductRepository(seed_products=[product], seed_categories=[cat])

    notif_service = NotificationService(
        notification_repo=notif_repo,
        retailer_user_repo=retailer_user_repo,
    )
    inquiry_service = InquiryService(
        inquiry_repo=inquiry_repo,
        product_repo=product_repo,
        notification_service=notif_service,
    )

    # Seed Retailers
    ret_alice = Retailer(
        id="ret-alice-1",
        name="Alice Grocery Store",
        phone="9876543210",
        email="alice@grocery.com",
    )
    ret_bob = Retailer(
        id="ret-bob-1",
        name="Bob Supermarket",
        phone="9876543211",
        email="bob@supermarket.com",
    )
    retailer_repo.create(ret_alice)
    retailer_repo.create(ret_bob)

    # Seed Retailer Users
    ret_user_alice = RetailerUser(
        id="uid_alice",
        retailer_id=ret_alice.id,
        email="alice@grocery.com",
        display_name="Alice",
    )
    ret_user_bob = RetailerUser(
        id="uid_bob",
        retailer_id=ret_bob.id,
        email="bob@supermarket.com",
        display_name="Bob",
    )
    retailer_user_repo.create_user(ret_user_alice)
    retailer_user_repo.create_user(ret_user_bob)

    return {
        "inquiry_repo": inquiry_repo,
        "product_repo": product_repo,
        "retailer_repo": retailer_repo,
        "retailer_user_repo": retailer_user_repo,
        "notif_repo": notif_repo,
        "notif_service": notif_service,
        "inquiry_service": inquiry_service,
        "product": product,
        "ret_alice": ret_alice,
        "ret_bob": ret_bob,
        "ret_user_alice": ret_user_alice,
    }


def test_retailer_can_submit_product_inquiry():
    """Retailer creates an inquiry for an existing product with open status."""
    env = setup_inquiry_environment()
    service: InquiryService = env["inquiry_service"]

    alice_user = CurrentUser(
        id="uid_alice",
        email="alice@grocery.com",
        role="Retailer",
        permissions=set(),
        account_type="retailer",
        retailer_id=env["ret_alice"].id,
    )

    req = CreateInquiryRequest(
        product_id=env["product"].id,
        message="Can we get a bulk discount for 50 bags?",
    )
    inquiry = service.create_retailer_inquiry(current_user=alice_user, payload=req)

    assert inquiry.id is not None
    assert inquiry.product_id == env["product"].id
    assert inquiry.product_name == "Royal Basmati Rice 25kg"
    assert inquiry.product_sku == "RIC-BAS-001"
    assert inquiry.retailer_id == env["ret_alice"].id
    assert inquiry.status == "open"
    assert inquiry.response is None


def test_retailer_sees_only_own_inquiries_strict_data_wall():
    """Retailer A cannot see inquiries submitted by Retailer B."""
    env = setup_inquiry_environment()
    service: InquiryService = env["inquiry_service"]
    inquiry_repo = env["inquiry_repo"]

    # Inquiry from Alice
    inq_alice = ProductInquiry(
        product_id=env["product"].id,
        retailer_id=env["ret_alice"].id,
        message="Alice question",
        status=InquiryStatusEnum.OPEN,
        created_at=datetime.now(UTC),
    )
    inq_alice.product = env["product"]
    inq_alice.retailer = env["ret_alice"]
    inquiry_repo.create(inq_alice)

    # Inquiry from Bob
    inq_bob = ProductInquiry(
        product_id=env["product"].id,
        retailer_id=env["ret_bob"].id,
        message="Bob question",
        status=InquiryStatusEnum.OPEN,
        created_at=datetime.now(UTC),
    )
    inq_bob.product = env["product"]
    inq_bob.retailer = env["ret_bob"]
    inquiry_repo.create(inq_bob)

    # Alice fetches inquiries
    alice_user = CurrentUser(
        id="uid_alice",
        email="alice@grocery.com",
        role="Retailer",
        permissions=set(),
        account_type="retailer",
        retailer_id=env["ret_alice"].id,
    )
    alice_inquiries = service.list_retailer_inquiries(alice_user)

    assert len(alice_inquiries) == 1
    assert alice_inquiries[0].message == "Alice question"
    assert alice_inquiries[0].retailer_id == env["ret_alice"].id


def test_staff_inbox_lists_and_filters_inquiries():
    """Staff sees all inquiries and can filter by status."""
    env = setup_inquiry_environment()
    service: InquiryService = env["inquiry_service"]
    inquiry_repo = env["inquiry_repo"]

    inq1 = ProductInquiry(
        product_id=env["product"].id,
        retailer_id=env["ret_alice"].id,
        message="Open question",
        status=InquiryStatusEnum.OPEN,
        created_at=datetime.now(UTC),
    )
    inq1.product = env["product"]
    inquiry_repo.create(inq1)

    inq2 = ProductInquiry(
        product_id=env["product"].id,
        retailer_id=env["ret_bob"].id,
        message="Responded question",
        status=InquiryStatusEnum.RESPONDED,
        response="Already answered",
        created_at=datetime.now(UTC),
    )
    inq2.product = env["product"]
    inquiry_repo.create(inq2)

    all_inquiries = service.list_staff_inquiries()
    assert len(all_inquiries) == 2

    open_inquiries = service.list_staff_inquiries(status_filter="open")
    assert len(open_inquiries) == 1
    assert open_inquiries[0].status == "open"

    responded_inquiries = service.list_staff_inquiries(status_filter="responded")
    assert len(responded_inquiries) == 1
    assert responded_inquiries[0].status == "responded"


def test_staff_responds_to_inquiry_and_dispatches_notification():
    """Staff responding updates inquiry status and sends notification to retailer user."""
    env = setup_inquiry_environment()
    service: InquiryService = env["inquiry_service"]
    inquiry_repo = env["inquiry_repo"]
    notif_repo = env["notif_repo"]

    inq = ProductInquiry(
        product_id=env["product"].id,
        retailer_id=env["ret_alice"].id,
        message="Can you deliver 100 bags tomorrow?",
        status=InquiryStatusEnum.OPEN,
        created_at=datetime.now(UTC),
    )
    inq.product = env["product"]
    inq.retailer = env["ret_alice"]
    inquiry_repo.create(inq)

    staff_user = CurrentUser(
        id="staff_123",
        email="manager@wareflow.io",
        role="Manager",
        permissions={"inquiries:manage"},
        account_type="staff",
    )

    resp_req = RespondInquiryRequest(
        response="Yes, 100 bags will be dispatched tomorrow by 10 AM.",
    )
    updated = service.respond_to_inquiry(
        inquiry_id=inq.id,
        payload=resp_req,
        current_user=staff_user,
    )

    assert updated.status == "responded"
    assert updated.response == "Yes, 100 bags will be dispatched tomorrow by 10 AM."
    assert updated.responded_at is not None

    # Verify notification was fired to retailer user
    notifications = notif_repo.list_for_user(env["ret_user_alice"].id)
    assert len(notifications) == 1
    assert "Inquiry Answered" in notifications[0].title
    assert "100 bags will be dispatched" in notifications[0].body
    assert notifications[0].type == "inquiry_response"


def test_inquiry_http_endpoints_and_guards():
    """HTTP router tests for portal and staff inquiry endpoints."""
    from app.core.di import get_inquiry_service
    from app.core.security import get_current_user

    env = setup_inquiry_environment()
    service: InquiryService = env["inquiry_service"]

    retailer_user = CurrentUser(
        id="uid_alice",
        email="alice@grocery.com",
        role="Retailer",
        permissions=set(),
        account_type="retailer",
        retailer_id=env["ret_alice"].id,
    )

    staff_user = CurrentUser(
        id="staff_123",
        email="manager@wareflow.io",
        role="Manager",
        permissions={"inquiries:read", "inquiries:manage"},
        account_type="staff",
    )

    app.dependency_overrides[get_inquiry_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: retailer_user

    client = TestClient(app)

    try:
        # Retailer submits inquiry
        post_res = client.post(
            "/portal/inquiries",
            json={"product_id": env["product"].id, "message": "Bulk price inquiry?"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert post_res.status_code == 201
        inq_data = post_res.json()
        inq_id = inq_data["id"]
        assert inq_data["status"] == "open"
        assert inq_data["product_name"] == "Royal Basmati Rice 25kg"

        # Retailer lists own inquiries
        list_res = client.get(
            "/portal/inquiries",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # Retailer cannot access staff inbox (403)
        staff_inbox_res = client.get(
            "/inquiries",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert staff_inbox_res.status_code == 403

        # Switch to staff user
        app.dependency_overrides[get_current_user] = lambda: staff_user

        # Staff lists inquiries
        staff_list_res = client.get(
            "/inquiries",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert staff_list_res.status_code == 200
        assert len(staff_list_res.json()) >= 1

        # Staff responds to inquiry
        respond_res = client.patch(
            f"/inquiries/{inq_id}/respond",
            json={"response": "We can offer a 7% bulk discount on 100+ units."},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert respond_res.status_code == 200
        assert respond_res.json()["status"] == "responded"
        assert "7% bulk discount" in respond_res.json()["response"]

    finally:
        app.dependency_overrides.clear()
