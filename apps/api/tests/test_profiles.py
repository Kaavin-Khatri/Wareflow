"""Automated tests for Profile bootstrapping, Owner assignment, and permissions (Step 3.1)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 Ensure all models are registered in Base.metadata
from app.core.di import get_profile_repository
from app.db.base import Base
from app.main import create_app
from app.models import Permission, Role, RolePermission
from app.repositories.impl.profile_repository import SqlAlchemyProfileRepository


@pytest.fixture
def db_session():
    """Create isolated SQLite database session with seed roles."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()

    # Seed Owner and Staff roles with permissions
    owner_role = Role(name="Owner", description="Root account")
    perm1 = Permission(code="inventory:view", description="View stock")
    perm2 = Permission(code="settings:manage", description="Manage settings")
    session.add_all([owner_role, perm1, perm2])
    session.flush()

    rp1 = RolePermission(role_id=owner_role.id, permission_id=perm1.id)
    rp2 = RolePermission(role_id=owner_role.id, permission_id=perm2.id)
    session.add_all([rp1, rp2])
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session):
    """FastAPI test client with profile repository injected to SQLite session."""
    app = create_app()

    def override_profile_repo():
        return SqlAlchemyProfileRepository(session=db_session)

    app.dependency_overrides[get_profile_repository] = override_profile_repo
    return TestClient(app)


def test_first_user_bootstraps_as_owner(client: TestClient):
    """The very first user to authenticate receives the Owner role with root permissions."""
    headers = {"Authorization": "Bearer test_token_uid_admin_001"}
    payload = {"display_name": "Rajesh Owner", "phone": "+919820000001"}

    response = client.post("/profiles/bootstrap", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "uid_admin_001"
    assert data["email"] == "uid_admin_001@example.com"
    assert data["display_name"] == "Rajesh Owner"
    assert data["role_name"] == "Owner"
    assert "inventory:view" in data["permissions"]
    assert "settings:manage" in data["permissions"]
    assert data["is_active"] is True


def test_bootstrap_is_idempotent(client: TestClient):
    """Calling bootstrap again for the same user returns existing profile without duplicate errors."""
    headers = {"Authorization": "Bearer test_token_uid_admin_002"}

    # First call
    res1 = client.post("/profiles/bootstrap", json={"display_name": "Alice"}, headers=headers)
    assert res1.status_code == 200

    # Second call
    res2 = client.post(
        "/profiles/bootstrap", json={"display_name": "Alice Modified"}, headers=headers
    )
    assert res2.status_code == 200
    assert res2.json()["id"] == "uid_admin_002"
    assert res2.json()["role_name"] == "Owner"


def test_get_my_profile(client: TestClient):
    """GET /profiles/me returns profile details for authenticated user."""
    headers = {"Authorization": "Bearer test_token_uid_admin_003"}
    _ = client.post("/profiles/bootstrap", json={"display_name": "Suresh"}, headers=headers)

    me_res = client.get("/profiles/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == "uid_admin_003"
    assert me_data["role_name"] == "Owner"


def test_unauthenticated_request_fails(client: TestClient):
    """Missing or invalid token returns 401 Unauthorized."""
    res = client.get("/profiles/me")
    assert res.status_code == 401
