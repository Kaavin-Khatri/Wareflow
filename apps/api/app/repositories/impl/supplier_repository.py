"""
Concrete implementations of SupplierRepositoryInterface.

Includes InMemorySupplierRepository (for unit tests and DIP proof) and
SqlAlchemySupplierRepository (for PostgreSQL/SQLite persistence via SQLAlchemy).
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface


class InMemorySupplierRepository(SupplierRepositoryInterface):
    """In-memory implementation of SupplierRepositoryInterface for testing and DIP."""

    def __init__(self, seed_suppliers: list[Any] | None = None) -> None:
        self._suppliers: dict[str, dict[str, Any]] = {}
        for item in seed_suppliers or []:
            if isinstance(item, Supplier):
                self._suppliers[item.id] = {
                    "id": item.id,
                    "name": item.name,
                    "contact_person": getattr(item, "contact_person", None),
                    "email": getattr(item, "email", None),
                    "phone": getattr(item, "phone", None),
                    "gstin": getattr(item, "gstin", None),
                    "address": getattr(item, "address", None),
                    "fssai_license_no": getattr(item, "fssai_license_no", None),
                    "fssai_expiry_date": getattr(item, "fssai_expiry_date", None),
                    "is_active": getattr(item, "is_active", True),
                }
            else:
                self._suppliers[item["id"]] = dict(item)

    def get_by_id(self, supplier_id: str) -> Any:
        item = self._suppliers.get(supplier_id)
        if not item:
            return None
        return Supplier(**item) if isinstance(item, dict) else item

    def get_by_name(self, name: str) -> Any:
        target = name.strip().lower()
        for s in self._suppliers.values():
            s_name = s.get("name", "") if isinstance(s, dict) else getattr(s, "name", "")
            if s_name.strip().lower() == target:
                return Supplier(**s) if isinstance(s, dict) else s
        return None

    def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Any]:
        results: list[dict[str, Any]] = list(self._suppliers.values())

        if is_active is not None:
            results = [
                s
                for s in results
                if (s.get("is_active") if isinstance(s, dict) else s.is_active) == is_active
            ]

        if search:
            q = search.strip().lower()
            filtered = []
            for s in results:
                name = (s.get("name", "") if isinstance(s, dict) else s.name).lower()
                contact = (
                    s.get("contact_person", "") if isinstance(s, dict) else (s.contact_person or "")
                ).lower()
                email = (s.get("email", "") if isinstance(s, dict) else (s.email or "")).lower()
                gstin = (s.get("gstin", "") if isinstance(s, dict) else (s.gstin or "")).lower()
                if q in name or q in contact or q in email or q in gstin:
                    filtered.append(s)
            results = filtered

        paginated = results[skip : skip + limit]
        return [Supplier(**s) if isinstance(s, dict) else s for s in paginated]

    def create_supplier(self, data: dict[str, Any]) -> Any:
        supplier_id = data.get("id") or str(uuid.uuid4())
        record = dict(data)
        record["id"] = supplier_id
        if "created_at" not in record or not record["created_at"]:
            record["created_at"] = datetime.now(UTC)
        self._suppliers[supplier_id] = record
        return Supplier(**record)

    def update_supplier(self, supplier_id: str, data: dict[str, Any]) -> Any:
        if supplier_id not in self._suppliers:
            return None
        existing = dict(self._suppliers[supplier_id])
        for k, v in data.items():
            if v is not None:
                existing[k] = v
        self._suppliers[supplier_id] = existing
        return Supplier(**existing)

    def delete_supplier(self, supplier_id: str) -> bool:
        if supplier_id in self._suppliers:
            del self._suppliers[supplier_id]
            return True
        return False


class SqlAlchemySupplierRepository(SupplierRepositoryInterface):
    """SQLAlchemy implementation of SupplierRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, supplier_id: str) -> Supplier | None:
        return self._session.get(Supplier, supplier_id)

    def get_by_name(self, name: str) -> Supplier | None:
        target = name.strip().lower()
        stmt = select(Supplier).where(func.lower(Supplier.name) == target)
        return self._session.execute(stmt).scalar_one_or_none()

    def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Supplier]:
        stmt = select(Supplier)

        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)

        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Supplier.name.ilike(pattern),
                    Supplier.contact_person.ilike(pattern),
                    Supplier.email.ilike(pattern),
                    Supplier.phone.ilike(pattern),
                    Supplier.gstin.ilike(pattern),
                )
            )

        stmt = stmt.order_by(Supplier.name.asc()).offset(skip).limit(limit)
        return list(self._session.execute(stmt).scalars().all())

    def create_supplier(self, data: dict[str, Any]) -> Supplier:
        supplier = Supplier(**data)
        self._session.add(supplier)
        self._session.commit()
        self._session.refresh(supplier)
        return supplier

    def update_supplier(self, supplier_id: str, data: dict[str, Any]) -> Supplier | None:
        supplier = self.get_by_id(supplier_id)
        if not supplier:
            return None

        for k, v in data.items():
            if hasattr(supplier, k) and v is not None:
                setattr(supplier, k, v)

        self._session.commit()
        self._session.refresh(supplier)
        return supplier

    def delete_supplier(self, supplier_id: str) -> bool:
        supplier = self.get_by_id(supplier_id)
        if not supplier:
            return False
        self._session.delete(supplier)
        self._session.commit()
        return True
