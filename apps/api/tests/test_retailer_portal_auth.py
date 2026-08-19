"""Unit tests for Retailer Self-Service Portal Auth, Invitation, and Tenant Data Wall."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.routers import portal, retailers
from app.core.di import get_ledger_service, get_portal_auth_service, get_retailer_service
from app.core.security import (
    CurrentUser,
    get_current_user,
    require_own_retailer,
    require_permission,
    require_portal_retailer,
    require_staff,
)
from app.models.auth_rbac import Role
from app.models.billing import Invoice, InvoiceStatusEnum
from app.models.portal import RetailerPortalInvite, RetailerUser
from app.models.profile import Profile
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SOStatusEnum
from app.repositories.impl.invoice_repository import InMemoryInvoiceRepository
from app.repositories.impl.payment_repository import InMemoryPaymentRepository
from app.repositories.impl.profile_repository import InMemoryProfileRepository
from app.repositories.impl.retailer_repository import InMemoryRetailerRepository
from app.repositories.impl.retailer_user_repository import InMemoryRetailerUserRepository
from app.repositories.impl.sales_order_repository import InMemorySalesOrderRepository
from app.schemas.retailers import RetailerInviteRequest
from app.services.ledger_service import LedgerService
from app.services.portal_auth_service import PortalAuthService
from app.services.retailer_service import RetailerService


def _setup_test_environment():
    owner_role = Role(id="role-owner", name="Owner", description="Owner")
    staff_profile = Profile(
        id="uid_staff_1",
        email="manager@wareflow.com",
        display_name="Manager Staff",
        role_id="role-owner",
        is_active=True,
    )
    profile_repo = InMemoryProfileRepository(
        initial_roles=[owner_role],
        initial_profiles=[staff_profile],
        initial_role_permissions={
            "role-owner": ["retailers:manage", "retailers:view", "orders:view", "invoices:view"]
        },
    )

    retailer_a = Retailer(
        id="ret-aaa",
        name="Alpha Mart Wholesale",
        contact_person="Alice Smith",
        email="alice@alphamart.com",
        pricing_tier="silver",
        credit_limit=500000.00,
        credit_balance=50000.00,
        is_active=True,
    )
    retailer_b = Retailer(
        id="ret-bbb",
        name="Beta Traders",
        contact_person="Bob Jones",
        email="bob@betatraders.com",
        pricing_tier="standard",
        credit_limit=200000.00,
        credit_balance=0.00,
        is_active=True,
    )
    retailer_repo = InMemoryRetailerRepository(initial_data=[retailer_a, retailer_b])

    ret_user_a = RetailerUser(
        id="uid_ret_alice",
        retailer_id="ret-aaa",
        email="alice@alphamart.com",
        display_name="Alice Smith",
        is_active=True,
    )
    user_repo = InMemoryRetailerUserRepository(initial_users=[ret_user_a])

    order_a = SalesOrder(
        id="so-aaa-1",
        so_number="SO-ALPHA-001",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-aaa",
        status=SOStatusEnum.CONFIRMED,
        total_amount=25000.00,
    )
    order_b = SalesOrder(
        id="so-bbb-1",
        so_number="SO-BETA-001",
        buyer_type=BuyerTypeEnum.RETAILER,
        retailer_id="ret-bbb",
        status=SOStatusEnum.CONFIRMED,
        total_amount=40000.00,
    )
    order_repo = InMemorySalesOrderRepository(orders=[order_a, order_b])

    inv_a = Invoice(
        id="inv-aaa-1",
        invoice_no="INV-2026-0001",
        sales_order_id="so-aaa-1",
        status=InvoiceStatusEnum.UNPAID,
        subtotal=21186.44,
        tax_amount=3813.56,
        total_amount=25000.00,
    )
    inv_a.sales_order = order_a
    invoice_repo = InMemoryInvoiceRepository()
    invoice_repo.set_sales_order(order_a)
    invoice_repo.create_invoice(inv_a, items=[])

    retailer_service = RetailerService(
        retailer_repo=retailer_repo,
        retailer_user_repo=user_repo,
    )
    portal_service = PortalAuthService(
        retailer_user_repo=user_repo,
        retailer_repo=retailer_repo,
        profile_repo=profile_repo,
        sales_order_repo=order_repo,
        invoice_repo=invoice_repo,
    )
    payment_repo = InMemoryPaymentRepository()
    ledger_service = LedgerService(
        retailer_repo=retailer_repo,
        invoice_repo=invoice_repo,
        payment_repo=payment_repo,
    )

    return {
        "profile_repo": profile_repo,
        "retailer_repo": retailer_repo,
        "user_repo": user_repo,
        "order_repo": order_repo,
        "invoice_repo": invoice_repo,
        "retailer_service": retailer_service,
        "portal_service": portal_service,
        "ledger_service": ledger_service,
        "staff_profile": staff_profile,
        "retailer_a": retailer_a,
        "retailer_b": retailer_b,
        "ret_user_a": ret_user_a,
        "order_a": order_a,
        "order_b": order_b,
        "inv_a": inv_a,
    }


def test_invite_retailer_generates_valid_portal_link_and_token():
    """QA 2: Inviting a retailer sends a working sign-in link tied to exactly that retailer record."""
    ctx = _setup_test_environment()
    retailer_service: RetailerService = ctx["retailer_service"]
    user_repo: InMemoryRetailerUserRepository = ctx["user_repo"]

    req = RetailerInviteRequest(email="procurement@betatraders.com", contact_person="Bob Lead")
    res = retailer_service.invite_portal_access("ret-bbb", req, actor_id="uid_staff_1")

    assert res.retailer_id == "ret-bbb"
    assert res.email == "procurement@betatraders.com"
    assert res.invite_token is not None
    assert "invite=" in res.sign_in_link or "token=" in res.sign_in_link

    # Verify invite is stored in repository
    invite = user_repo.get_invite_by_token(res.invite_token)
    assert invite is not None
    assert invite.retailer_id == "ret-bbb"
    assert invite.is_accepted is False


def test_retailer_portal_bootstrap_binds_to_retailer_and_rejects_staff():
    """Verify retailer user bootstrap with invite token or existing user."""
    ctx = _setup_test_environment()
    portal_service: PortalAuthService = ctx["portal_service"]
    user_repo: InMemoryRetailerUserRepository = ctx["user_repo"]

    # 1. Create invite
    invite = RetailerPortalInvite(
        id="inv-123",
        retailer_id="ret-bbb",
        email="buyer@betatraders.com",
        token="inv_tok_999",
        is_accepted=False,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    user_repo.create_invite(invite)

    # 2. Retailer signs up / bootstraps
    res = portal_service.bootstrap_retailer_user(
        uid="uid_firebase_bob",
        email="buyer@betatraders.com",
        invite_token="inv_tok_999",
        display_name="Bob Jones",
    )
    assert res.id == "uid_firebase_bob"
    assert res.retailer_id == "ret-bbb"
    assert res.retailer_name == "Beta Traders"
    assert res.account_type == "retailer"
    assert res.pricing_tier == "standard"

    # Verify invite marked accepted
    assert user_repo.get_invite_by_token("inv_tok_999").is_accepted is True

    # 3. Staff account attempting to bootstrap portal gets 403
    with pytest.raises(HTTPException) as exc_info:
        portal_service.bootstrap_retailer_user(
            uid="uid_staff_1",
            email="manager@wareflow.com",
        )
    assert exc_info.value.status_code == 403
    assert "Staff accounts cannot log into the Retailer Portal" in exc_info.value.detail


def test_retailer_sees_only_own_orders_and_invoices():
    """QA 1: A retailer logging into /portal sees only their own orders/invoices."""
    ctx = _setup_test_environment()
    portal_service: PortalAuthService = ctx["portal_service"]

    retailer_user_a = CurrentUser(
        id="uid_ret_alice",
        email="alice@alphamart.com",
        role="Retailer",
        permissions=set(),
        account_type="retailer",
        retailer_id="ret-aaa",
    )

    # Fetch orders for Retailer A
    orders = portal_service.list_retailer_orders(retailer_user_a)
    assert len(orders) == 1
    assert orders[0].id == "so-aaa-1"
    assert orders[0].so_number == "SO-ALPHA-001"

    # Fetch invoices for Retailer A
    invoices = portal_service.list_retailer_invoices(retailer_user_a)
    assert len(invoices) == 1
    assert invoices[0].id == "inv-aaa-1"
    assert invoices[0].invoice_number == "INV-2026-0001"


def test_retailer_attempting_to_fetch_another_retailers_order_is_blocked_with_403():
    """QA 1 (direct probe): Attempting to fetch another retailer's order ID directly via API confirms 403."""
    ctx = _setup_test_environment()
    portal_service: PortalAuthService = ctx["portal_service"]

    # Retailer A tries to fetch Retailer B's order "so-bbb-1"
    retailer_user_a = CurrentUser(
        id="uid_ret_alice",
        email="alice@alphamart.com",
        role="Retailer",
        permissions=set(),
        account_type="retailer",
        retailer_id="ret-aaa",
    )

    with pytest.raises(HTTPException) as exc_info:
        portal_service.get_retailer_order("so-bbb-1", retailer_user_a)

    assert exc_info.value.status_code == 403
    assert "Access denied: cannot access another retailer's data" in exc_info.value.detail

    # But fetching own order succeeds
    own_order = portal_service.get_retailer_order("so-aaa-1", retailer_user_a)
    assert own_order.id == "so-aaa-1"
    assert own_order.retailer_id == "ret-aaa"


