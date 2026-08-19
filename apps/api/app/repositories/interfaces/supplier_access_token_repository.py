"""Supplier access token repository interface protocol."""

from typing import Protocol

from app.models.portal import SupplierAccessToken


class SupplierAccessTokenRepositoryInterface(Protocol):
    """Data access contract for supplier magic-link access tokens."""

    def create(self, token: SupplierAccessToken) -> SupplierAccessToken:
        """Persist a new supplier access token."""
        ...

    def get_by_token(self, token: str) -> SupplierAccessToken | None:
        """Fetch access token by its unique token string."""
        ...

    def get_by_purchase_order_id(self, po_id: str) -> SupplierAccessToken | None:
        """Fetch access token associated with a specific Purchase Order."""
        ...

    def delete(self, token_id: str) -> bool:
        """Remove a token by primary key (single-use invalidation)."""
        ...
