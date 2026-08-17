"""Test appearance theme mode and accent color preference persistence."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.di import get_profile_repository
from app.core.security import CurrentUser, get_current_user, get_current_user_claims
from app.db.base import Base
from app.main import create_app
from app.models.auth_rbac import Role
from app.models.profile import Profile
from app.repositories.impl.profile_repository import SqlAlchemyProfileRepository


@pytest.fixture
def db_session():
    """Create isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client_with_mock_user(db_session):
    """Client authenticated as an owner profile."""
    role = Role(id="role-owner", name="Owner", description="Owner")
    db_session.add(role)
    db_session.commit()

    profile = Profile(
        id="test-user-pref",
        email="pref-user@wareflow.io",
        display_name="Preference User",
        role_id=role.id,
        is_active=True,
        theme_preference="system",
        accent_color="violet",
    )
    db_session.add(profile)
    db_session.commit()

    app = create_app()

    mock_user = CurrentUser(
        id="test-user-pref",
        email="pref-user@wareflow.io",
        role="Owner",
        permissions={"settings:view", "settings:manage"},
        display_name="Preference User",
    )
    mock_claims = {
        "uid": "test-user-pref",
        "email": "pref-user@wareflow.io",
        "name": "Preference User",
    }

    app.dependency_overrides[get_profile_repository] = lambda: SqlAlchemyProfileRepository(
        db_session
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_user_claims] = lambda: mock_claims

    with TestClient(app) as test_client:
        yield test_client


def test_get_me_returns_appearance_preferences(client_with_mock_user):
    """Verify /me returns default appearance preferences."""
    response = client_with_mock_user.get("/me")
    assert response.status_code == 200
    data = response.json()
    assert data["theme_preference"] == "system"
    assert data["accent_color"] == "violet"


def test_update_appearance_preferences_success(client_with_mock_user):
    """Verify PATCH /profiles/preferences updates theme and accent color."""
    payload = {
        "theme_preference": "dark",
        "accent_color": "emerald",
    }
    response = client_with_mock_user.patch("/profiles/preferences", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["theme_preference"] == "dark"
    assert data["accent_color"] == "emerald"

    # Confirm /me returns the updated preferences
    me_resp = client_with_mock_user.get("/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["theme_preference"] == "dark"
    assert me_resp.json()["accent_color"] == "emerald"


def test_update_appearance_preferences_invalid_theme_fails(client_with_mock_user):
    """Verify invalid theme values are rejected with 400."""
    payload = {
        "theme_preference": "neon-rainbow",
        "accent_color": "violet",
    }
    response = client_with_mock_user.patch("/profiles/preferences", json=payload)
    assert response.status_code == 400
    assert "Invalid theme preference" in response.json()["detail"]


def test_update_appearance_preferences_invalid_accent_fails(client_with_mock_user):
    """Verify invalid accent colors outside curated set are rejected with 400."""
    payload = {
        "theme_preference": "dark",
        "accent_color": "hotpink_untested",
    }
    response = client_with_mock_user.patch("/profiles/preferences", json=payload)
    assert response.status_code == 400
    assert "Invalid accent color" in response.json()["detail"]