def test_cross_boundary_guards():
    """QA 3: Staff accounts cannot access portal, and retailer accounts cannot access admin."""
    staff_user = CurrentUser(
        id="uid_staff_1",
        email="manager@wareflow.com",
        role="Manager",
        permissions={"retailers:manage", "retailers:view"},
        account_type="staff",
        retailer_id=None,
    )
    retailer_user = CurrentUser(
        id="uid_ret_alice",
        email="alice@alphamart.com",
        role="Retailer",
        permissions=set(),
        account_type="retailer",
        retailer_id="ret-aaa",
    )

    # 1. Staff accessing portal-only dependency gets 403
    with pytest.raises(HTTPException) as exc_staff:
        require_portal_retailer(staff_user)
    assert exc_staff.value.status_code == 403
    assert "Retailer portal access only" in exc_staff.value.detail

    # 2. Retailer accessing staff-only dependency gets 403
    with pytest.raises(HTTPException) as exc_ret:
        require_staff(retailer_user)
    assert exc_ret.value.status_code == 403
    assert "Staff access only" in exc_ret.value.detail

    # 3. require_own_retailer check:
    # Retailer accessing own ID succeeds
    assert require_own_retailer("ret-aaa", retailer_user).retailer_id == "ret-aaa"

    # Retailer accessing different ID gets 403
    with pytest.raises(HTTPException) as exc_own:
        require_own_retailer("ret-bbb", retailer_user)
    assert exc_own.value.status_code == 403
    assert "Access denied: cannot access another retailer's data" in exc_own.value.detail


