"""Profile repository interface protocol."""

from typing import Protocol

from app.models.auth_rbac import Permission, Role
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

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Profile]:
        """List all staff user profiles."""
        ...

    def create(self, profile: Profile) -> Profile:
        """Persist a new profile in the database."""
        ...

    def get_role_by_id(self, role_id: str) -> Role | None:
        """Fetch system role by UUID primary key."""
        ...

    def get_role_by_name(self, name: str) -> Role | None:
        """Fetch system role by unique name (e.g. 'Owner')."""
        ...

    def list_roles(self) -> list[Role]:
        """List all defined system roles."""
        ...

    def list_permissions(self) -> list[Permission]:
        """List all defined system permissions."""
        ...

    def get_role_permissions(self, role_id: str) -> list[str]:
        """Fetch all permission codes granted to a given role ID."""
        ...

    def update_role(self, profile_id: str, role_id: str) -> Profile | None:
        """Update a staff member's assigned role."""
        ...

    def update_status(self, profile_id: str, is_active: bool) -> Profile | None:
        """Toggle active status for a staff profile."""
        ...

    def update_role_permissions(self, role_id: str, permission_codes: list[str]) -> list[str]:
        """Sync granted permissions for a role by permission codes."""
        ...
