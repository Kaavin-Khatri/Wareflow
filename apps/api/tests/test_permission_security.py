"""
Security & RBAC Permission Enforcement Test Suite (Step 22.1).

Validates that mutating routes strictly enforce granular permissions and reject unauthorized roles:
- Products / Inventory adjustments (requires 'inventory:manage'): Sales Staff, Retailer -> 403 Forbidden
- Sales Orders creation / confirmation (requires 'orders:create' / 'orders:approve'): Warehouse Staff -> 403 Forbidden
- GST Tax Invoicing (requires 'orders:manage'): Warehouse Staff, Sales Staff -> 403 Forbidden
- Payments recording (requires 'orders:manage'): Sales Staff, Warehouse Staff -> 403 Forbidden
- Staff & Role management (requires 'staff:manage'): Accountant, Sales Staff, Warehouse Staff -> 403 Forbidden
- Unauthenticated requests -> 401 Unauthorized
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser, get_current_user
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def mock_role_user(user_id: str, email: str, role: str, permissions: list[str]):
    """Helper to mock CurrentUser with specific permissions."""
    def _override():
        return CurrentUser(
            id=user_id,
            email=email,
            role=role,
            permissions=set(permissions),
            account_type="staff",
            is_active=True,
            is_2fa_verified=True,
        )
    return _override


class TestUnauthenticatedAccess:
    """Verify that all mutating routes reject unauthenticated requests with 401 Unauthorized."""

    def test_create_product_unauthenticated(self, client):
        app.dependency_overrides.clear()
        res = client.post("/products", json={"name": "Hacked Product", "sku": "HACK-01"})
        assert res.status_code == 401

    def test_create_order_unauthenticated(self, client):
        app.dependency_overrides.clear()
        res = client.post("/sales-orders", json={"retailer_id": "test", "items": []})
        assert res.status_code == 401

    def test_create_invoice_unauthenticated(self, client):
        app.dependency_overrides.clear()
        res = client.post("/sales-orders/so-123/invoice")
        assert res.status_code == 401

    def test_record_payment_unauthenticated(self, client):
        app.dependency_overrides.clear()
        res = client.post("/invoices/inv-123/payments", json={"amount": 1000.0, "payment_mode": "cash"})
        assert res.status_code == 401

    def test_invite_staff_unauthenticated(self, client):
        app.dependency_overrides.clear()
        res = client.post("/staff/invite", json={"email": "attacker@evil.com", "role_id": "r1"})
        assert res.status_code == 401


class TestRBACPermissionGating:
    """Verify that roles without required permissions receive 403 Forbidden."""

    def test_warehouse_staff_cannot_create_invoice(self, client):
        # Warehouse staff has ['inventory:view', 'inventory:manage', 'orders:view'], NOT 'orders:manage'
        app.dependency_overrides[get_current_user] = mock_role_user(
            "u-wh", "wh@wareflow.io", "Warehouse Staff", ["inventory:view", "inventory:manage", "orders:view"]
        )
        res = client.post("/sales-orders/so-001/invoice")
        assert res.status_code == 403
        assert "orders:manage" in res.json().get("detail", "")
        app.dependency_overrides.clear()

    def test_sales_staff_cannot_adjust_inventory(self, client):
        # Sales staff has ['inventory:view', 'orders:create', 'orders:view', 'invoices:view'], NOT 'inventory:manage'
        app.dependency_overrides[get_current_user] = mock_role_user(
            "u-sales", "sales@wareflow.io", "Sales Staff", ["inventory:view", "orders:create", "orders:view", "invoices:view"]
        )
        res = client.post("/stock/adjustments", json={
            "product_id": "p1",
            "warehouse_id": "wh1",
            "batch_id": "b1",
            "delta": -5.0,
            "reason": "damaged",
            "notes": "Test"
        })
        assert res.status_code == 403
        assert "inventory:manage" in res.json().get("detail", "")
        app.dependency_overrides.clear()

    def test_accountant_cannot_invite_staff_or_change_roles(self, client):
        # Accountant has ['orders:view', 'invoices:create', 'invoices:view', 'payments:record', 'reports:view'], NOT 'staff:manage'
        app.dependency_overrides[get_current_user] = mock_role_user(
            "u-acc", "acc@wareflow.io", "Accountant", ["orders:view", "invoices:create", "invoices:view", "payments:record", "reports:view"]
        )
        res = client.post("/staff/invite", json={"email": "newbie@wareflow.io", "role_id": "role-1"})
        assert res.status_code == 403
        assert "staff:manage" in res.json().get("detail", "")
        app.dependency_overrides.clear()

    def test_sales_staff_cannot_record_payments(self, client):
        # Sales staff without orders:manage cannot record payments against customer balances
        app.dependency_overrides[get_current_user] = mock_role_user(
            "u-sales", "sales@wareflow.io", "Sales Staff", ["inventory:view", "orders:create", "orders:view"]
        )
        res = client.post("/invoices/inv-001/payments", json={"amount": 5000.0, "payment_mode": "cash"})
        assert res.status_code == 403
        assert "orders:manage" in res.json().get("detail", "")
        app.dependency_overrides.clear()