def test_portal_http_router_endpoints():
    """Test FastAPI TestClient execution of /portal and /retailers invite endpoints."""
    ctx = _setup_test_environment()
    app = FastAPI()
    app.include_router(portal.router)
    app.include_router(retailers.router)

    portal_service: PortalAuthService = ctx["portal_service"]
    retailer_service: RetailerService = ctx["retailer_service"]
    ledger_service: LedgerService = ctx["ledger_service"]

    retailer_user = CurrentUser(
        id="uid_ret_alice",
        email="alice@alphamart.com",
        role="Retailer",
        permissions=set(),
        account_type="retailer",
        retailer_id="ret-aaa",
    )
    staff_user = CurrentUser(
        id="uid_staff_1",
        email="manager@wareflow.com",
        role="Owner",
        permissions={"retailers:manage", "retailers:view"},
        account_type="staff",
        retailer_id=None,
    )

    app.dependency_overrides[get_portal_auth_service] = lambda: portal_service
    app.dependency_overrides[get_retailer_service] = lambda: retailer_service
    app.dependency_overrides[get_ledger_service] = lambda: ledger_service
    app.dependency_overrides[require_portal_retailer] = lambda: retailer_user
    app.dependency_overrides[get_current_user] = lambda: retailer_user
    app.dependency_overrides[require_permission("retailers:manage")] = lambda: staff_user

    client = TestClient(app)

    # 1. GET /portal/me
    res = client.get("/portal/me")
    assert res.status_code == 200
    data = res.json()
    assert data["retailer_id"] == "ret-aaa"
    assert data["retailer_name"] == "Alpha Mart Wholesale"
    assert data["account_type"] == "retailer"

    # 2. GET /portal/orders
    res_orders = client.get("/portal/orders")
    assert res_orders.status_code == 200
    assert len(res_orders.json()) == 1
    assert res_orders.json()[0]["id"] == "so-aaa-1"

    # 3. GET /portal/invoices
    res_inv = client.get("/portal/invoices")
    assert res_inv.status_code == 200
    assert len(res_inv.json()) == 1
    assert res_inv.json()[0]["invoice_number"] == "INV-2026-0001"

    # 4. POST /retailers/{id}/invite-portal-access (staff-authorized)
    app.dependency_overrides[get_current_user] = lambda: staff_user
    res_invite = client.post(
        "/retailers/ret-aaa/invite-portal-access",
        json={"email": "custom@alphamart.com", "contact_person": "Alice Manager"},
    )
    assert res_invite.status_code == 200
    invite_data = res_invite.json()
    assert invite_data["retailer_id"] == "ret-aaa"
    assert invite_data["invite_token"] is not None
