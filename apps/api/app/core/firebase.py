import logging
import os
from pathlib import Path
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
    candidate_paths = [
        settings.firebase_service_account_key_path,
        os.path.join(os.getcwd(), "serviceAccountKey.json"),
        str(Path(__file__).resolve().parents[3] / "serviceAccountKey.json"),
    ]

    for path in candidate_paths:
        if path and os.path.exists(path):
            try:
                cred = credentials.Certificate(path)
                return firebase_admin.initialize_app(cred)
            except Exception as exc:
                logger.warning(
                    "Failed to load Firebase service account certificate from %s: %s", path, exc
                )

    try:
        return firebase_admin.initialize_app()
    except Exception as exc:
        logger.warning("Firebase Admin default init fallback: %s", exc)
        return None
