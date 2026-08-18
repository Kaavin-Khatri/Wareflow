"""
Pluggable wholesale pricing strategy engine (Open/Closed Principle).

Allows registering and resolving tiered pricing strategies (Standard, Silver, Gold,
or custom volume tiers) without modifying sales order or pricing calculation logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PricingCalculationResult:
    """Calculated pricing breakdown for an order line item."""

    base_unit_price: float
    discount_percentage: float
    effective_unit_price: float
    quantity: int
    line_total: float
    discount_amount: float
    tier_applied: str

    @property
    def unit_price(self) -> float:
        """Alias for effective_unit_price."""
        return self.effective_unit_price


class PricingStrategy(ABC):
    """Abstract Strategy interface for wholesale pricing rules (OCP)."""

    @property
    @abstractmethod
    def tier_name(self) -> str:
        """Name of the pricing tier this strategy handles."""
        ...

    @property
    @abstractmethod
    def default_discount_percentage(self) -> float:
        """Default base percentage discount for this tier (0.0 to 100.0)."""
        ...

    @abstractmethod
    def calculate_unit_price(
        self, base_price: float, quantity: int = 1, context: dict[str, Any] | None = None
    ) -> float:
        """Calculate discounted unit price per single item."""
        ...

    def calculate_line(
        self,
        base_price: float,
        quantity: int = 1,
        context: dict[str, Any] | None = None,
    ) -> PricingCalculationResult:
        """Calculate complete line breakdown including unit price, line total, and savings."""
        if quantity <= 0:
            quantity = 1
        unit_price = self.calculate_unit_price(base_price, quantity, context)
        line_total = round(unit_price * quantity, 2)
        base_total = round(base_price * quantity, 2)
        discount_amount = max(0.0, round(base_total - line_total, 2))
        discount_percentage = (
            round((discount_amount / base_total) * 100.0, 2) if base_total > 0 else 0.0
        )

        return PricingCalculationResult(
            base_unit_price=round(base_price, 2),
            discount_percentage=discount_percentage,
            effective_unit_price=unit_price,
            quantity=quantity,
            line_total=line_total,
            discount_amount=discount_amount,
            tier_applied=self.tier_name,
        )


class StandardPricingStrategy(PricingStrategy):
    """Standard wholesale pricing strategy with 0% discount."""

    @property
    def tier_name(self) -> str:
        return "standard"

    @property
    def default_discount_percentage(self) -> float:
        return 0.0

    def calculate_unit_price(
        self, base_price: float, quantity: int = 1, context: dict[str, Any] | None = None
    ) -> float:
        return round(base_price, 2)


class SilverPricingStrategy(PricingStrategy):
    """Silver wholesale tier strategy granting a 5% discount."""

    def __init__(self, discount_percentage: float = 5.0) -> None:
        self._discount = discount_percentage

    @property
    def tier_name(self) -> str:
        return "silver"

    @property
    def default_discount_percentage(self) -> float:
        return self._discount

    def calculate_unit_price(
        self, base_price: float, quantity: int = 1, context: dict[str, Any] | None = None
    ) -> float:
        multiplier = max(0.0, 1.0 - (self._discount / 100.0))
        return round(base_price * multiplier, 2)


class GoldPricingStrategy(PricingStrategy):
    """Gold wholesale tier strategy granting a 10% discount."""

    def __init__(self, discount_percentage: float = 10.0) -> None:
        self._discount = discount_percentage

    @property
    def tier_name(self) -> str:
        return "gold"

    @property
    def default_discount_percentage(self) -> float:
        return self._discount

    def calculate_unit_price(
        self, base_price: float, quantity: int = 1, context: dict[str, Any] | None = None
    ) -> float:
        multiplier = max(0.0, 1.0 - (self._discount / 100.0))
        return round(base_price * multiplier, 2)


class TieredDiscountPricingStrategy(PricingStrategy):
    """
    Volume-sensitive discount strategy based on order line quantities.
    Example:
      1-9 units: 0% discount
      10-49 units: 5% discount
      50+ units: 12% discount
    """

    def __init__(self, tier_name: str = "volume_tiered") -> None:
        self._tier_name = tier_name

    @property
    def tier_name(self) -> str:
        return self._tier_name

    @property
    def default_discount_percentage(self) -> float:
        return 0.0

    def calculate_unit_price(
        self, base_price: float, quantity: int = 1, context: dict[str, Any] | None = None
    ) -> float:
        if quantity >= 50:
            discount = 12.0
        elif quantity >= 10:
            discount = 5.0
        else:
            discount = 0.0

        multiplier = max(0.0, 1.0 - (discount / 100.0))
        return round(base_price * multiplier, 2)


class PricingEngineService:
    """
    Pricing Engine coordinating pluggable pricing strategies.

    SalesOrderService and other domain services depend on this engine,
    which delegates to the appropriate Strategy without hardcoded if/else chains.
    """

    def __init__(self, strategies: list[PricingStrategy] | None = None) -> None:
        self._strategies: dict[str, PricingStrategy] = {}

        # Register default strategies
        default_list = strategies or [
            StandardPricingStrategy(),
            SilverPricingStrategy(),
            GoldPricingStrategy(),
            TieredDiscountPricingStrategy(),
        ]
        for strategy in default_list:
            self.register_strategy(strategy)

    def register_strategy(self, strategy: PricingStrategy) -> None:
        """Register or override a strategy for a tier (OCP extension point)."""
        self._strategies[strategy.tier_name.lower()] = strategy

    def get_strategy(self, tier: str | None) -> PricingStrategy:
        """Resolve strategy by tier name, falling back to Standard."""
        normalized = (tier or "standard").strip().lower()
        return self._strategies.get(
            normalized, self._strategies.get("standard", StandardPricingStrategy())
        )

    def calculate_line_price(
        self,
        tier: str | None,
        base_price: float,
        quantity: int = 1,
        context: dict[str, Any] | None = None,
    ) -> PricingCalculationResult:
        """Calculate line price breakdown for a retailer's pricing tier."""
        strategy = self.get_strategy(tier)
        return strategy.calculate_line(base_price, quantity, context)
