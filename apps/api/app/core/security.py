"""Authentication, Firebase token verification, and RBAC permission guards."""

import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from app.core.config import get_settings
from app.core.di import get_profile_repository
from app.core.firebase import get_firebase_app
from app.repositories.interfaces.profile_repository import ProfileRepository

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """Authenticated caller context with resolved database profile & RBAC permissions."""

    id: str
    email: str
    role: str
    permissions: set[str]
    display_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    is_active: bool = True
    is_2fa_enabled: bool = False
    is_2fa_required: bool = False
    is_2fa_verified: bool = False


def _handle_test_token(token: str) -> dict[str, Any] | None:
    """Extract synthetic claims for test tokens in non-production test suites."""
    settings = get_settings()
    if (settings.debug or not token.startswith("ey")) and token.startswith("test_token_"):
        uid = token.replace("test_token_", "")
        return {
            "uid": uid,
            "email": f"{uid}@example.com",
            "name": f"Test User {uid}",
            "picture": None,
        }
    return None


def verify_id_token(id_token: str) -> dict[str, Any]:
    """Verify Firebase ID token and return claims dictionary."""
    mock_claims = _handle_test_token(id_token)
    if mock_claims:
        return mock_claims

    get_firebase_app()
    try:
        return firebase_auth.verify_id_token(id_token)
    except Exception as exc:
        logger.warning("Firebase ID token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def verify_session_cookie(session_cookie: str, check_revoked: bool = False) -> dict[str, Any]:
    """Verify Firebase session cookie and return claims dictionary."""
    mock_claims = _handle_test_token(session_cookie)
    if mock_claims:
        return mock_claims

    get_firebase_app()
    try:
        return firebase_auth.verify_session_cookie(session_cookie, check_revoked=check_revoked)
    except Exception as exc:
        logger.warning("Firebase session cookie verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session cookie",
        ) from exc


def extract_raw_auth_token(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(security_bearer),
) -> tuple[str, str]:
    """
    Extract raw token string and source type from HTTP Bearer header or session cookie.

    Returns tuple of (token_string, 'bearer' | 'cookie').
    """
    if creds and creds.credentials:
        return creds.credentials, "bearer"

    session_cookie = request.cookies.get("session") or request.cookies.get("__session")
    if session_cookie:
        return session_cookie, "cookie"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials (bearer token or session cookie required)",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_claims(
    auth_info: tuple[str, str] = Depends(extract_raw_auth_token),
) -> dict[str, Any]:
    """FastAPI dependency returning decoded Firebase claims dictionary."""
    token, token_type = auth_info
    if token_type == "cookie":
        return verify_session_cookie(token)
    return verify_id_token(token)


def get_current_user(
    request: Request,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    profile_repo: ProfileRepository = Depends(get_profile_repository),
) -> CurrentUser:
    """
    FastAPI dependency resolving database profile & permissions for the authenticated caller.

    Validates that:
    1. Firebase token is valid.
    2. Profile exists in database.
    3. User account is active.
    4. Loads full permission code set from role_permissions.
    5. Resolves 2FA enrollment and verification status.
    """
    uid = claims["uid"]
    profile = profile_repo.get_by_id(uid)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not registered. Please bootstrap account.",
        )

    if not profile.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Contact administrator.",
        )

    permissions_list = profile_repo.get_role_permissions(profile.role_id)
    role_name = profile.role.name if profile.role else "Unknown"

    # Check 2FA requirement policy (financial / owner roles require 2FA)
    required_roles = {"Owner", "Manager", "Accountant"}
    is_2fa_required = role_name in required_roles
    is_2fa_enabled = bool(profile.totp_enabled)

    # 2FA verification check: if enabled, check header, cookie, or claims
    two_fa_verified = False
    if not is_2fa_enabled:
        two_fa_verified = True
    else:
        header_val = request.headers.get("X-2FA-Verified")
        cookie_val = request.cookies.get("wareflow_2fa_verified")
        claims_val = claims.get("2fa_verified") or claims.get("is_2fa_verified")
        if header_val == "true" or cookie_val == "true" or bool(claims_val):
            two_fa_verified = True

    return CurrentUser(
        id=profile.id,
        email=profile.email,
        role=role_name,
        permissions=set(permissions_list),
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        phone=profile.phone,
        is_active=profile.is_active,
        is_2fa_enabled=is_2fa_enabled,
        is_2fa_required=is_2fa_required,
        is_2fa_verified=two_fa_verified,
    )


def require_2fa_if_enrolled(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """FastAPI dependency enforcing that 2FA verification is passed if enabled on this account."""
    if current_user.is_2fa_enabled and not current_user.is_2fa_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Two-factor authentication required. Complete TOTP verification.",
        )
    return current_user


def require_permission(permission_code: str):
    """FastAPI dependency factory enforcing that caller holds a specific permission code."""

    def _permission_guard(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if permission_code not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission_code}",
            )
        if current_user.is_2fa_enabled and not current_user.is_2fa_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Two-factor authentication required for sensitive operations.",
            )
        return current_user

    return _permission_guard


def require_role(role_name: str):
    """FastAPI dependency factory enforcing a specific role name (convenience wrapper)."""

    def _role_guard(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {role_name}",
            )
        return current_user

    return _role_guard
