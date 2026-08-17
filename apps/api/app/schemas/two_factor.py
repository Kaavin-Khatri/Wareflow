"""Two-factor authentication schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class TwoFactorEnrollResponse(BaseModel):
    """Response payload for 2FA enrollment initiation."""

    secret: str = Field(..., description="Base32 TOTP secret for manual app configuration")
    qr_code_data_url: str = Field(
        ..., description="Data URL containing PNG QR code image scannable by authenticator apps"
    )
    backup_codes: list[str] = Field(
        ..., description="10 single-use 8-character recovery backup codes"
    )


class TwoFactorVerifyEnrollmentRequest(BaseModel):
    """Request payload to confirm enrollment with first 6-digit TOTP code."""

    code: str = Field(..., min_length=6, max_length=8, description="6-digit TOTP validation code")


class TwoFactorVerifyRequest(BaseModel):
    """Request payload to verify 2FA challenge during login."""

    code: str = Field(
        ..., min_length=6, max_length=12, description="6-digit TOTP or 8-character backup code"
    )


class TwoFactorDisableRequest(BaseModel):
    """Request payload to disable two-factor authentication."""

    code: str = Field(
        ..., min_length=6, max_length=12, description="Verification code to confirm disable"
    )


class TwoFactorStatusResponse(BaseModel):
    """Status payload representing 2FA enrollment and policy state."""

    is_enabled: bool
    is_required: bool
    enrolled_at: datetime | None = None
    remaining_backup_codes: int = 0


class TwoFactorVerifyResponse(BaseModel):
    """Response payload after successful 2FA verification."""

    verified: bool = True
    used_backup_code: bool = False
    remaining_backup_codes: int = 0
    message: str = "Two-factor authentication verified successfully"
