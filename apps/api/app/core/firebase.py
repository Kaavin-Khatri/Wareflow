"""Firebase Admin SDK singleton initialization."""

import logging
from typing import Any

import firebase_admin
from firebase_admin import credentials

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_firebase_app() -> Any:
    """Initialize or retrieve the Firebase Admin application instance."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    settings = get_settings()
    if settings.firebase_service_account_key_path:
        try:
            cred = credentials.Certificate(settings.firebase_service_account_key_path)
            return firebase_admin.initialize_app(cred)
        except Exception as exc:
            logger.warning("Failed to load Firebase service account certificate: %s", exc)

    try:
        return firebase_admin.initialize_app()
    except Exception as exc:
        logger.warning("Firebase Admin default init fallback: %s", exc)
        return None
