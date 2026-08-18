"""Repository interface protocol for Direct Customer entities."""

from typing import Any, Protocol, runtime_checkable

from app.models.portal import Customer


@runtime_checkable
class CustomerRepositoryInterface(Protocol):
    """Protocol defining persistence operations for Direct Customers (DIP)."""

    def get_by_id(self, customer_id: str) -> Customer | None:
        """Fetch customer by primary key ID."""
        ...

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> tuple[list[Customer], int]:
        """Fetch paginated customers matching search query along with total count."""
        ...

    def create(self, customer: Customer) -> Customer:
        """Persist a new Customer entity."""
        ...

    def update(self, customer_id: str, updates: dict[str, Any]) -> Customer | None:
        """Apply partial updates to a Customer entity."""
        ...

    def delete(self, customer_id: str) -> bool:
        """Delete customer entity by ID."""
        ...
