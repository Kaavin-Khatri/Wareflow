"""Current user profile and permission inspection router."""

from fastapi import APIRouter, Depends, status

from app.core.di import get_profile_service
from app.core.security import CurrentUser, get_current_user
from app.schemas.profile import ProfileResponse
from app.services.profile_service import ProfileService

router = APIRouter(tags=["Auth & Identity"])


@router.get(
    "/me",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get caller profile and active permissions",
)
def get_caller_identity(
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Retrieve full profile details, role, and permission codes for the caller."""
    return service.get_profile(current_user.id)
