"""Protocol interface for Delivery repository."""

from typing import Protocol

from app.models.delivery import Delivery, DeliveryStatusEnum


class DeliveryRepositoryInterface(Protocol):
    """Interface for Delivery data access operations."""

    def create(self, delivery: Delivery) -> Delivery:
        """Persist a new delivery record."""
        ...

    def get_by_id(self, delivery_id: str) -> Delivery | None:
        """Retrieve delivery by ID."""
        ...

    def get_by_sales_order_id(self, sales_order_id: str) -> Delivery | None:
        """Retrieve delivery associated with a sales order."""
        ...

    def update(self, delivery: Delivery) -> Delivery:
        """Update existing delivery record."""
        ...

    def list_all(
        self,
        status: DeliveryStatusEnum | str | None = None,
        driver_name: str | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[Delivery]:
        """List deliveries with optional filtering."""
        ...
