"""Supplier access token repository implementations."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.portal import SupplierAccessToken


class SqlAlchemySupplierAccessTokenRepository:
    """Database-backed repository for supplier magic-link access tokens."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, token: SupplierAccessToken) -> SupplierAccessToken:
        """Persist a new supplier access token."""
        self._session.add(token)
        self._session.commit()
        self._session.refresh(token)
        return token

    def get_by_token(self, token: str) -> SupplierAccessToken | None:
        """Fetch access token by its unique token string with eager-loaded relationships."""
        return self._session.execute(
            select(SupplierAccessToken)
            .options(
                joinedload(SupplierAccessToken.supplier),
                joinedload(SupplierAccessToken.purchase_order),
            )
            .where(SupplierAccessToken.token == token)
        ).scalar_one_or_none()

    def get_by_purchase_order_id(self, po_id: str) -> SupplierAccessToken | None:
        """Fetch access token associated with a specific Purchase Order."""
        return self._session.execute(
            select(SupplierAccessToken).where(SupplierAccessToken.purchase_order_id == po_id)
        ).scalar_one_or_none()

    def delete(self, token_id: str) -> bool:
        """Remove a token by primary key (single-use invalidation)."""
        token_obj = self._session.get(SupplierAccessToken, token_id)
        if not token_obj:
            return False
        self._session.delete(token_obj)
        self._session.commit()
        return True


class InMemorySupplierAccessTokenRepository:
    """In-memory mock repository for supplier access token unit testing."""

    def __init__(self) -> None:
        self._tokens: dict[str, SupplierAccessToken] = {}

    def create(self, token: SupplierAccessToken) -> SupplierAccessToken:
        """Store a new token in memory."""
        self._tokens[token.id] = token
        return token

    def get_by_token(self, token: str) -> SupplierAccessToken | None:
        """Find token by its unique token string."""
        for t in self._tokens.values():
            if t.token == token:
                return t
        return None

    def get_by_purchase_order_id(self, po_id: str) -> SupplierAccessToken | None:
        """Find token by associated Purchase Order ID."""
        for t in self._tokens.values():
            if t.purchase_order_id == po_id:
                return t
        return None

    def delete(self, token_id: str) -> bool:
        """Remove token from storage."""
        if token_id in self._tokens:
            del self._tokens[token_id]
            return True
        return False
