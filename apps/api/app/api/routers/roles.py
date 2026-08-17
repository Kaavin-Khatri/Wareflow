"""Role and permission matrix configuration router."""

from fastapi import APIRouter, Depends, status

from app.core.di import get_staff_service
from app.core.security import CurrentUser, get_current_user, require_permission
from app.schemas.staff import (
    PermissionSummaryResponse,
    RolePermissionsUpdateRequest,
    RoleSummaryResponse,
)
from app.services.staff_service import StaffService

router = APIRouter(tags=["Roles & Permissions"])


@router.get(
    "/roles",
    response_model=list[RoleSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all roles and their currently granted permissions",
)
def list_system_roles(
    current_user: CurrentUser = Depends(get_current_user),
    service: StaffService = Depends(get_staff_service),
) -> list[RoleSummaryResponse]:
    """Retrieve all roles with granted permission codes."""
    return service.list_roles()


@router.get(
    "/permissions",
    response_model=list[PermissionSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all available granular system permissions",
)
def list_system_permissions(
    current_user: CurrentUser = Depends(get_current_user),
    service: StaffService = Depends(get_staff_service),
) -> list[PermissionSummaryResponse]:
    """Retrieve all defined permission codes and descriptions."""
    return service.list_permissions()


@router.patch(
    "/roles/{role_id}/permissions",
    response_model=RoleSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update permission matrix mappings for a role",
)
def update_role_permissions(
    role_id: str,
    payload: RolePermissionsUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("settings:manage")),
    service: StaffService = Depends(get_staff_service),
) -> RoleSummaryResponse:
    """Modify the permissions granted to a specific role."""
    return service.update_role_permissions(role_id=role_id, data=payload)
