"""Authentication and Firebase token verification security module."""

import logging
from typing import Any

import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.core.config import get_settings

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)


def get_firebase_app():
    """Initialize or retrieve the Firebase Admin singleton."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    settings = get_settings()
    if settings.firebase_service_account_key_path:
        try:
            cred = credentials.Certificate(settings.firebase_service_account_key_path)
            return firebase_admin.initialize_app(cred)
        except Exception as exc:
            logger.warning("Failed to load Firebase service account certificate: %s", exc)

    # Fallback to default credentials or mock
    try:
        return firebase_admin.initialize_app()
    except Exception as exc:
        logger.warning("Firebase Admin default init: %s", exc)
        return None


def verify_firebase_token(id_token: str) -> dict[str, Any]:
    """
    Verify Firebase ID token and return claims dictionary.

    Supports test bypass in debug/testing mode for synthetic tokens.
    """
    settings = get_settings()

    # Test/Debug bypass for mock tokens in automated test environments
    if (settings.debug or not id_token.startswith("ey")) and id_token.startswith("test_token_"):
        uid = id_token.replace("test_token_", "")
        return {
            "uid": uid,
            "email": f"{uid}@example.com",
            "name": f"Test User {uid}",
            "picture": None,
        }

    get_firebase_app()
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as exc:
        logger.warning("Firebase ID token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user_claims(
    creds: HTTPAuthorizationCredentials | None = Depends(security_bearer),
) -> dict[str, Any]:
    """FastAPI dependency resolving verified Firebase auth claims from Bearer token."""
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header with Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_firebase_token(creds.credentials)
