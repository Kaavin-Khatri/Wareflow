"""SQLAlchemy concrete implementation of ProfileRepository."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.auth_rbac import Permission, Role, RolePermission
from app.models.profile import Profile


class SqlAlchemyProfileRepository:
    """SQLAlchemy data access implementation for Profile entity."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, profile_id: str) -> Profile | None:
        return self._session.execute(
            select(Profile).where(Profile.id == profile_id)
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> Profile | None:
        return self._session.execute(
            select(Profile).where(Profile.email == email)
        ).scalar_one_or_none()

    def count_all(self) -> int:
        count = self._session.scalar(select(func.count(Profile.id)))
        return count or 0

    def create(self, profile: Profile) -> Profile:
        self._session.add(profile)
        self._session.commit()
        self._session.refresh(profile)
        return profile

    def get_role_by_name(self, name: str) -> Role | None:
        return self._session.execute(select(Role).where(Role.name == name)).scalar_one_or_none()

    def get_role_permissions(self, role_id: str) -> list[str]:
        query = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        return list(self._session.execute(query).scalars().all())
