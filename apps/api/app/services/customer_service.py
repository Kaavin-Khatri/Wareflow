"""Customer service orchestrating CRUD operations and direct buyer records."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.models.portal import Customer
from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.customer_repository import CustomerRepositoryInterface
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.schemas.customers import (
    CustomerCreateRequest,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdateRequest,
)


class CustomerService:
    """Business logic and validation for direct walk-in customers."""

    def __init__(
        self,
        customer_repo: CustomerRepositoryInterface,
        audit_repo: AuditRepository | None = None,
        so_repo: SalesOrderRepositoryInterface | None = None,
    ) -> None:
        self.customer_repo = customer_repo
        self.audit_repo = audit_repo
        self.so_repo = so_repo

    def create_customer(
        self, payload: CustomerCreateRequest, current_user: Any = None
    ) -> CustomerResponse:
        """Register a new direct walk-in customer."""
        customer = Customer(
            id=str(uuid.uuid4()),
            name=payload.name.strip(),
            phone=payload.phone.strip() if payload.phone else None,
            email=str(payload.email).strip() if payload.email else None,
            address=payload.address.strip() if payload.address else None,
            notes=payload.notes.strip() if payload.notes else None,
            created_at=datetime.now(UTC),
        )


        saved = self.customer_repo.create(customer)
        self._audit_log(
            action="customer_created",
            target_id=saved.id,
            before=None,
            after=self._customer_to_dict(saved),
            current_user=current_user,
        )

        return self._to_response(saved)

    def update_customer(
        self, customer_id: str, payload: CustomerUpdateRequest, current_user: Any = None
    ) -> CustomerResponse:
        """Update customer details."""
        existing = self._get_customer_or_404(customer_id)
        before_state = self._customer_to_dict(existing)

        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name.strip()
        if payload.phone is not None:
            updates["phone"] = payload.phone.strip() if payload.phone else None
        if payload.email is not None:
            updates["email"] = str(payload.email).strip() if payload.email else None
        if payload.address is not None:
            updates["address"] = payload.address.strip() if payload.address else None
        if payload.notes is not None:
            updates["notes"] = payload.notes.strip() if payload.notes else None

        updated = self.customer_repo.update(customer_id, updates)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found.",
            )

        self._audit_log(
            action="customer_updated",
            target_id=updated.id,
            before=before_state,
            after=self._customer_to_dict(updated),
            current_user=current_user,
        )

        return self._to_response(updated)

    def get_customer(self, customer_id: str) -> CustomerResponse:
        """Fetch customer profile by ID."""
        customer = self._get_customer_or_404(customer_id)
        return self._to_response(customer)

    def list_customers(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> CustomerListResponse:
        """Fetch paginated direct customer records with search filter."""
        items, total = self.customer_repo.list_all(skip=skip, limit=limit, search=search)
        return CustomerListResponse(
            items=[self._to_response(c) for c in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    def delete_customer(self, customer_id: str, current_user: Any = None) -> None:
        """Delete customer if no active sales orders exist."""
        customer = self._get_customer_or_404(customer_id)
        before_state = self._customer_to_dict(customer)

        if self.so_repo:
            orders, total = self.so_repo.list_all(limit=1, buyer_type="customer")
            customer_orders = [o for o in orders if getattr(o, "customer_id", None) == customer_id]
            if customer_orders or total > 0:
                # Check specific order association
                specific_orders, count = self.so_repo.list_all(limit=10, buyer_type="customer")
                if any(getattr(o, "customer_id", None) == customer_id for o in specific_orders):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Cannot delete customer '{customer.name}' with existing sales orders.",
                    )

        deleted = self.customer_repo.delete(customer_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found.",
            )

        self._audit_log(
            action="customer_deleted",
            target_id=customer_id,
            before=before_state,
            after=None,
            current_user=current_user,
        )

    def _get_customer_or_404(self, customer_id: str) -> Customer:
        customer = self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found.",
            )
        return customer

    def _to_response(self, customer: Customer) -> CustomerResponse:
        total_orders = 0
        total_spend = 0.0

        if self.so_repo:
            orders, _ = self.so_repo.list_all(limit=1000, buyer_type="customer")
            customer_orders = [
                o for o in orders if getattr(o, "customer_id", None) == customer.id
            ]
            total_orders = len(customer_orders)
            total_spend = sum(
                float(o.total_amount)
                for o in customer_orders
                if getattr(o, "status", "") != "cancelled"
            )

        return CustomerResponse(
            id=customer.id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email,
            address=customer.address,
            notes=customer.notes,
            created_at=customer.created_at,
            total_orders_count=total_orders,
            total_spend=round(total_spend, 2),
        )

    def _customer_to_dict(self, customer: Customer) -> dict[str, Any]:
        return {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
            "notes": customer.notes,
        }

    def _audit_log(
        self,
        action: str,
        target_id: str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
        current_user: Any = None,
    ) -> None:
        if not self.audit_repo:
            return
        actor_id = getattr(current_user, "id", None) or "system"
        self.audit_repo.create_log(
            actor_id=actor_id,
            action=action,
            entity_type="customer",
            entity_id=target_id,
            before_value=before,
            after_value=after,
        )

