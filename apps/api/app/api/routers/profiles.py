"""Profile and User onboarding API router."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.di import get_profile_service
from app.core.security import get_current_user_claims
from app.schemas.profile import (
    AppearancePreferencesRequest,
    ProfileBootstrapRequest,
    ProfileResponse,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.post(
    "/bootstrap",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Bootstrap or retrieve user profile after Firebase authentication",
)
def bootstrap_profile(
    body: ProfileBootstrapRequest | None = None,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """
    Onboard authenticated Firebase user.

    The first user to sign up is assigned the 'Owner' role.
    Subsequent users must be invited or permitted by system configuration.
    """
    display_name = body.display_name if body and body.display_name else claims.get("name")
    avatar_url = body.avatar_url if body and body.avatar_url else claims.get("picture")
    phone = body.phone if body and body.phone else claims.get("phone_number")
    email = claims.get("email", "")

    return service.bootstrap_user(
        uid=claims["uid"],
        email=email,
        name=display_name,
        avatar=avatar_url,
        phone=phone,
    )


@router.get(
    "/me",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get currently authenticated user's profile and permissions",
)
def get_my_profile(
    claims: dict[str, Any] = Depends(get_current_user_claims),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Retrieve profile and active role permissions for the caller."""
    return service.get_profile(claims["uid"])


@router.patch(
    "/preferences",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update appearance theme mode and accent color preferences",
)
def update_my_preferences(
    body: AppearancePreferencesRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Persist theme mode and accent color to caller's profile."""
    return service.update_appearance_preferences(
        uid=claims["uid"],
        theme_preference=body.theme_preference,
        accent_color=body.accent_color,
    )
