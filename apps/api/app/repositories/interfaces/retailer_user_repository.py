"""Retailer portal user and invite repository interface definition."""

from typing import Protocol, runtime_checkable

from app.models.portal import RetailerPortalInvite, RetailerUser


@runtime_checkable
class RetailerUserRepository(Protocol):
    """Abstraction for retailer portal user identity and invitation lifecycle."""

    def create_user(self, user: RetailerUser) -> RetailerUser:
        """Persist a new retailer portal user record."""
        ...

    def get_user_by_id(self, user_id: str) -> RetailerUser | None:
        """Fetch retailer user by Firebase UID."""
        ...

    def get_user_by_email(self, email: str) -> RetailerUser | None:
        """Fetch retailer user by email."""
        ...

    def get_users_by_retailer_id(self, retailer_id: str) -> list[RetailerUser]:
        """Fetch all portal users associated with a specific retailer account."""
        ...

    def create_invite(self, invite: RetailerPortalInvite) -> RetailerPortalInvite:
        """Persist a pending retailer portal invite record."""
        ...

    def get_invite_by_token(self, token: str) -> RetailerPortalInvite | None:
        """Lookup an invitation by unique invite token."""
        ...

    def get_pending_invite_by_email(self, email: str) -> RetailerPortalInvite | None:
        """Lookup active unaccepted invite by email."""
        ...

    def mark_invite_accepted(self, token: str) -> bool:
        """Mark an invite token as accepted."""
        ...
