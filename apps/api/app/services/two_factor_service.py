"""Two-factor authentication business logic service (RFC 6238 TOTP + recovery backup codes)."""

import base64
import io
import json
import secrets
from typing import ClassVar

import pyotp
import qrcode
from fastapi import HTTPException, status

from app.core.crypto import decrypt_secret, encrypt_secret
from app.models.profile import Profile
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.schemas.two_factor import (
    TwoFactorEnrollResponse,
    TwoFactorStatusResponse,
    TwoFactorVerifyResponse,
)


class TwoFactorService:
    """Orchestrates TOTP enrollment, validation, and single-use backup recovery."""

    # Roles requiring mandatory two-factor authentication (financial/administrative)
    REQUIRED_ROLES: ClassVar[set[str]] = {"Owner", "Manager", "Accountant"}

    def __init__(self, profile_repo: ProfileRepository) -> None:
        self._profile_repo = profile_repo

    def is_2fa_required_for_role(self, role_name: str, permissions: set[str] | None = None) -> bool:
        """Determine if 2FA is required based on role or sensitive permissions."""
        if role_name in self.REQUIRED_ROLES:
            return True
        if permissions:
            sensitive = {
                "accounting.manage",
                "purchasing.manage",
                "settings.manage",
                "owner.manage",
            }
            if bool(permissions.intersection(sensitive)):
                return True
        return False

    def get_status(self, profile: Profile) -> TwoFactorStatusResponse:
        """Compute current 2FA state, requirement policy, and remaining backup codes."""
        role_name = profile.role.name if profile.role else "Unknown"
        is_required = self.is_2fa_required_for_role(role_name)

        remaining_codes = 0
        if profile.backup_codes_encrypted:
            try:
                decrypted = decrypt_secret(profile.backup_codes_encrypted)
                remaining_codes = len(json.loads(decrypted))
            except Exception:
                remaining_codes = 0

        return TwoFactorStatusResponse(
            is_enabled=profile.totp_enabled,
            is_required=is_required,
            enrolled_at=profile.totp_enrolled_at,
            remaining_backup_codes=remaining_codes,
        )

    def enroll(self, profile_id: str) -> TwoFactorEnrollResponse:
        """Initiate TOTP enrollment: generate secret, QR Code Data URL, and 10 backup codes."""
        profile = self._profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

        # 1. Generate base32 TOTP secret
        secret = pyotp.random_base32()

        # 2. Build provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=profile.email, issuer_name="WareFlow Wholesale"
        )

        # 3. Generate PNG QR code
        qr = qrcode.QRCode(version=1, box_size=8, border=3)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_data_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

        # 4. Generate 10 single-use 8-character backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # 5. Encrypt secret & backup codes at rest
        encrypted_secret = encrypt_secret(secret)
        encrypted_codes = encrypt_secret(json.dumps(backup_codes))

        # 6. Save on profile with totp_enabled = False until confirmed
        self._profile_repo.update_two_factor(
            profile_id=profile.id,
            totp_secret_encrypted=encrypted_secret,
            totp_enabled=False,
            backup_codes_encrypted=encrypted_codes,
        )

        return TwoFactorEnrollResponse(
            secret=secret,
            qr_code_data_url=qr_data_url,
            backup_codes=backup_codes,
        )

    def verify_enrollment(self, profile_id: str, code: str) -> TwoFactorStatusResponse:
        """Confirm enrollment by validating the user's first 6-digit TOTP code."""
        profile = self._profile_repo.get_by_id(profile_id)
        if not profile or not profile.totp_secret_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enrollment not initiated. Please start enrollment first.",
            )

        secret = decrypt_secret(profile.totp_secret_encrypted)
        totp = pyotp.TOTP(secret)

        if not totp.verify(code.strip(), valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 6-digit verification code. Please check your authenticator app clock.",
            )

        # Enable 2FA
        updated = self._profile_repo.update_two_factor(
            profile_id=profile.id,
            totp_secret_encrypted=profile.totp_secret_encrypted,
            totp_enabled=True,
            backup_codes_encrypted=profile.backup_codes_encrypted,
        )
        return self.get_status(updated or profile)

    def verify_challenge(self, profile_id: str, code: str) -> TwoFactorVerifyResponse:
        """Verify 2FA during sign-in using either a 6-digit TOTP code or single-use backup code."""
        profile = self._profile_repo.get_by_id(profile_id)
        if not profile or not profile.totp_enabled or not profile.totp_secret_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Two-factor authentication is not enabled for this account.",
            )

        cleaned_code = code.strip().replace("-", "").replace(" ", "").upper()

        # 1. Try TOTP 6-digit verification
        secret = decrypt_secret(profile.totp_secret_encrypted)
        totp = pyotp.TOTP(secret)
        if totp.verify(cleaned_code, valid_window=1):
            remaining_count = self._get_remaining_backup_count(profile)
            return TwoFactorVerifyResponse(
                verified=True,
                used_backup_code=False,
                remaining_backup_codes=remaining_count,
                message="Two-factor authentication verified successfully.",
            )

        # 2. Try single-use backup code
        if profile.backup_codes_encrypted:
            try:
                backup_codes: list[str] = json.loads(decrypt_secret(profile.backup_codes_encrypted))
                if cleaned_code in backup_codes:
                    # Atomic consumption: remove used code
                    backup_codes.remove(cleaned_code)
                    new_encrypted = encrypt_secret(json.dumps(backup_codes))
                    self._profile_repo.update_backup_codes(profile.id, new_encrypted)
                    return TwoFactorVerifyResponse(
                        verified=True,
                        used_backup_code=True,
                        remaining_backup_codes=len(backup_codes),
                        message=f"Verified via backup code. {len(backup_codes)} recovery codes remaining.",
                    )
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 6-digit authenticator code or recovery backup code.",
        )

    def disable(self, profile_id: str, code: str) -> TwoFactorStatusResponse:
        """Disable two-factor authentication after verifying a valid code."""
        # Verify code first
        self.verify_challenge(profile_id, code)

        # Clear credentials
        updated = self._profile_repo.update_two_factor(
            profile_id=profile_id,
            totp_secret_encrypted=None,
            totp_enabled=False,
            backup_codes_encrypted=None,
        )
        return self.get_status(updated or self._profile_repo.get_by_id(profile_id))

    def regenerate_backup_codes(self, profile_id: str, code: str) -> list[str]:
        """Regenerate 10 new backup recovery codes after validating current TOTP."""
        profile = self._profile_repo.get_by_id(profile_id)
        if not profile or not profile.totp_enabled or not profile.totp_secret_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Two-factor authentication is not active.",
            )

        # Verify live code
        secret = decrypt_secret(profile.totp_secret_encrypted)
        totp = pyotp.TOTP(secret)
        if not totp.verify(code.strip(), valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 6-digit TOTP code.",
            )

        # Generate 10 new codes
        new_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        encrypted = encrypt_secret(json.dumps(new_codes))
        self._profile_repo.update_backup_codes(profile_id, encrypted)
        return new_codes

    def _get_remaining_backup_count(self, profile: Profile) -> int:
        """Count remaining unused backup codes."""
        if not profile.backup_codes_encrypted:
            return 0
        try:
            codes = json.loads(decrypt_secret(profile.backup_codes_encrypted))
            return len(codes)
        except Exception:
            return 0
