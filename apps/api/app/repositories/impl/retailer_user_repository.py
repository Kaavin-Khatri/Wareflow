"""SQLAlchemy and In-Memory implementations of RetailerUserRepository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.portal import RetailerPortalInvite, RetailerUser
from app.repositories.interfaces.retailer_user_repository import RetailerUserRepository


class SqlAlchemyRetailerUserRepository(RetailerUserRepository):
    """Concrete repository persisting and querying RetailerUser and RetailerPortalInvite records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_user(self, user: RetailerUser) -> RetailerUser:
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def get_user_by_id(self, user_id: str) -> RetailerUser | None:
        try:
            return self._session.scalar(select(RetailerUser).where(RetailerUser.id == user_id))
        except Exception:
            self._session.rollback()
            return None

    def get_user_by_email(self, email: str) -> RetailerUser | None:
        try:
            return self._session.scalar(
                select(RetailerUser).where(RetailerUser.email.ilike(email.strip()))
            )
        except Exception:
            self._session.rollback()
            return None

    def get_users_by_retailer_id(self, retailer_id: str) -> list[RetailerUser]:
        try:
            stmt = (
                select(RetailerUser)
                .where(RetailerUser.retailer_id == retailer_id)
                .order_by(RetailerUser.created_at.desc())
            )
            return list(self._session.scalars(stmt).all())
        except Exception:
            self._session.rollback()
            return []

    def create_invite(self, invite: RetailerPortalInvite) -> RetailerPortalInvite:
        self._session.add(invite)
        self._session.commit()
        self._session.refresh(invite)
        return invite

    def get_invite_by_token(self, token: str) -> RetailerPortalInvite | None:
        return self._session.scalar(
            select(RetailerPortalInvite).where(RetailerPortalInvite.token == token.strip())
        )

    def get_pending_invite_by_email(self, email: str) -> RetailerPortalInvite | None:
        now = datetime.now(UTC)
        stmt = (
            select(RetailerPortalInvite)
            .where(
                RetailerPortalInvite.email.ilike(email.strip()),
                RetailerPortalInvite.is_accepted.is_(False),
                RetailerPortalInvite.expires_at > now,
            )
            .order_by(RetailerPortalInvite.created_at.desc())
        )
        return self._session.scalar(stmt)

    def mark_invite_accepted(self, token: str) -> bool:
        invite = self.get_invite_by_token(token)
        if not invite:
            return False
        invite.is_accepted = True
        self._session.commit()
        self._session.refresh(invite)
        return True


class InMemoryRetailerUserRepository(RetailerUserRepository):
    """In-memory mock repository for fast, zero-DB unit testing."""

    def __init__(
        self,
        initial_users: list[RetailerUser] | None = None,
        initial_invites: list[RetailerPortalInvite] | None = None,
    ) -> None:
        self._users: dict[str, RetailerUser] = {}
        self._invites: dict[str, RetailerPortalInvite] = {}
        if initial_users:
            for u in initial_users:
                self._users[u.id] = u
        if initial_invites:
            for inv in initial_invites:
                self._invites[inv.token] = inv

    def create_user(self, user: RetailerUser) -> RetailerUser:
        self._users[user.id] = user
        return user

    def get_user_by_id(self, user_id: str) -> RetailerUser | None:
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> RetailerUser | None:
        norm = email.strip().lower()
        for u in self._users.values():
            if u.email.strip().lower() == norm:
                return u
        return None

    def get_users_by_retailer_id(self, retailer_id: str) -> list[RetailerUser]:
        return [u for u in self._users.values() if u.retailer_id == retailer_id]

    def create_invite(self, invite: RetailerPortalInvite) -> RetailerPortalInvite:
        self._invites[invite.token] = invite
        return invite

    def get_invite_by_token(self, token: str) -> RetailerPortalInvite | None:
        return self._invites.get(token.strip())

    def get_pending_invite_by_email(self, email: str) -> RetailerPortalInvite | None:
        norm = email.strip().lower()
        now = datetime.now(UTC)
        for inv in self._invites.values():
            if (
                inv.email.strip().lower() == norm
                and not inv.is_accepted
                and (inv.expires_at.tzinfo is None or inv.expires_at > now)
            ):
                return inv
        return None

    def mark_invite_accepted(self, token: str) -> bool:
        inv = self._invites.get(token.strip())
        if not inv:
            return False
        inv.is_accepted = True
        return True
