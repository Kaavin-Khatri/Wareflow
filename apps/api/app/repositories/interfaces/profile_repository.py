"""Profile repository interface protocol."""

from typing import Protocol

from app.models.auth_rbac import Role
from app.models.profile import Profile


class ProfileRepository(Protocol):
    """Data access interface for Profile and Role lookups."""

    def get_by_id(self, profile_id: str) -> Profile | None:
        """Fetch profile by Firebase UID."""
        ...

    def get_by_email(self, email: str) -> Profile | None:
        """Fetch profile by unique email address."""
        ...

    def count_all(self) -> int:
        """Count total registered profiles in the system."""
        ...

    def create(self, profile: Profile) -> Profile:
        """Persist a new profile in the database."""
        ...

    def get_role_by_name(self, name: str) -> Role | None:
        """Fetch system role by unique name (e.g. 'Owner')."""
        ...

    def get_role_permissions(self, role_id: str) -> list[str]:
        """Fetch all permission codes granted to a given role ID."""
        ...
