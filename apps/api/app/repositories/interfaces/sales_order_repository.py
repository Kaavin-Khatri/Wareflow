"""Sales Order repository interface protocol."""

from typing import Protocol

from app.models.retailer import SalesOrder


class SalesOrderRepositoryInterface(Protocol):
    """Data access contract for Sales Orders and Order Items."""

    def get_by_id(self, order_id: str) -> SalesOrder | None:
        """Fetch sales order by ID with items, retailer, and product relationships loaded."""
        ...

    def get_by_so_number(self, so_number: str) -> SalesOrder | None:
        """Fetch sales order by unique human-readable SO number."""
        ...

    def list_all(
        self,
        status: str | None = None,
        retailer_id: str | None = None,
        buyer_type: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[SalesOrder], int]:
        """List sales orders with optional filtering, search, and pagination."""
        ...

    def create(self, order: SalesOrder) -> SalesOrder:
        """Persist a newly created sales order with line items."""
        ...

    def update(self, order: SalesOrder) -> SalesOrder:
        """Save updates to an existing sales order."""
        ...

    def generate_next_so_number(self) -> str:
        """Generate the next sequential human-readable sales order number (e.g. SO-YYYYMM-0001)."""
        ...

    def get_historical_order_quantities(
        self,
        product_id: str,
        retailer_id: str | None = None,
        customer_id: str | None = None,
        exclude_order_id: str | None = None,
    ) -> list[float]:
        """Fetch historical ordered quantities for a specific product and buyer (retailer/customer)."""
        ...
