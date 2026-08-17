"""SQLAlchemy concrete implementation of ProfileRepository."""

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
