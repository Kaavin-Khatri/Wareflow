"""Staff management and role assignment router."""

from fastapi import APIRouter, Depends, status

from app.core.di import get_staff_service
from app.core.security import CurrentUser, require_permission
from app.schemas.staff import (
    StaffInviteRequest,
    StaffInviteResponse,
    StaffMemberResponse,
    StaffRoleUpdateRequest,
    StaffStatusUpdateRequest,
)
from app.services.staff_service import StaffService

router = APIRouter(prefix="/staff", tags=["Staff Management"])


@router.post(
    "/invite",
    response_model=StaffInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a new staff member with a designated role",
)
def invite_staff_member(
    payload: StaffInviteRequest,
    current_user: CurrentUser = Depends(require_permission("staff:manage")),
    service: StaffService = Depends(get_staff_service),
) -> StaffInviteResponse:
    """Invite staff member by creating auth credentials and database profile."""
    return service.invite_staff(payload)


@router.get(
    "",
    response_model=list[StaffMemberResponse],
    status_code=status.HTTP_200_OK,
    summary="List all staff members and their roles",
)
def list_staff_members(
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentUser = Depends(require_permission("staff:view")),
    service: StaffService = Depends(get_staff_service),
) -> list[StaffMemberResponse]:
    """Retrieve all staff profiles and their current roles."""
    return service.list_staff(skip=skip, limit=limit)


@router.patch(
    "/{profile_id}/role",
    response_model=StaffMemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a staff member's assigned role",
)
def change_staff_role(
    profile_id: str,
    payload: StaffRoleUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("staff:manage")),
    service: StaffService = Depends(get_staff_service),
) -> StaffMemberResponse:
    """Reassign staff member to a different system role."""
    return service.update_staff_role(profile_id=profile_id, data=payload, actor_id=current_user.id)


@router.patch(
    "/{profile_id}/status",
    response_model=StaffMemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle staff member active status",
)
def change_staff_status(
    profile_id: str,
    payload: StaffStatusUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("staff:manage")),
    service: StaffService = Depends(get_staff_service),
) -> StaffMemberResponse:
    """Activate or deactivate a staff member account."""
    return service.update_staff_status(
        profile_id=profile_id, data=payload, actor_id=current_user.id
    )
