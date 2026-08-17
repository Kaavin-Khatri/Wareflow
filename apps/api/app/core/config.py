"""Application configuration — loaded from environment variables via pydantic-settings."""

import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised config. All values come from env vars or .env file."""

    # App
    app_name: str = "WareFlow API"
    debug: bool = False
    allow_first_signup: bool = True
    allowed_origins: list[str] | str = ["http://localhost:3000"]

    # Supabase / Postgres
    database_url: str = ""
    direct_database_url: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Firebase
    firebase_service_account_key_path: str = ""

    # Resend
    resend_api_key: str = ""

    # Groq
    groq_api_key: str = ""

    # Security & 2FA
    totp_encryption_key: str = ""

    @field_validator("allowed_origins", mode="after")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        """Support comma-separated strings or JSON arrays in env vars."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return list(value)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Factory function for dependency injection of settings."""
    return Settings()
