"""
Product repository interface contract.

Defines data-access abstraction using typing.Protocol.
Services depend exclusively on this interface, never on concrete database classes.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProductRepositoryInterface(Protocol):
    """Abstraction for product data operations."""

    def get_by_id(self, product_id: str) -> dict[str, str] | None:
        """Fetch a single product by ID."""
        ...

    def list_all(self) -> list[dict[str, str]]:
        """List all products."""
        ...
