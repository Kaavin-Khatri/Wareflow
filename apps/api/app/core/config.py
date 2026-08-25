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
    frontend_url: str = "http://localhost:3000"

    # Supabase / Postgres
    database_url: str = ""
    direct_database_url: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Firebase
    firebase_service_account_key_path: str = ""

    # Resend
    resend_api_key: str = ""

    # Groq (Step 0.3 / Step 14.3)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    insight_cache_ttl_days: int = 7
    anomaly_stddev_multiplier: float = 3.0

    # Security & 2FA
    totp_encryption_key: str = ""

    # GST Compliance & E-Invoicing (Step 10.3)
    einvoice_enabled: bool = False
    gsp_provider: str = "sandbox"
    gsp_api_key: str = ""
    gsp_api_secret: str = ""
    eway_bill_threshold_inr: float = 50000.0

    # WhatsApp (Meta Cloud API — Step 13.3)
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_api_version: str = "v21.0"

    # SMS Fallback Channel (Step 13.6)
    sms_provider: str = "twilio"
    sms_provider_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # Demand Forecasting (Step 14.1)
    forecast_strategy: str = "moving_average"  # 'moving_average' | 'exponential_smoothing'
    forecast_cache_ttl_hours: int = 24

    # Google Places Lead Scanner (Step 17.1)
    google_places_api_key: str = ""
    lead_scan_interval_days: int = 7
    lead_scan_center_lat: float = 23.0119
    lead_scan_center_lng: float = 72.5381
    lead_scan_radius_km: float = 15.0

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
