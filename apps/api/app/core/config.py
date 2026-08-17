"""Application configuration — loaded from environment variables via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised config. All values come from env vars or .env file."""

    # App
    app_name: str = "WareFlow API"
    debug: bool = False

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Factory function for dependency injection of settings."""
    return Settings()
