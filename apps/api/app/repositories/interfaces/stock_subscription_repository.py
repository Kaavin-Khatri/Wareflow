"""Repository interface for Retailer Stock Subscriptions (Step 13.4)."""

from abc import ABC, abstractmethod

from app.models.portal import StockSubscription


class StockSubscriptionRepositoryInterface(ABC):
    """Abstract contract for stock back-in-stock alert subscriptions."""

    @abstractmethod
    def get_by_id(self, subscription_id: str) -> StockSubscription | None:
        """Fetch subscription record by primary key UUID."""
        ...

    @abstractmethod
    def get_by_product_and_retailer(
        self, product_id: str, retailer_id: str
    ) -> StockSubscription | None:
        """Fetch subscription for a specific product and retailer combination."""
        ...

    @abstractmethod
    def list_active_for_product(self, product_id: str) -> list[StockSubscription]:
        """Fetch all active pending subscriptions for a product."""
        ...

    @abstractmethod
    def list_for_product(self, product_id: str) -> list[StockSubscription]:
        """List all subscriptions (active and fulfilled) for a product."""
        ...

    @abstractmethod
    def list_for_retailer(self, retailer_id: str) -> list[StockSubscription]:
        """List all subscriptions for a retailer."""
        ...

    @abstractmethod
    def count_active_for_retailer(self, retailer_id: str) -> int:
        """Count active standing subscriptions for a retailer."""
        ...

    @abstractmethod
    def count_active_by_retailers(self) -> dict[str, int]:
        """Return mapping of retailer_id -> active subscription count."""
        ...

    @abstractmethod
    def create(self, subscription: StockSubscription) -> StockSubscription:
        """Create a new stock subscription record."""
        ...

    @abstractmethod
    def update(self, subscription: StockSubscription) -> StockSubscription:
        """Update an existing stock subscription record."""
        ...

    @abstractmethod
    def delete(self, subscription_id: str) -> bool:
        """Permanently delete a stock subscription record."""
        ...
