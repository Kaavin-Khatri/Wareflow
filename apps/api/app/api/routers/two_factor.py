"""Two-factor authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.di import get_profile_repository, get_two_factor_service
from app.core.security import CurrentUser, get_current_user
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.schemas.two_factor import (
    TwoFactorDisableRequest,
    TwoFactorEnrollResponse,
    TwoFactorStatusResponse,
    TwoFactorVerifyEnrollmentRequest,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
)
from app.services.two_factor_service import TwoFactorService

router = APIRouter(prefix="/auth/2fa", tags=["Two-Factor Authentication"])


@router.get("/status", response_model=TwoFactorStatusResponse)
def get_two_factor_status(
    current_user: CurrentUser = Depends(get_current_user),
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
) -> TwoFactorStatusResponse:
    """Retrieve 2FA status, requirement policy, and remaining backup code count."""
    profile = profile_repo.get_by_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return two_factor_service.get_status(profile)


@router.post("/enroll", response_model=TwoFactorEnrollResponse)
def enroll_two_factor(
    current_user: CurrentUser = Depends(get_current_user),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
) -> TwoFactorEnrollResponse:
    """Generate a new TOTP secret, QR code, and 10 single-use recovery backup codes."""
    return two_factor_service.enroll(profile_id=current_user.id)


@router.post("/verify-enrollment", response_model=TwoFactorStatusResponse)
def verify_enrollment(
    payload: TwoFactorVerifyEnrollmentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
) -> TwoFactorStatusResponse:
    """Confirm TOTP enrollment with first 6-digit code and activate 2FA."""
    return two_factor_service.verify_enrollment(profile_id=current_user.id, code=payload.code)


@router.post("/verify", response_model=TwoFactorVerifyResponse)
def verify_two_factor_challenge(
    payload: TwoFactorVerifyRequest,
    current_user: CurrentUser = Depends(get_current_user),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
) -> TwoFactorVerifyResponse:
    """Verify 2FA challenge via TOTP 6-digit code or single-use backup code."""
    return two_factor_service.verify_challenge(profile_id=current_user.id, code=payload.code)


@router.post("/disable", response_model=TwoFactorStatusResponse)
def disable_two_factor(
    payload: TwoFactorDisableRequest,
    current_user: CurrentUser = Depends(get_current_user),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
) -> TwoFactorStatusResponse:
    """Disable two-factor authentication after validating verification code."""
    return two_factor_service.disable(profile_id=current_user.id, code=payload.code)


@router.post("/regenerate-backup-codes", response_model=list[str])
def regenerate_backup_codes(
    payload: TwoFactorVerifyEnrollmentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
) -> list[str]:
    """Generate 10 fresh backup recovery codes after validating live TOTP."""
    return two_factor_service.regenerate_backup_codes(profile_id=current_user.id, code=payload.code)
