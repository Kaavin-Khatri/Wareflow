"""SQLAlchemy and In-Memory implementations for CustomerRepositoryInterface."""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.portal import Customer
from app.repositories.interfaces.customer_repository import CustomerRepositoryInterface


class SqlAlchemyCustomerRepository(CustomerRepositoryInterface):
    """Production SQLAlchemy implementation of CustomerRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, customer_id: str) -> Customer | None:
        stmt = select(Customer).where(Customer.id == customer_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> tuple[list[Customer], int]:
        stmt = select(Customer)

        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Customer.name.ilike(q),
                    Customer.phone.ilike(q),
                    Customer.email.ilike(q),
                    Customer.notes.ilike(q),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
        items = list(self.session.execute(stmt).scalars().all())

        return items, total

    def create(self, customer: Customer) -> Customer:
        self.session.add(customer)
        self.session.flush()
        return customer

    def update(self, customer_id: str, updates: dict[str, Any]) -> Customer | None:
        customer = self.get_by_id(customer_id)
        if not customer:
            return None

        for key, value in updates.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        self.session.flush()
        return customer

    def delete(self, customer_id: str) -> bool:
        customer = self.get_by_id(customer_id)
        if not customer:
            return False

        self.session.delete(customer)
        self.session.flush()
        return True


class InMemoryCustomerRepository(CustomerRepositoryInterface):
    """In-Memory implementation of CustomerRepositoryInterface for unit testing."""

    def __init__(self, initial_data: list[Customer] | None = None) -> None:
        self._customers: dict[str, Customer] = {}
        if initial_data:
            for c in initial_data:
                self._customers[c.id] = c

    def get_by_id(self, customer_id: str) -> Customer | None:
        return self._customers.get(customer_id)

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> tuple[list[Customer], int]:
        results = list(self._customers.values())

        if search:
            q = search.strip().lower()
            results = [
                c
                for c in results
                if q in c.name.lower()
                or (c.phone and q in c.phone.lower())
                or (c.email and q in c.email.lower())
                or (c.notes and q in c.notes.lower())
            ]

        total = len(results)
        results.sort(key=lambda c: getattr(c, "created_at", None) or "", reverse=True)
        return results[skip : skip + limit], total

    def create(self, customer: Customer) -> Customer:
        self._customers[customer.id] = customer
        return customer

    def update(self, customer_id: str, updates: dict[str, Any]) -> Customer | None:
        customer = self._customers.get(customer_id)
        if not customer:
            return None

        for key, value in updates.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        return customer

    def delete(self, customer_id: str) -> bool:
        if customer_id in self._customers:
            del self._customers[customer_id]
            return True
        return False
