"""Automated tests for Staff management, Role assignment, and Permission Matrix (Step 3.3)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.di import get_profile_repository
from app.db.base import Base
from app.db.session import get_db_session
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
    manager_role = Role(name="Manager", description="Operations")
    staff_role = Role(name="Warehouse Staff", description="Warehouse operations")
    session.add_all([owner_role, manager_role, staff_role])
    session.flush()

    # Create Permissions
    p_inv_view = Permission(code="inventory:view", description="View stock")
    p_inv_manage = Permission(code="inventory:manage", description="Manage stock")
    p_staff_view = Permission(code="staff:view", description="View staff")
    p_staff_manage = Permission(code="staff:manage", description="Manage staff")
    p_settings_manage = Permission(code="settings:manage", description="Manage settings")
    session.add_all([p_inv_view, p_inv_manage, p_staff_view, p_staff_manage, p_settings_manage])
    session.flush()

    # Role Permissions
    session.add_all(
        [
            RolePermission(role_id=owner_role.id, permission_id=p_inv_view.id),
            RolePermission(role_id=owner_role.id, permission_id=p_inv_manage.id),
            RolePermission(role_id=owner_role.id, permission_id=p_staff_view.id),
            RolePermission(role_id=owner_role.id, permission_id=p_staff_manage.id),
            RolePermission(role_id=owner_role.id, permission_id=p_settings_manage.id),
            # Staff role only has inventory:view
            RolePermission(role_id=staff_role.id, permission_id=p_inv_view.id),
        ]
    )

    # Seed Profiles
    owner_profile = Profile(
        id="uid_owner_1",
        email="owner@wareflow.com",
        display_name="Owner User",
        role_id=owner_role.id,
        is_active=True,
    )
    staff_profile = Profile(
        id="uid_staff_1",
        email="staff@wareflow.com",
        display_name="Warehouse Staff 1",
        role_id=staff_role.id,
        is_active=True,
    )
    session.add_all([owner_profile, staff_profile])
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_app(db_session: Session) -> FastAPI:
    """Create test FastAPI application with injected profile repository and test db session."""
    app = create_app()

    def override_profile_repo():
        return SqlAlchemyProfileRepository(session=db_session)

    app.dependency_overrides[get_profile_repository] = override_profile_repo
    app.dependency_overrides[get_db_session] = lambda: db_session
    return app



@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


def test_owner_can_invite_staff(client: TestClient, db_session: Session):
    """Owner invites a new staff member, creating profile with specified role."""
    headers = {"Authorization": "Bearer test_token_uid_owner_1"}
    staff_role = db_session.query(Role).filter(Role.name == "Warehouse Staff").first()

    payload = {
        "email": "new.picker@wareflow.com",
        "role_id": staff_role.id,
        "display_name": "New Picker",
        "phone": "+919876543210",
    }
    response = client.post("/staff/invite", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new.picker@wareflow.com"
    assert data["role_name"] == "Warehouse Staff"
    assert "invited successfully" in data["message"]

    # Verify profile in DB
    invited_profile = (
        db_session.query(Profile).filter(Profile.email == "new.picker@wareflow.com").first()
    )
    assert invited_profile is not None
    assert invited_profile.role_id == staff_role.id


def test_non_owner_cannot_invite_staff(client: TestClient, db_session: Session):
    """Staff member without staff:manage gets 403 Forbidden."""
    headers = {"Authorization": "Bearer test_token_uid_staff_1"}
    staff_role = db_session.query(Role).filter(Role.name == "Warehouse Staff").first()

    payload = {
        "email": "unauthorized@wareflow.com",
        "role_id": staff_role.id,
    }
    response = client.post("/staff/invite", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Missing required permission: staff:manage" in response.json()["detail"]


def test_cannot_invite_duplicate_email(client: TestClient, db_session: Session):
    """Attempting to invite existing email returns 400 Bad Request."""
    headers = {"Authorization": "Bearer test_token_uid_owner_1"}
    staff_role = db_session.query(Role).filter(Role.name == "Warehouse Staff").first()

    payload = {
        "email": "owner@wareflow.com",
        "role_id": staff_role.id,
    }
    response = client.post("/staff/invite", json=payload, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_list_staff_and_modify_role(client: TestClient, db_session: Session):
    """Owner lists staff and modifies a staff member's role."""
    headers = {"Authorization": "Bearer test_token_uid_owner_1"}

    # List staff
    list_res = client.get("/staff", headers=headers)
    assert list_res.status_code == 200
    staff_list = list_res.json()
    assert len(staff_list) >= 2

    # Change staff_1 to Manager role
    manager_role = db_session.query(Role).filter(Role.name == "Manager").first()
    patch_res = client.patch(
        "/staff/uid_staff_1/role",
        json={"role_id": manager_role.id},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["role_name"] == "Manager"


def test_toggle_staff_status(client: TestClient):
    """Owner deactivates a staff member account."""
    headers = {"Authorization": "Bearer test_token_uid_owner_1"}

    res = client.patch(
        "/staff/uid_staff_1/status",
        json={"is_active": False},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False


def test_permission_matrix_editor(client: TestClient, db_session: Session):
    """Owner reads roles & permissions and dynamically updates role permission matrix."""
    owner_headers = {"Authorization": "Bearer test_token_uid_owner_1"}
    staff_headers = {"Authorization": "Bearer test_token_uid_staff_1"}

    # List roles & permissions
    roles_res = client.get("/roles", headers=owner_headers)
    assert roles_res.status_code == 200
    perms_res = client.get("/permissions", headers=owner_headers)
    assert perms_res.status_code == 200

    staff_role = db_session.query(Role).filter(Role.name == "Warehouse Staff").first()

    # Non-owner cannot modify permissions
    unauth_patch = client.patch(
        f"/roles/{staff_role.id}/permissions",
        json={"permission_codes": ["inventory:view", "inventory:manage"]},
        headers=staff_headers,
    )
    assert unauth_patch.status_code == 403
    assert "Missing required permission: settings:manage" in unauth_patch.json()["detail"]

    # Owner updates Warehouse Staff to have inventory:manage as well
    auth_patch = client.patch(
        f"/roles/{staff_role.id}/permissions",
        json={"permission_codes": ["inventory:view", "inventory:manage"]},
        headers=owner_headers,
    )
    assert auth_patch.status_code == 200
    data = auth_patch.json()
    assert "inventory:manage" in data["permissions"]
    assert "inventory:view" in data["permissions"]
