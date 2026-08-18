"""Unit of Measure domain service enforcing packaging conversions and boundary rules."""

from fastapi import HTTPException, status

from app.models.uom import ProductUOMConversion, UnitOfMeasure
from app.repositories.interfaces.uom_repository import UomRepositoryInterface
from app.services.audit_service import AuditService


class UomConversionError(ValueError):
    """Raised when a unit of measure conversion cannot be resolved."""

    pass


class UomService:
    """Domain service for managing Units of Measure and packaging conversion ratios."""

    def __init__(
        self,
        uom_repo: UomRepositoryInterface,
        audit_service: AuditService | None = None,
    ) -> None:
        self.uom_repo = uom_repo
        self.audit_service = audit_service

    def list_uoms(self) -> list[UnitOfMeasure]:
        """List all units of measure."""
        return self.uom_repo.list_uoms()

    def get_uom(self, uom_id: str) -> UnitOfMeasure:
        """Get unit of measure by ID or raise 404."""
        uom = self.uom_repo.get_uom_by_id(uom_id)
        if not uom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unit of measure '{uom_id}' not found.",
            )
        return uom

    def create_uom(
        self, name: str, abbreviation: str, actor_id: str | None = None
    ) -> UnitOfMeasure:
        """Create a new unit of measure with uniqueness validation."""
        existing = self.uom_repo.get_uom_by_abbreviation(abbreviation)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Unit of measure with abbreviation '{abbreviation}' already exists.",
            )

        uom = self.uom_repo.create_uom(name=name, abbreviation=abbreviation)

        if self.audit_service and actor_id:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="uom_created",
                entity_type="unit_of_measure",
                entity_id=uom.id,
                before_value=None,
                after_value={"name": uom.name, "abbreviation": uom.abbreviation},
            )
        return uom

    def update_uom(
        self,
        uom_id: str,
        name: str | None = None,
        abbreviation: str | None = None,
        actor_id: str | None = None,
    ) -> UnitOfMeasure:
        """Update an existing unit of measure."""
        uom = self.get_uom(uom_id)
        before_state = {"name": uom.name, "abbreviation": uom.abbreviation}

        if abbreviation and abbreviation.strip().lower() != uom.abbreviation.lower():
            existing = self.uom_repo.get_uom_by_abbreviation(abbreviation)
            if existing and existing.id != uom_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Unit of measure with abbreviation '{abbreviation}' already exists.",
                )

        updated = self.uom_repo.update_uom(uom_id, name=name, abbreviation=abbreviation)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unit of measure '{uom_id}' not found.",
            )

        if self.audit_service and actor_id:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="uom_updated",
                entity_type="unit_of_measure",
                entity_id=updated.id,
                before_value=before_state,
                after_value={"name": updated.name, "abbreviation": updated.abbreviation},
            )
        return updated

    def delete_uom(self, uom_id: str, actor_id: str | None = None) -> bool:
        """Delete a unit of measure."""
        uom = self.get_uom(uom_id)
        before_state = {"name": uom.name, "abbreviation": uom.abbreviation}
        success = self.uom_repo.delete_uom(uom_id)

        if success and self.audit_service and actor_id:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="uom_deleted",
                entity_type="unit_of_measure",
                entity_id=uom_id,
                before_value=before_state,
                after_value=None,
            )
        return success

    def list_product_conversions(self, product_id: str) -> list[ProductUOMConversion]:
        """List all defined conversion ratios for a product."""
        return self.uom_repo.list_product_conversions(product_id)

    def create_or_update_conversion(
        self,
        product_id: str,
        from_uom_id: str,
        to_uom_id: str,
        factor: float,
        actor_id: str | None = None,
    ) -> ProductUOMConversion:
        """
        Define or update a conversion ratio (e.g. 1 from_uom = factor * to_uom).
        """
        if factor <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversion factor must be greater than 0.",
            )
        if from_uom_id == to_uom_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target units of measure cannot be identical.",
            )

        # Validate UoMs exist
        self.get_uom(from_uom_id)
        self.get_uom(to_uom_id)

        existing = self.uom_repo.get_conversion_between(product_id, from_uom_id, to_uom_id)
        before_val = (
            {
                "from_uom_id": existing.from_uom_id,
                "to_uom_id": existing.to_uom_id,
                "factor": float(existing.factor),
            }
            if existing
            else None
        )

        conv = self.uom_repo.create_or_update_conversion(
            product_id=product_id,
            from_uom_id=from_uom_id,
            to_uom_id=to_uom_id,
            factor=factor,
        )

        if self.audit_service and actor_id:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="product_uom_conversion_updated"
                if existing
                else "product_uom_conversion_created",
                entity_type="product_uom_conversion",
                entity_id=conv.id,
                before_value=before_val,
                after_value={
                    "product_id": product_id,
                    "from_uom_id": from_uom_id,
                    "to_uom_id": to_uom_id,
                    "factor": float(factor),
                },
            )
        return conv

    def delete_conversion(self, conversion_id: str, actor_id: str | None = None) -> bool:
        """Delete a product UoM conversion ratio."""
        conv = self.uom_repo.get_conversion_by_id(conversion_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversion '{conversion_id}' not found.",
            )

        before_state = {
            "product_id": conv.product_id,
            "from_uom_id": conv.from_uom_id,
            "to_uom_id": conv.to_uom_id,
            "factor": float(conv.factor),
        }
        success = self.uom_repo.delete_conversion(conversion_id)

        if success and self.audit_service and actor_id:
            self.audit_service.log_action(
                actor_id=actor_id,
                action="product_uom_conversion_deleted",
                entity_type="product_uom_conversion",
                entity_id=conversion_id,
                before_value=before_state,
                after_value=None,
            )
        return success

    def _resolve_factor(self, product_id: str, from_uom_id: str, to_uom_id: str) -> float | None:
        """Helper to resolve conversion ratio via direct link or graph traversal."""
        if from_uom_id == to_uom_id:
            return 1.0

        conversions = self.uom_repo.list_product_conversions(product_id)
        if not conversions:
            return None

        adj: dict[str, list[tuple[str, float]]] = {}
        for c in conversions:
            factor = float(c.factor)
            if factor <= 0:
                continue
            adj.setdefault(c.from_uom_id, []).append((c.to_uom_id, factor))
            adj.setdefault(c.to_uom_id, []).append((c.from_uom_id, 1.0 / factor))

        queue: list[tuple[str, float]] = [(from_uom_id, 1.0)]
        visited: set[str] = {from_uom_id}

        while queue:
            curr_uom, curr_factor = queue.pop(0)
            if curr_uom == to_uom_id:
                return curr_factor
            for neighbor, step_factor in adj.get(curr_uom, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, curr_factor * step_factor))

        return None

    def convert(
        self,
        product_id: str,
        qty: float,
        from_uom_id: str,
        to_uom_id: str,
    ) -> float:
        """
        Convert quantity from one UoM to another for a given product.

        Resolves direct conversion or multi-hop traversal.
        Raises UomConversionError if no conversion path exists.
        """
        if from_uom_id == to_uom_id:
            return float(qty)

        factor = self._resolve_factor(product_id, from_uom_id, to_uom_id)
        if factor is not None:
            return round(float(qty) * factor, 6)

        raise UomConversionError(
            f"No conversion path exists from UoM '{from_uom_id}' to UoM '{to_uom_id}' for product '{product_id}'."
        )

    def convert_to_base_uom(
        self,
        product_id: str,
        qty: float,
        uom_id: str | None,
    ) -> float:
        """
        Convert quantity to the product's base UoM at the stock movement boundary.

        Graceful default: If no uom_id is provided, product has no base UoM,
        or uom_id matches the product's base UoM, quantity is returned 1:1.
        """
        if uom_id is None:
            return float(qty)

        base_uom_id = self.uom_repo.get_product_base_uom_id(product_id)
        if base_uom_id is None or uom_id == base_uom_id:
            return float(qty)

        return self.convert(
            product_id=product_id,
            qty=qty,
            from_uom_id=uom_id,
            to_uom_id=base_uom_id,
        )
