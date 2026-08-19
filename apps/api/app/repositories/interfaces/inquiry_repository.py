"""Product inquiry repository interface."""

from typing import Protocol, runtime_checkable

from app.models.portal import ProductInquiry


@runtime_checkable
class InquiryRepositoryInterface(Protocol):
    """Protocol contract for ProductInquiry persistence (DIP)."""

    def create(self, inquiry: ProductInquiry) -> ProductInquiry:
        """Persist a new product inquiry."""
        ...

    def get_by_id(self, inquiry_id: str) -> ProductInquiry | None:
        """Fetch inquiry by ID."""
        ...

    def list_for_retailer(self, retailer_id: str) -> list[ProductInquiry]:
        """List inquiries strictly for a specific retailer in chronological order."""
        ...

    def list_all(
        self,
        status: str | None = None,
        product_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProductInquiry]:
        """List inquiries for staff with optional filters."""
        ...

    def update(self, inquiry: ProductInquiry) -> ProductInquiry:
        """Update an existing inquiry."""
        ...
