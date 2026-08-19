from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.auth_rbac import Permission, Role, RolePermission
from app.models.profile import Profile


class SqlAlchemyProfileRepository:
    """SQLAlchemy data access implementation for Profile entity."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, profile_id: str) -> Profile | None:
        return self._session.execute(
            select(Profile).options(joinedload(Profile.role)).where(Profile.id == profile_id)
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> Profile | None:
        return self._session.execute(
            select(Profile).options(joinedload(Profile.role)).where(Profile.email == email)
        ).scalar_one_or_none()

    def count_all(self) -> int:
        count = self._session.scalar(select(func.count(Profile.id)))
        return count or 0

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Profile]:
        return list(
            self._session.execute(
                select(Profile)
                .options(joinedload(Profile.role))
                .order_by(Profile.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def create(self, profile: Profile) -> Profile:
        self._session.add(profile)
        self._session.commit()
        self._session.refresh(profile)
        return self.get_by_id(profile.id) or profile

    def get_role_by_id(self, role_id: str) -> Role | None:
        return self._session.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()

    def get_role_by_name(self, name: str) -> Role | None:
        return self._session.execute(select(Role).where(Role.name == name)).scalar_one_or_none()

    def list_roles(self) -> list[Role]:
        return list(self._session.execute(select(Role).order_by(Role.name.asc())).scalars().all())

    def list_permissions(self) -> list[Permission]:
        return list(
            self._session.execute(select(Permission).order_by(Permission.code.asc()))
            .scalars()
            .all()
        )

    def get_role_permissions(self, role_id: str) -> list[str]:
        query = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        return list(self._session.execute(query).scalars().all())

    def update_role(self, profile_id: str, role_id: str) -> Profile | None:
        profile = self.get_by_id(profile_id)
        if not profile:
            return None
        profile.role_id = role_id
        self._session.commit()
        self._session.refresh(profile)
        return profile

    def update_status(self, profile_id: str, is_active: bool) -> Profile | None:
        profile = self.get_by_id(profile_id)
        if not profile:
            return None
        profile.is_active = is_active
        self._session.commit()
        self._session.refresh(profile)
        return profile

    def update_role_permissions(self, role_id: str, permission_codes: list[str]) -> list[str]:
        # Delete existing mappings for this role
        self._session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))

        # Query all matching permissions by code
        perms = (
            self._session.execute(select(Permission).where(Permission.code.in_(permission_codes)))
            .scalars()
            .all()
        )

        # Create new mappings
        for perm in perms:
            self._session.add(RolePermission(role_id=role_id, permission_id=perm.id))

        self._session.commit()
        return self.get_role_permissions(role_id)

    def update_two_factor(
        self,
        profile_id: str,
        totp_secret_encrypted: str | None,
        totp_enabled: bool,
        backup_codes_encrypted: str | None,
    ) -> Profile | None:
        profile = self.get_by_id(profile_id)
        if not profile:
            return None
        profile.totp_secret_encrypted = totp_secret_encrypted
        profile.totp_enabled = totp_enabled
        profile.backup_codes_encrypted = backup_codes_encrypted
        profile.totp_enrolled_at = datetime.now(UTC) if totp_enabled else None
        self._session.commit()
        self._session.refresh(profile)
        return profile

    def update_backup_codes(
        self, profile_id: str, backup_codes_encrypted: str | None
    ) -> Profile | None:
        profile = self.get_by_id(profile_id)
        if not profile:
            return None
        profile.backup_codes_encrypted = backup_codes_encrypted
        self._session.commit()
        self._session.refresh(profile)
        return profile

    def update_appearance_preferences(
        self, profile_id: str, theme_preference: str, accent_color: str
    ) -> Profile | None:
        profile = self.get_by_id(profile_id)
        if not profile:
            return None
        profile.theme_preference = theme_preference
        profile.accent_color = accent_color
        self._session.commit()
        self._session.refresh(profile)
        return profile


class InMemoryProfileRepository:
    """In-memory mock repository for Profile entity unit testing."""

    def __init__(
        self,
        initial_profiles: list[Profile] | None = None,
        initial_roles: list[Role] | None = None,
        initial_role_permissions: dict[str, list[str]] | None = None,
    ) -> None:
        self._profiles: dict[str, Profile] = {}
        self._roles: dict[str, Role] = {}
        self._role_permissions: dict[str, list[str]] = initial_role_permissions or {}
        if initial_profiles:
            for p in initial_profiles:
                self._profiles[p.id] = p
        if initial_roles:
            for r in initial_roles:
                self._roles[r.id] = r

    def get_by_id(self, profile_id: str) -> Profile | None:
        return self._profiles.get(profile_id)

    def get_by_email(self, email: str) -> Profile | None:
        norm = email.strip().lower()
        for p in self._profiles.values():
            if p.email.strip().lower() == norm:
                return p
        return None

    def count_all(self) -> int:
        return len(self._profiles)

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Profile]:
        return list(self._profiles.values())[skip : skip + limit]

    def create(self, profile: Profile) -> Profile:
        self._profiles[profile.id] = profile
        return profile

    def get_role_by_id(self, role_id: str) -> Role | None:
        return self._roles.get(role_id)

    def get_role_by_name(self, name: str) -> Role | None:
        norm = name.strip().lower()
        for r in self._roles.values():
            if r.name.strip().lower() == norm:
                return r
        return None

    def list_roles(self) -> list[Role]:
        return list(self._roles.values())

    def list_permissions(self) -> list[Permission]:
        return []

    def get_role_permissions(self, role_id: str) -> list[str]:
        return self._role_permissions.get(role_id, [])

    def update_role(self, profile_id: str, role_id: str) -> Profile | None:
        p = self.get_by_id(profile_id)
        if not p:
            return None
        p.role_id = role_id
        return p

    def update_status(self, profile_id: str, is_active: bool) -> Profile | None:
        p = self.get_by_id(profile_id)
        if not p:
            return None
        p.is_active = is_active
        return p

    def update_role_permissions(self, role_id: str, permission_codes: list[str]) -> list[str]:
        self._role_permissions[role_id] = permission_codes
        return permission_codes

    def update_two_factor(
        self,
        profile_id: str,
        totp_secret_encrypted: str | None,
        totp_enabled: bool,
        backup_codes_encrypted: str | None,
    ) -> Profile | None:
        p = self.get_by_id(profile_id)
        if not p:
            return None
        p.totp_secret_encrypted = totp_secret_encrypted
        p.totp_enabled = totp_enabled
        p.backup_codes_encrypted = backup_codes_encrypted
        p.totp_enrolled_at = datetime.now(UTC) if totp_enabled else None
        return p

    def update_backup_codes(
        self, profile_id: str, backup_codes_encrypted: str | None
    ) -> Profile | None:
        p = self.get_by_id(profile_id)
        if not p:
            return None
        p.backup_codes_encrypted = backup_codes_encrypted
        return p

    def update_appearance_preferences(
        self, profile_id: str, theme_preference: str, accent_color: str
    ) -> Profile | None:
        p = self.get_by_id(profile_id)
        if not p:
            return None
        p.theme_preference = theme_preference
        p.accent_color = accent_color
        return p

