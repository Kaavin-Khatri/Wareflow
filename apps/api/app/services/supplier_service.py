"""
Supplier domain service.

Contains core business logic for vendor management, unique name constraints,
GSTIN validation, contact info checks, and administrative audit logging.
Strictly adheres to the Dependency Inversion Principle (DIP) and SOLID principles.
"""

import re
from typing import Any

from fastapi import HTTPException, status

from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.schemas.suppliers import SupplierCreateRequest, SupplierUpdateRequest
from app.services.audit_service import AuditService

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


class SupplierService:
    """Service handling supplier business rules and lifecycle."""

    def __init__(
        self,
        repository: SupplierRepositoryInterface,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repo = repository
        self._audit = audit_service

    @staticmethod
    def validate_gstin(gstin: str | None) -> None:
        """Validate Indian 15-character GSTIN format if provided."""
        if not gstin:
            return
        cleaned = gstin.strip().upper()
        if not GSTIN_REGEX.match(cleaned):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid GSTIN format. Expected standard 15-character Indian GSTIN (e.g. 27ABCDE1234F1Z5).",
            )

    @staticmethod
    def validate_contact_info(phone: str | None, email: str | None) -> None:
        """Validate phone and email syntax if provided."""
        if email and email.strip() and not EMAIL_REGEX.match(email.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid email address format: '{email}'.",
            )
        if phone and phone.strip():
            digits = re.sub(r"\D", "", phone)
            if len(digits) < 7 or len(digits) > 15:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid phone number '{phone}'. Expected between 7 and 15 digits.",
                )

    def get_supplier(self, supplier_id: str) -> Any:
        """Fetch a single supplier by unique ID."""
        if not supplier_id or not supplier_id.strip():
            raise ValueError("Supplier ID cannot be empty.")
        supplier = self._repo.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID '{supplier_id}' not found.",
            )
        return supplier

    def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Any]:
        """List suppliers with pagination, text search, and active filters."""
        return self._repo.list_suppliers(skip=skip, limit=limit, search=search, is_active=is_active)

    def create_supplier(self, payload: SupplierCreateRequest, actor_id: str | None = None) -> Any:
        """Create a new supplier with duplicate name and syntax validation."""
        # 1. Check duplicate name (case-insensitive)
        existing = self._repo.get_by_name(payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A supplier with the name '{payload.name}' already exists.",
            )

        # 2. Validate GSTIN and contact details
        self.validate_gstin(payload.gstin)
        self.validate_contact_info(payload.phone, payload.email)

        # 3. Persist
        data = payload.model_dump()
        created = self._repo.create_supplier(data)

        # 4. Audit Log
        if self._audit and actor_id:
            supplier_id = getattr(created, "id", None) or data.get("id")
            self._audit.log_action(
                actor_id=actor_id,
                action="supplier_created",
                entity_type="supplier",
                entity_id=str(supplier_id),
                after_value={
                    "name": payload.name,
                    "gstin": payload.gstin,
                    "contact_person": payload.contact_person,
                    "is_active": payload.is_active,
                },
            )

        return created

    def update_supplier(
        self, supplier_id: str, payload: SupplierUpdateRequest, actor_id: str | None = None
    ) -> Any:
        """Update an existing supplier with validation and audit diffs."""
        existing = self.get_supplier(supplier_id)

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return existing

        # Check duplicate name if name is updated
        if "name" in update_data and update_data["name"]:
            new_name = update_data["name"]
            existing_with_name = self._repo.get_by_name(new_name)
            if existing_with_name:
                found_id = (
                    existing_with_name.get("id")
                    if isinstance(existing_with_name, dict)
                    else getattr(existing_with_name, "id", "")
                )
                if found_id != supplier_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"A supplier with the name '{new_name}' already exists.",
                    )

        # Validate GSTIN if updated
        if "gstin" in update_data:
            self.validate_gstin(update_data["gstin"])

        # Validate contact info if updated
        phone = update_data.get("phone", getattr(existing, "phone", None))
        email = update_data.get("email", getattr(existing, "email", None))
        self.validate_contact_info(phone, email)

        # Capture before state for audit
        before_state = {
            "name": getattr(existing, "name", None),
            "contact_person": getattr(existing, "contact_person", None),
            "phone": getattr(existing, "phone", None),
            "email": getattr(existing, "email", None),
            "gstin": getattr(existing, "gstin", None),
            "is_active": getattr(existing, "is_active", None),
        }

        updated = self._repo.update_supplier(supplier_id, update_data)

        # Audit Log
        if self._audit and actor_id and updated:
            after_state = {
                "name": getattr(updated, "name", None),
                "contact_person": getattr(updated, "contact_person", None),
                "phone": getattr(updated, "phone", None),
                "email": getattr(updated, "email", None),
                "gstin": getattr(updated, "gstin", None),
                "is_active": getattr(updated, "is_active", None),
            }
            self._audit.log_action(
                actor_id=actor_id,
                action="supplier_updated",
                entity_type="supplier",
                entity_id=supplier_id,
                before_value=before_state,
                after_value=after_state,
            )

        return updated
