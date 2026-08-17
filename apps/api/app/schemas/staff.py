"""Pydantic schemas for Staff management, Role assignments, and Permission matrices."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class StaffInviteRequest(BaseModel):
    """Payload to invite a new staff member."""

    email: EmailStr
    role_id: str
    display_name: str | None = None
    phone: str | None = None


class StaffInviteResponse(BaseModel):
    """Response returned when a staff invitation is created."""

    id: str
    email: str
    role_name: str
    sign_in_link: str | None = None
    message: str


class StaffMemberResponse(BaseModel):
    """Staff member profile and role details."""

    id: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    role_id: str
    role_name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffRoleUpdateRequest(BaseModel):
    """Payload to modify staff member's role."""

    role_id: str


class StaffStatusUpdateRequest(BaseModel):
    """Payload to toggle staff member's active status."""

    is_active: bool


class PermissionSummaryResponse(BaseModel):
    """Granular permission code definition."""

    id: str
    code: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RoleSummaryResponse(BaseModel):
    """Role and its currently assigned permission codes."""

    id: str
    name: str
    description: str | None = None
    permissions: list[str]

    model_config = ConfigDict(from_attributes=True)


class RolePermissionsUpdateRequest(BaseModel):
    """Payload to batch-update assigned permission codes for a role."""

    permission_codes: list[str]
