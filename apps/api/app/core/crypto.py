"""Symmetric encryption utilities for sensitive data at rest (TOTP secrets & backup codes)."""

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet

from app.core.config import get_settings


@lru_cache
def _get_fernet() -> Fernet:
    """Derive a 32-byte urlsafe Fernet key from application settings."""
    settings = get_settings()
    seed = (
        settings.totp_encryption_key
        or settings.supabase_service_role_key
        or "wareflow-default-encryption-salt-2026"
    )
    # Derive deterministic 32-byte key via SHA-256
    derived_bytes = hashlib.sha256(seed.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(derived_bytes)
    return Fernet(fernet_key)


def encrypt_secret(plain_text: str) -> str:
    """Encrypt plaintext string into a Fernet base64 token."""
    if not plain_text:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_text: str) -> str:
    """Decrypt a Fernet token back into plaintext."""
    if not encrypted_text:
        return ""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
