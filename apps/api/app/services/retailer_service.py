"""Retailer domain service with audit logging for credit limit mutations."""

from fastapi import HTTPException, status

from app.models.retailer import Retailer
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.services.audit_service import AuditService


class RetailerService:
    """Service handling retailer accounts and credit limits."""

    def __init__(
        self,
        retailer_repo: RetailerRepository,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repo = retailer_repo
        self._audit = audit_service

    def get_retailer(self, retailer_id: str) -> Retailer:
        """Fetch retailer with 404 validation."""
        retailer = self._repo.get_by_id(retailer_id)
        if not retailer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer with ID '{retailer_id}' not found.",
            )
        return retailer

    def list_retailers(self, skip: int = 0, limit: int = 100) -> list[Retailer]:
        """List wholesale retailers."""
        return self._repo.list_all(skip=skip, limit=limit)

    def update_credit_limit(
        self,
        retailer_id: str,
        new_credit_limit: float,
        actor_id: str | None = None,
    ) -> Retailer:
        """Update credit limit and record immutable audit log entry."""
        if new_credit_limit < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit limit cannot be negative.",
            )

        retailer = self.get_retailer(retailer_id)
        old_limit = float(retailer.credit_limit)

        updated = self._repo.update_credit_limit(retailer_id, new_credit_limit)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer with ID '{retailer_id}' not found.",
            )

        if self._audit and old_limit != new_credit_limit:
            self._audit.log(
                actor_id=actor_id,
                action="retailer_credit_limit_updated",
                entity_type="retailer",
                entity_id=retailer.id,
                before={"name": retailer.name, "credit_limit": old_limit},
                after={"name": retailer.name, "credit_limit": float(new_credit_limit)},
            )

        return updated
