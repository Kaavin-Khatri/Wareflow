"""Automated test suite for TOTP Two-Factor Authentication & Recovery Backup Codes."""

from collections.abc import Generator

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.di import get_profile_repository
from app.db.base import Base
from app.main import create_app
from app.models.auth_rbac import Permission, Role, RolePermission
from app.models.profile import Profile
from app.repositories.impl.profile_repository import SqlAlchemyProfileRepository


@pytest.fixture
def test_db_session() -> Generator[Session, None, None]:
    """In-memory SQLite database session for unit tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    # Seed roles and permissions
    owner_role = Role(id="role_owner_1", name="Owner", description="Business Owner")
    warehouse_role = Role(
        id="role_warehouse_1", name="Warehouse Staff", description="Warehouse Operative"
    )
    session.add_all([owner_role, warehouse_role])
    session.flush()

    p_staff_manage = Permission(id="p1", code="staff:manage", description="Staff Manage")
    p_staff_view = Permission(id="p2", code="staff:view", description="Staff View")
    p_stock_view = Permission(id="p3", code="stock:view", description="Stock View")
    p_settings_manage = Permission(id="p4", code="settings:manage", description="Settings Manage")
    session.add_all([p_staff_manage, p_staff_view, p_stock_view, p_settings_manage])
    session.flush()

    session.add(RolePermission(role_id=owner_role.id, permission_id=p_staff_manage.id))
    session.add(RolePermission(role_id=owner_role.id, permission_id=p_staff_view.id))
    session.add(RolePermission(role_id=owner_role.id, permission_id=p_settings_manage.id))
    session.add(RolePermission(role_id=warehouse_role.id, permission_id=p_stock_view.id))

    # Seed profiles
    owner_profile = Profile(
        id="owner_uid_1",
        email="owner@wareflow.io",
        display_name="Warehouse Owner",
        role_id=owner_role.id,
        is_active=True,
    )
    warehouse_profile = Profile(
        id="warehouse_uid_1",
        email="staff@wareflow.io",
        display_name="Floor Staff",
        role_id=warehouse_role.id,
        is_active=True,
    )
    session.add_all([owner_profile, warehouse_profile])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db_session: Session) -> TestClient:
    """FastAPI TestClient with in-memory repository override."""
    app = create_app()
    app.dependency_overrides[get_profile_repository] = lambda: SqlAlchemyProfileRepository(
        session=test_db_session
    )
    return TestClient(app)


def test_2fa_enrollment_lifecycle(client: TestClient) -> None:
    """Test standard TOTP enrollment, scannable QR generation, and activation."""
    headers = {"Authorization": "Bearer test_token_owner_uid_1"}

    # 1. Check initial status
    res = client.get("/auth/2fa/status", headers=headers)
    assert res.status_code == 200
    status_data = res.json()
    assert status_data["is_enabled"] is False
    assert status_data["is_required"] is True  # Owner role requires 2FA
    assert status_data["remaining_backup_codes"] == 0

    # 2. Initiate enrollment
    enroll_res = client.post("/auth/2fa/enroll", headers=headers)
    assert enroll_res.status_code == 200
    enroll_data = enroll_res.json()
    secret = enroll_data["secret"]
    assert len(secret) == 32
    assert enroll_data["qr_code_data_url"].startswith("data:image/png;base64,")
    assert len(enroll_data["backup_codes"]) == 10

    # 3. Invalid code rejection
    bad_res = client.post(
        "/auth/2fa/verify-enrollment",
        headers=headers,
        json={"code": "000000"},
    )
    assert bad_res.status_code == 400

    # 4. Valid TOTP activation
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    confirm_res = client.post(
        "/auth/2fa/verify-enrollment",
        headers=headers,
        json={"code": valid_code},
    )
    assert confirm_res.status_code == 200
    confirmed_data = confirm_res.json()
    assert confirmed_data["is_enabled"] is True
    assert confirmed_data["remaining_backup_codes"] == 10


def test_2fa_totp_and_single_use_backup_codes(client: TestClient) -> None:
    """Test TOTP code verification and strict single-use consumption of backup recovery codes."""
    headers = {"Authorization": "Bearer test_token_owner_uid_1"}

    # Enroll
    enroll_data = client.post("/auth/2fa/enroll", headers=headers).json()
    secret = enroll_data["secret"]
    backup_codes = enroll_data["backup_codes"]
    first_backup_code = backup_codes[0]

    # Confirm enrollment
    client.post(
        "/auth/2fa/verify-enrollment",
        headers=headers,
        json={"code": pyotp.TOTP(secret).now()},
    )

    # Verify via live TOTP
    verify_res = client.post(
        "/auth/2fa/verify",
        headers=headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True
    assert verify_res.json()["used_backup_code"] is False
    assert verify_res.json()["remaining_backup_codes"] == 10

    # Verify via 1st backup code
    backup_res = client.post(
        "/auth/2fa/verify",
        headers=headers,
        json={"code": first_backup_code},
    )
    assert backup_res.status_code == 200
    assert backup_res.json()["verified"] is True
    assert backup_res.json()["used_backup_code"] is True
    assert backup_res.json()["remaining_backup_codes"] == 9

    # Reusing the EXACT SAME backup code MUST FAIL (single-use invariant)
    reuse_res = client.post(
        "/auth/2fa/verify",
        headers=headers,
        json={"code": first_backup_code},
    )
    assert reuse_res.status_code == 401


def test_2fa_sensitive_route_protection(client: TestClient) -> None:
    """Test that financial/owner routes require 2FA verification for enrolled accounts."""
    headers = {"Authorization": "Bearer test_token_owner_uid_1"}

    # Enroll and activate 2FA
    enroll_data = client.post("/auth/2fa/enroll", headers=headers).json()
    client.post(
        "/auth/2fa/verify-enrollment",
        headers=headers,
        json={"code": pyotp.TOTP(enroll_data["secret"]).now()},
    )

    # Calling /staff (which requires staff:manage) without 2FA verified header gets 403
    unverified_res = client.get("/staff", headers=headers)
    assert unverified_res.status_code == 403
    assert "Two-factor authentication required" in unverified_res.json()["detail"]

    # Calling /staff with X-2FA-Verified header succeeds
    verified_headers = {
        "Authorization": "Bearer test_token_owner_uid_1",
        "X-2FA-Verified": "true",
    }
    verified_res = client.get("/staff", headers=verified_headers)
    assert verified_res.status_code == 200


def test_role_exemption_for_operational_staff(client: TestClient) -> None:
    """Test that Warehouse Staff are exempt by default from mandatory 2FA."""
    staff_headers = {"Authorization": "Bearer test_token_warehouse_uid_1"}

    status_res = client.get("/auth/2fa/status", headers=staff_headers)
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["is_enabled"] is False
    assert data["is_required"] is False  # Exempt by default


def test_disable_and_regenerate_backup_codes(client: TestClient) -> None:
    """Test regenerating recovery backup codes and disabling 2FA."""
    headers = {"Authorization": "Bearer test_token_owner_uid_1"}

    # Enroll and activate
    enroll_data = client.post("/auth/2fa/enroll", headers=headers).json()
    secret = enroll_data["secret"]
    client.post(
        "/auth/2fa/verify-enrollment",
        headers=headers,
        json={"code": pyotp.TOTP(secret).now()},
    )

    # Regenerate backup codes with valid TOTP
    regen_res = client.post(
        "/auth/2fa/regenerate-backup-codes",
        headers=headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert regen_res.status_code == 200
    new_codes = regen_res.json()
    assert len(new_codes) == 10

    # Disable 2FA with valid TOTP
    disable_res = client.post(
        "/auth/2fa/disable",
        headers=headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert disable_res.status_code == 200
    assert disable_res.json()["is_enabled"] is False
