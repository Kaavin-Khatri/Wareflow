"""Automated tests for Firebase verification, CurrentUser context, and RBAC permission guards (Step 3.2)."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 Ensure all models are registered in Base.metadata
from app.core.di import get_profile_repository
from app.core.security import CurrentUser, require_permission, require_role
from app.db.base import Base
from app.main import create_app
from app.models import Permission, Profile, Role, RolePermission
from app.repositories.impl.profile_repository import SqlAlchemyProfileRepository


@pytest.fixture
def db_session():
    """Create isolated SQLite database session with seed roles, permissions, and profiles."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()

    # Create Roles
    owner_role = Role(name="Owner", description="Root account")
    warehouse_role = Role(name="Warehouse Staff", description="Handles inventory and dispatch")
    session.add_all([owner_role, warehouse_role])
    session.flush()

    # Create Permissions
    p_inv_view = Permission(code="inventory:view", description="View stock")
    p_inv_adjust = Permission(code="inventory:adjust", description="Adjust stock")
    p_inv_create = Permission(code="invoices:create", description="Create invoices")
    p_settings_manage = Permission(code="settings:manage", description="Manage system settings")
    session.add_all([p_inv_view, p_inv_adjust, p_inv_create, p_settings_manage])
    session.flush()

    # Role Permissions
    # Owner gets all
    session.add_all(
        [
            RolePermission(role_id=owner_role.id, permission_id=p_inv_view.id),
            RolePermission(role_id=owner_role.id, permission_id=p_inv_adjust.id),
            RolePermission(role_id=owner_role.id, permission_id=p_inv_create.id),
            RolePermission(role_id=owner_role.id, permission_id=p_settings_manage.id),
        ]
    )
    # Warehouse Staff gets only inventory view & adjust
    session.add_all(
        [
            RolePermission(role_id=warehouse_role.id, permission_id=p_inv_view.id),
            RolePermission(role_id=warehouse_role.id, permission_id=p_inv_adjust.id),
        ]
    )

    # Seed Profiles
    owner_profile = Profile(
        id="uid_owner_101",
        email="owner@wareflow.com",
        display_name="Ramesh Owner",
        role_id=owner_role.id,
        is_active=True,
    )
    warehouse_profile = Profile(
        id="uid_warehouse_202",
        email="picker@wareflow.com",
        display_name="Sunil Warehouse",
        role_id=warehouse_role.id,
        is_active=True,
    )
    inactive_profile = Profile(
        id="uid_inactive_303",
        email="inactive@wareflow.com",
        display_name="Inactive User",
        role_id=warehouse_role.id,
        is_active=False,
    )
    session.add_all([owner_profile, warehouse_profile, inactive_profile])
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app_with_test_routes(db_session: Session) -> FastAPI:
    """Create test FastAPI application containing permission-guarded routes."""
    app = create_app()

    def override_profile_repo():
        return SqlAlchemyProfileRepository(session=db_session)

    app.dependency_overrides[get_profile_repository] = override_profile_repo

    # Add protected sample routes to verify guards
    @app.post("/test-guarded/invoices", status_code=201)
    def create_test_invoice(user: CurrentUser = Depends(require_permission("invoices:create"))):
        return {"status": "created", "created_by": user.id}

    @app.get("/test-guarded/inventory")
    def view_test_inventory(user: CurrentUser = Depends(require_permission("inventory:view"))):
        return {"status": "ok", "viewer": user.id}

    @app.get("/test-guarded/owner-only")
    def test_owner_only_route(user: CurrentUser = Depends(require_role("Owner"))):
        return {"status": "owner_confirmed", "owner_id": user.id}

    return app


@pytest.fixture
def client(app_with_test_routes: FastAPI) -> TestClient:
    return TestClient(app_with_test_routes)


def test_get_me_returns_profile_and_permissions(client: TestClient):
    """GET /me returns user profile, role name, and full permission list."""
    headers = {"Authorization": "Bearer test_token_uid_owner_101"}
    response = client.get("/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "uid_owner_101"
    assert data["email"] == "owner@wareflow.com"
    assert data["display_name"] == "Ramesh Owner"
    assert data["role_name"] == "Owner"
    assert "invoices:create" in data["permissions"]
    assert "inventory:view" in data["permissions"]
    assert "settings:manage" in data["permissions"]


def test_warehouse_staff_hitting_invoicing_route_gets_403_naming_permission(client: TestClient):
    """A Warehouse Staff token hitting an invoicing-only route gets 403 naming missing permission."""
    headers = {"Authorization": "Bearer test_token_uid_warehouse_202"}

    # Warehouse staff CAN view inventory
    inv_res = client.get("/test-guarded/inventory", headers=headers)
    assert inv_res.status_code == 200

    # Warehouse staff CANNOT create invoices
    invoice_res = client.post("/test-guarded/invoices", headers=headers)
    assert invoice_res.status_code == 403
    assert "Missing required permission: invoices:create" in invoice_res.json()["detail"]


def test_owner_role_guard(client: TestClient):
    """require_role('Owner') allows Owner and forbids non-owner with 403."""
    owner_headers = {"Authorization": "Bearer test_token_uid_owner_101"}
    wh_headers = {"Authorization": "Bearer test_token_uid_warehouse_202"}

    # Owner allowed
    owner_res = client.get("/test-guarded/owner-only", headers=owner_headers)
    assert owner_res.status_code == 200
    assert owner_res.json()["status"] == "owner_confirmed"

    # Non-owner forbidden
    wh_res = client.get("/test-guarded/owner-only", headers=wh_headers)
    assert wh_res.status_code == 403
    assert "Requires role: Owner" in wh_res.json()["detail"]


def test_tampered_or_missing_token_returns_401(client: TestClient):
    """Missing or invalid token returns 401 Unauthorized."""
    # No auth header or cookie
    res_no_auth = client.get("/me")
    assert res_no_auth.status_code == 401

    # Unregistered user token
    res_unregistered = client.get("/me", headers={"Authorization": "Bearer test_token_uid_unknown"})
    assert res_unregistered.status_code == 401
    assert "User profile not registered" in res_unregistered.json()["detail"]


def test_session_cookie_auth_handshake(client: TestClient):
    """Inbound session cookie verifies credentials and loads permissions identically to Bearer header."""
    client.cookies.set("session", "test_token_uid_warehouse_202")
    response = client.get("/me")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "uid_warehouse_202"
    assert data["role_name"] == "Warehouse Staff"
    assert "inventory:view" in data["permissions"]
    assert "invoices:create" not in data["permissions"]


def test_inactive_user_is_forbidden(client: TestClient):
    """An inactive user profile is blocked with 403 Forbidden."""
    headers = {"Authorization": "Bearer test_token_uid_inactive_303"}
    res = client.get("/test-guarded/inventory", headers=headers)

    assert res.status_code == 403
    assert "User account is inactive" in res.json()["detail"]
