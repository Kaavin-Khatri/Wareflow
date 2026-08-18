"""Repository interface protocol for Sales Returns (RMA In)."""

from typing import Protocol, runtime_checkable

from app.models.returns import SalesReturn, SalesReturnStatusEnum


@runtime_checkable
class SalesReturnRepositoryInterface(Protocol):
    """Protocol defining persistence operations for Sales Returns (DIP)."""

    def get_by_id(self, return_id: str) -> SalesReturn | None:
        """Fetch a single Sales Return by ID with eager-loaded relations."""
        ...

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        retailer_id: str | None = None,
        sales_order_id: str | None = None,
        status: SalesReturnStatusEnum | None = None,
        search: str | None = None,
    ) -> list[SalesReturn]:
        """Fetch filtered and paginated Sales Returns."""
        ...

    def create(self, sales_return: SalesReturn) -> SalesReturn:
        """Persist a new Sales Return and its line items."""
        ...

    def update_status(
        self, return_id: str, status: SalesReturnStatusEnum
    ) -> SalesReturn | None:
        """Update lifecycle status of a Sales Return."""
        ...

    def get_returned_quantities_by_order(self, sales_order_id: str) -> dict[str, float]:
        """
        Get aggregated previously returned quantities per product for a sales order.
        Excludes rejected returns.
        """
        ...
