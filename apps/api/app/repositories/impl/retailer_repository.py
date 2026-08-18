"""SQLAlchemy and In-Memory implementations of RetailerRepository."""

import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.retailer import Retailer
from app.repositories.interfaces.retailer_repository import RetailerRepository


class SqlAlchemyRetailerRepository(RetailerRepository):
    """Concrete repository persisting and querying Retailer records via SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, retailer_id: str) -> Retailer | None:
        return self._session.scalar(select(Retailer).where(Retailer.id == retailer_id))

    def get_by_name(self, name: str) -> Retailer | None:
        return self._session.scalar(
            select(Retailer).where(Retailer.name.ilike(name.strip()))
        )

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Retailer]:
        stmt = select(Retailer)
        if is_active is not None:
            stmt = stmt.where(Retailer.is_active == is_active)
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Retailer.name.ilike(q),
                    Retailer.contact_person.ilike(q),
                    Retailer.phone.ilike(q),
                    Retailer.email.ilike(q),
                    Retailer.gstin.ilike(q),
                )
            )
        stmt = stmt.order_by(Retailer.name.asc()).offset(skip).limit(limit)
        return list(self._session.scalars(stmt).all())

    def create(self, retailer: Retailer) -> Retailer:
        self._session.add(retailer)
        self._session.commit()
        self._session.refresh(retailer)
        return retailer

    def update(self, retailer_id: str, updates: dict[str, Any]) -> Retailer | None:
        retailer = self.get_by_id(retailer_id)
        if not retailer:
            return None
        for key, value in updates.items():
            if hasattr(retailer, key):
                setattr(retailer, key, value)
        self._session.commit()
        self._session.refresh(retailer)
        return retailer

    def update_credit_limit(self, retailer_id: str, new_limit: float) -> Retailer | None:
        retailer = self.get_by_id(retailer_id)
        if not retailer:
            return None
        retailer.credit_limit = new_limit
        self._session.commit()
        self._session.refresh(retailer)
        return retailer


class InMemoryRetailerRepository(RetailerRepository):
    """In-memory mock repository for fast, zero-DB unit testing."""

    def __init__(self, initial_data: list[Retailer] | None = None) -> None:
        self._retailers: dict[str, Retailer] = {}
        if initial_data:
            for r in initial_data:
                self._retailers[r.id] = r

    def get_by_id(self, retailer_id: str) -> Retailer | None:
        return self._retailers.get(retailer_id)

    def get_by_name(self, name: str) -> Retailer | None:
        norm = name.strip().lower()
        for r in self._retailers.values():
            if r.name.strip().lower() == norm:
                return r
        return None

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Retailer]:
        results = list(self._retailers.values())
        if is_active is not None:
            results = [r for r in results if r.is_active == is_active]
        if search:
            q = search.strip().lower()
            results = [
                r
                for r in results
                if q in (r.name or "").lower()
                or q in (r.contact_person or "").lower()
                or q in (r.phone or "").lower()
                or q in (r.email or "").lower()
                or q in (r.gstin or "").lower()
            ]
        results.sort(key=lambda r: (r.name or "").lower())
        return results[skip : skip + limit]

    def create(self, retailer: Retailer) -> Retailer:
        if not retailer.id:
            retailer.id = str(uuid.uuid4())
        self._retailers[retailer.id] = retailer
        return retailer

    def update(self, retailer_id: str, updates: dict[str, Any]) -> Retailer | None:
        retailer = self.get_by_id(retailer_id)
        if not retailer:
            return None
        for key, value in updates.items():
            if hasattr(retailer, key):
                setattr(retailer, key, value)
        return retailer

    def update_credit_limit(self, retailer_id: str, new_limit: float) -> Retailer | None:
        retailer = self.get_by_id(retailer_id)
        if not retailer:
            return None
        retailer.credit_limit = new_limit
        return retailer
