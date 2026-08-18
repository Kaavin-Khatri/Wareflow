"""UoM Repository Interface Protocol."""

from typing import Protocol

from app.models.uom import ProductUOMConversion, UnitOfMeasure


class UomRepositoryInterface(Protocol):
    """Abstract data-access protocol for Units of Measure and Product Conversions."""

    def list_uoms(self) -> list[UnitOfMeasure]:
        """List all defined units of measure ordered by name."""
        ...

    def get_uom_by_id(self, uom_id: str) -> UnitOfMeasure | None:
        """Find a unit of measure by UUID."""
        ...

    def get_uom_by_abbreviation(self, abbreviation: str) -> UnitOfMeasure | None:
        """Find a unit of measure by case-insensitive abbreviation."""
        ...

    def create_uom(self, name: str, abbreviation: str) -> UnitOfMeasure:
        """Create a new unit of measure."""
        ...

    def update_uom(
        self, uom_id: str, name: str | None = None, abbreviation: str | None = None
    ) -> UnitOfMeasure | None:
        """Update an existing unit of measure."""
        ...

    def delete_uom(self, uom_id: str) -> bool:
        """Delete a unit of measure."""
        ...

    def list_product_conversions(self, product_id: str) -> list[ProductUOMConversion]:
        """List all UoM conversion ratios defined for a specific product."""
        ...

    def get_conversion_by_id(self, conversion_id: str) -> ProductUOMConversion | None:
        """Find a specific conversion rule by UUID."""
        ...

    def get_conversion_between(
        self, product_id: str, from_uom_id: str, to_uom_id: str
    ) -> ProductUOMConversion | None:
        """Find conversion factor between two specific UoMs for a product."""
        ...

    def create_or_update_conversion(
        self, product_id: str, from_uom_id: str, to_uom_id: str, factor: float
    ) -> ProductUOMConversion:
        """Create or update a conversion ratio between two UoMs for a product."""
        ...

    def delete_conversion(self, conversion_id: str) -> bool:
        """Delete a product UoM conversion rule."""
        ...

    def get_product_base_uom_id(self, product_id: str) -> str | None:
        """Get the base UoM ID for a product."""
        ...
