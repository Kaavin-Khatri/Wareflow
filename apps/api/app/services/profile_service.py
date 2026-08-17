"""Profile and User authorization lifecycle service."""

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.profile import Profile
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.schemas.profile import ProfileResponse


class ProfileService:
    """Business logic for user profiles, roles, and bootstrap onboarding."""

    def __init__(self, profile_repo: ProfileRepository) -> None:
        self._repo = profile_repo

    def bootstrap_user(
        self,
        uid: str,
        email: str,
        name: str | None = None,
        avatar: str | None = None,
        phone: str | None = None,
    ) -> ProfileResponse:
        """
        Bootstrap authenticated Firebase user.

        If profile exists, returns it.
        If first user in system or ALLOW_FIRST_SIGNUP is True, assigns 'Owner' role.
        Otherwise raises 403 Forbidden (invitation required).
        """
        existing = self._repo.get_by_id(uid)
        if existing:
            return self._build_response(existing)

        settings = get_settings()
        total_profiles = self._repo.count_all()

        if total_profiles == 0 or settings.allow_first_signup:
            target_role_name = "Owner"
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is by invitation only. Contact your organization administrator.",
            )

        role = self._repo.get_role_by_name(target_role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Default role '{target_role_name}' not found in database.",
            )

        new_profile = Profile(
            id=uid,
            email=email,
            display_name=name,
            avatar_url=avatar,
            phone=phone,
            role_id=role.id,
            is_active=True,
        )
        created = self._repo.create(new_profile)
        return self._build_response(created)

    def get_profile(self, uid: str) -> ProfileResponse:
        """Fetch existing user profile by Firebase UID."""
        profile = self._repo.get_by_id(uid)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found.",
            )
        return self._build_response(profile)

    def _build_response(self, profile: Profile) -> ProfileResponse:
        permissions = self._repo.get_role_permissions(profile.role_id)
        return ProfileResponse(
            id=profile.id,
            email=profile.email,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            phone=profile.phone,
            role_id=profile.role_id,
            role_name=profile.role.name if profile.role else "Unknown",
            permissions=permissions,
            is_active=profile.is_active,
            created_at=profile.created_at,
        )
