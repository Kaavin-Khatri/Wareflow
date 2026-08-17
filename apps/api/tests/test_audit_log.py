"""Test suite for Admin Action Audit Logging."""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models.auth_rbac import Permission, Role, RolePermission
from app.models.catalog import Product
from app.models.profile import Profile
from app.models.retailer import Retailer


@pytest.fixture
def test_db_session() -> Generator[Session, None, None]:
    """In-memory SQLite database session for audit log unit tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def audit_test_env(test_db_session: Session):
    """Seed test database with roles, permissions, and profiles for audit testing."""
    # Seed Permissions
    p_audit = Permission(id=str(uuid.uuid4()), code="audit:view", description="View audit logs")
    p_settings = Permission(
        id=str(uuid.uuid4()), code="settings:manage", description="Manage settings"
    )
    p_inventory = Permission(
        id=str(uuid.uuid4()), code="inventory:manage", description="Manage inventory"
    )
    p_inv_view = Permission(
        id=str(uuid.uuid4()), code="inventory:view", description="View inventory"
    )
    test_db_session.add_all([p_audit, p_settings, p_inventory, p_inv_view])
    test_db_session.commit()

    # Seed Roles
    r_owner = Role(id=str(uuid.uuid4()), name="Owner", description="Owner role")
    r_staff = Role(
        id=str(uuid.uuid4()), name="Warehouse Staff", description="Warehouse floor staff"
    )
    r_accountant = Role(id=str(uuid.uuid4()), name="Accountant", description="Financial management")
    test_db_session.add_all([r_owner, r_staff, r_accountant])
    test_db_session.commit()

    # Seed Role Permissions
    rp1 = RolePermission(role_id=r_owner.id, permission_id=p_audit.id)
    rp2 = RolePermission(role_id=r_owner.id, permission_id=p_settings.id)
    rp3 = RolePermission(role_id=r_owner.id, permission_id=p_inventory.id)
    rp4 = RolePermission(role_id=r_staff.id, permission_id=p_inv_view.id)
    test_db_session.add_all([rp1, rp2, rp3, rp4])
    test_db_session.commit()

    # Seed Profiles
    owner_profile = Profile(
        id="owner_uid",
        email="owner@wareflow.io",
        display_name="Boss Owner",
        role_id=r_owner.id,
        is_active=True,
    )
    staff_profile = Profile(
        id="staff_uid",
        email="staff@wareflow.io",
        display_name="Floor Worker",
        role_id=r_staff.id,
        is_active=True,
    )
    test_db_session.add_all([owner_profile, staff_profile])
    test_db_session.commit()

    # Seed Product & Retailer
    product = Product(
        id=str(uuid.uuid4()),
        sku="AUDIT-PRD-01",
        name="Premium Basmati 25kg",
        wholesale_price=2000.00,
        cost_price=1600.00,
        reorder_point=10,
        reorder_qty=50,
    )
    retailer = Retailer(
        id=str(uuid.uuid4()),
        name="Metro Wholesale Hub",
        credit_limit=50000.00,
        credit_balance=0.00,
    )
    test_db_session.add_all([product, retailer])
    test_db_session.commit()

    return {
        "session": test_db_session,
        "owner": owner_profile,
        "staff": staff_profile,
        "product": product,
        "retailer": retailer,
        "roles": {"owner": r_owner, "staff": r_staff, "accountant": r_accountant},
        "permissions": {"audit": p_audit, "settings": p_settings, "inventory": p_inventory},
    }


def test_product_price_edit_creates_audit_entry(audit_test_env):
    """Test that editing product price produces an audit record with before/after diff."""
    db_session = audit_test_env["session"]
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    from app.core.security import CurrentUser

    # Simulate Owner caller
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=audit_test_env["owner"].id,
        email=audit_test_env["owner"].email,
        role="Owner",
        permissions={"inventory:manage", "audit:view"},
        display_name=audit_test_env["owner"].display_name,
        is_active=True,
    )

    client = TestClient(app)
    prod_id = audit_test_env["product"].id

    # 1. Update product price
    patch_res = client.patch(
        f"/products/{prod_id}/price",
        json={"wholesale_price": 2450.00, "cost_price": 1750.00},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["wholesale_price"] == 2450.00
    assert data["cost_price"] == 1750.00

    # 2. Query audit log
    audit_res = client.get("/admin/audit-log")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total"] >= 1

    entry = next(e for e in audit_data["items"] if e["entity_id"] == prod_id)
    assert entry["action"] == "product_price_updated"
    assert entry["entity_type"] == "product"
    assert entry["actor_email"] == "owner@wareflow.io"
    assert entry["before_value"]["wholesale_price"] == 2000.00
    assert entry["after_value"]["wholesale_price"] == 2450.00
    assert (
        "changed wholesale price of 'Premium Basmati 25kg' from ₹2,000.00 to ₹2,450.00"
        in entry["description"]
    )


def test_retailer_credit_limit_edit_creates_audit_entry(audit_test_env):
    """Test that modifying a retailer's credit limit generates a clean audit record."""
    db_session = audit_test_env["session"]
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    from app.core.security import CurrentUser

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=audit_test_env["owner"].id,
        email=audit_test_env["owner"].email,
        role="Owner",
        permissions={"settings:manage", "audit:view"},
        display_name=audit_test_env["owner"].display_name,
        is_active=True,
    )

    client = TestClient(app)
    ret_id = audit_test_env["retailer"].id

    # 1. Update credit limit from 50,000 to 75,000
    patch_res = client.patch(
        f"/retailers/{ret_id}/credit-limit",
        json={"credit_limit": 75000.00},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["credit_limit"] == 75000.00

    # 2. Inspect audit entry
    audit_res = client.get("/admin/audit-log?entity_type=retailer")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total"] >= 1

    entry = next(e for e in audit_data["items"] if e["entity_id"] == ret_id)
    assert entry["action"] == "retailer_credit_limit_updated"
    assert entry["before_value"]["credit_limit"] == 50000.00
    assert entry["after_value"]["credit_limit"] == 75000.00
    assert (
        "changed Retailer 'Metro Wholesale Hub' credit limit from ₹50,000.00 to ₹75,000.00"
        in entry["description"]
    )


def test_permission_matrix_edit_creates_audit_entry(audit_test_env):
    """Test that updating role permissions produces an audit entry capturing diff."""
    db_session = audit_test_env["session"]
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    from app.core.security import CurrentUser

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=audit_test_env["owner"].id,
        email=audit_test_env["owner"].email,
        role="Owner",
        permissions={"settings:manage", "audit:view"},
        display_name=audit_test_env["owner"].display_name,
        is_active=True,
    )

    client = TestClient(app)
    role_id = audit_test_env["roles"]["accountant"].id

    # Update Accountant role permissions to add settings:manage
    patch_res = client.patch(
        f"/roles/{role_id}/permissions",
        json={"permission_codes": ["settings:manage", "inventory:manage"]},
    )
    assert patch_res.status_code == 200

    # Check audit entry
    audit_res = client.get("/admin/audit-log?entity_type=role_permissions")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    entry = next(e for e in audit_data["items"] if e["entity_id"] == role_id)
    assert entry["action"] == "role_permissions_updated"
    assert "modified permissions for role 'Accountant'" in entry["description"]


def test_unauthorized_user_cannot_view_audit_log(audit_test_env):
    """Test that non-permitted staff (e.g. Warehouse Staff) receives 403 Forbidden."""
    db_session = audit_test_env["session"]
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    from app.core.security import CurrentUser

    # Simulate Warehouse Staff caller without audit:view
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=audit_test_env["staff"].id,
        email=audit_test_env["staff"].email,
        role="Warehouse Staff",
        permissions={"inventory:view"},
        display_name=audit_test_env["staff"].display_name,
        is_active=True,
    )

    client = TestClient(app)
    res = client.get("/admin/audit-log")
    assert res.status_code == 403
    assert "Missing required permission: audit:view" in res.json()["detail"]
