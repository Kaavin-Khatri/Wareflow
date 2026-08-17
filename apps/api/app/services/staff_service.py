"""Staff management, Role assignment, and Permission matrix service."""

import contextlib
import logging
import uuid

from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth

from app.core.firebase import get_firebase_app
from app.models.profile import Profile
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.schemas.staff import (
    PermissionSummaryResponse,
    RolePermissionsUpdateRequest,
    RoleSummaryResponse,
    StaffInviteRequest,
    StaffInviteResponse,
    StaffMemberResponse,
    StaffRoleUpdateRequest,
    StaffStatusUpdateRequest,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class StaffService:
    """Business logic for inviting staff, changing roles, and managing permission matrices."""

    def __init__(
        self,
        profile_repo: ProfileRepository,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repo = profile_repo
        self._audit = audit_service

    def invite_staff(self, data: StaffInviteRequest) -> StaffInviteResponse:
        """Create Firebase Auth account, allocate database profile, and assign role."""
        existing = self._repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Staff member with email '{data.email}' already exists.",
            )

        role = self._repo.get_role_by_id(data.role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{data.role_id}' not found.",
            )

        uid, sign_in_link = self._provision_firebase_user(
            email=data.email,
            display_name=data.display_name,
            phone=data.phone,
        )

        new_profile = Profile(
            id=uid,
            email=data.email,
            display_name=data.display_name,
            phone=data.phone,
            role_id=role.id,
            is_active=True,
        )
        created = self._repo.create(new_profile)

        return StaffInviteResponse(
            id=created.id,
            email=created.email,
            role_name=role.name,
            sign_in_link=sign_in_link,
            message=f"Staff member invited successfully with role '{role.name}'.",
        )

    def list_staff(self, skip: int = 0, limit: int = 100) -> list[StaffMemberResponse]:
        """Fetch all staff members with their active role metadata."""
        profiles = self._repo.list_all(skip=skip, limit=limit)
        return [
            StaffMemberResponse(
                id=p.id,
                email=p.email,
                display_name=p.display_name,
                avatar_url=p.avatar_url,
                phone=p.phone,
                role_id=p.role_id,
                role_name=p.role.name if p.role else "Unknown",
                is_active=p.is_active,
                created_at=p.created_at,
            )
            for p in profiles
        ]

    def update_staff_role(
        self, profile_id: str, data: StaffRoleUpdateRequest, actor_id: str | None = None
    ) -> StaffMemberResponse:
        """Update the assigned role of a staff member."""
        role = self._repo.get_role_by_id(data.role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{data.role_id}' not found.",
            )

        existing = self._repo.get_by_id(profile_id)
        old_role_name = existing.role.name if existing and existing.role else "Unknown"

        updated = self._repo.update_role(profile_id=profile_id, role_id=data.role_id)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found.",
            )

        if self._audit and old_role_name != role.name:
            self._audit.log(
                actor_id=actor_id,
                action="staff_role_updated",
                entity_type="staff",
                entity_id=updated.id,
                before={"email": updated.email, "role_name": old_role_name},
                after={"email": updated.email, "role_name": role.name},
            )

        return StaffMemberResponse(
            id=updated.id,
            email=updated.email,
            display_name=updated.display_name,
            avatar_url=updated.avatar_url,
            phone=updated.phone,
            role_id=updated.role_id,
            role_name=role.name,
            is_active=updated.is_active,
            created_at=updated.created_at,
        )

    def update_staff_status(
        self, profile_id: str, data: StaffStatusUpdateRequest, actor_id: str | None = None
    ) -> StaffMemberResponse:
        """Toggle active/inactive status for a staff profile."""
        existing = self._repo.get_by_id(profile_id)
        old_status = existing.is_active if existing else None

        updated = self._repo.update_status(profile_id=profile_id, is_active=data.is_active)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found.",
            )

        if self._audit and old_status != data.is_active:
            self._audit.log(
                actor_id=actor_id,
                action="staff_status_updated",
                entity_type="staff",
                entity_id=updated.id,
                before={"email": updated.email, "is_active": old_status},
                after={"email": updated.email, "is_active": data.is_active},
            )

        return StaffMemberResponse(
            id=updated.id,
            email=updated.email,
            display_name=updated.display_name,
            avatar_url=updated.avatar_url,
            phone=updated.phone,
            role_id=updated.role_id,
            role_name=updated.role.name if updated.role else "Unknown",
            is_active=updated.is_active,
            created_at=updated.created_at,
        )

    def list_roles(self) -> list[RoleSummaryResponse]:
        """Fetch all roles with their granted permission codes."""
        roles = self._repo.list_roles()
        result = []
        for r in roles:
            perms = self._repo.get_role_permissions(r.id)
            result.append(
                RoleSummaryResponse(
                    id=r.id,
                    name=r.name,
                    description=r.description,
                    permissions=perms,
                )
            )
        return result

    def list_permissions(self) -> list[PermissionSummaryResponse]:
        """Fetch all granular permissions defined in the system."""
        permissions = self._repo.list_permissions()
        return [
            PermissionSummaryResponse(
                id=p.id,
                code=p.code,
                description=p.description,
            )
            for p in permissions
        ]

    def update_role_permissions(
        self,
        role_id: str,
        data: RolePermissionsUpdateRequest,
        actor_id: str | None = None,
    ) -> RoleSummaryResponse:
        """Batch-update role permission mapping."""
        role = self._repo.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found.",
            )

        old_perms = self._repo.get_role_permissions(role_id)

        updated_perms = self._repo.update_role_permissions(
            role_id=role_id, permission_codes=data.permission_codes
        )

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="role_permissions_updated",
                entity_type="role_permissions",
                entity_id=role.id,
                before={"role_name": role.name, "permissions": old_perms},
                after={"role_name": role.name, "permissions": updated_perms},
            )

        return RoleSummaryResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=updated_perms,
        )

    def _provision_firebase_user(
        self, email: str, display_name: str | None, phone: str | None
    ) -> tuple[str, str | None]:
        """Create Firebase auth user if app is live, otherwise generate mock UID."""
        uid = f"uid_{uuid.uuid4().hex[:12]}"
        sign_in_link = None

        if get_firebase_app():
            try:
                user_record = firebase_auth.create_user(
                    email=email,
                    display_name=display_name,
                    phone_number=phone,
                )
                uid = user_record.uid
                with contextlib.suppress(Exception):
                    sign_in_link = firebase_auth.generate_password_reset_link(email)
            except firebase_auth.EmailAlreadyExistsError:
                user_record = firebase_auth.get_user_by_email(email)
                uid = user_record.uid
            except Exception as exc:
                logger.warning("Firebase Admin create_user failed: %s", exc)

        return uid, sign_in_link
