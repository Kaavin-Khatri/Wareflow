"""SQLAlchemy and In-Memory implementations of PaymentRepositoryInterface."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.billing import Payment
from app.repositories.interfaces.payment_repository import PaymentRepositoryInterface


class SqlAlchemyPaymentRepository(PaymentRepositoryInterface):
    """PostgreSQL SQLAlchemy implementation of Payment repository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payment: Payment) -> Payment:
        """Persist a new payment record."""
        self.session.add(payment)
        self.session.flush()
        return payment

    def get_by_id(self, payment_id: str) -> Payment | None:
        """Fetch payment by unique ID."""
        stmt = (
            select(Payment)
            .options(
                joinedload(Payment.invoice),
                joinedload(Payment.retailer),
                joinedload(Payment.customer),
            )
            .where(Payment.id == payment_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_invoice_id(self, invoice_id: str) -> list[Payment]:
        """Fetch all payments recorded against an invoice."""
        stmt = (
            select(Payment)
            .options(joinedload(Payment.retailer), joinedload(Payment.customer))
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.paid_at.asc(), Payment.created_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_by_retailer_id(self, retailer_id: str) -> list[Payment]:
        """Fetch all payments received from a specific retailer."""
        stmt = (
            select(Payment)
            .options(joinedload(Payment.invoice))
            .where(Payment.retailer_id == retailer_id)
            .order_by(Payment.paid_at.asc(), Payment.created_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_total_paid_for_invoice(self, invoice_id: str) -> float:
        """Calculate cumulative payments made towards an invoice."""
        stmt = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.invoice_id == invoice_id
        )
        return float(self.session.execute(stmt).scalar_one())

    def list_all(self, skip: int = 0, limit: int = 100) -> tuple[list[Payment], int]:
        """List all payments with pagination."""
        count_stmt = select(func.count(Payment.id))
        total = self.session.execute(count_stmt).scalar_one()

        stmt = (
            select(Payment)
            .options(joinedload(Payment.invoice), joinedload(Payment.retailer))
            .order_by(desc(Payment.paid_at))
            .offset(skip)
            .limit(limit)
        )
        items = list(self.session.execute(stmt).scalars().all())
        return items, total


class InMemoryPaymentRepository(PaymentRepositoryInterface):
    """In-Memory implementation of Payment repository for zero-IO testing."""

    def __init__(self, seed_payments: list[Payment | dict[str, Any]] | None = None) -> None:
        self._payments: dict[str, Payment] = {}
        for p in seed_payments or []:
            if isinstance(p, Payment):
                self._payments[p.id] = p

    def create(self, payment: Payment) -> Payment:
        self._payments[payment.id] = payment
        return payment

    def get_by_id(self, payment_id: str) -> Payment | None:
        return self._payments.get(payment_id)

    def list_by_invoice_id(self, invoice_id: str) -> list[Payment]:
        matched = [p for p in self._payments.values() if p.invoice_id == invoice_id]
        return sorted(
            matched,
            key=lambda x: (
                getattr(x, "paid_at", datetime.min),
                getattr(x, "created_at", datetime.min),
            ),
        )

    def list_by_retailer_id(self, retailer_id: str) -> list[Payment]:
        matched = [p for p in self._payments.values() if p.retailer_id == retailer_id]
        return sorted(
            matched,
            key=lambda x: (
                getattr(x, "paid_at", datetime.min),
                getattr(x, "created_at", datetime.min),
            ),
        )

    def get_total_paid_for_invoice(self, invoice_id: str) -> float:
        return sum(float(p.amount) for p in self._payments.values() if p.invoice_id == invoice_id)

    def list_all(self, skip: int = 0, limit: int = 100) -> tuple[list[Payment], int]:
        all_sorted = sorted(
            self._payments.values(),
            key=lambda x: getattr(x, "paid_at", datetime.now(UTC)),
            reverse=True,
        )
        total = len(all_sorted)
        return all_sorted[skip : skip + limit], total
