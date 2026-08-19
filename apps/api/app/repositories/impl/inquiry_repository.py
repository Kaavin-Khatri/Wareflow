"""Product inquiry repository implementation."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.portal import ProductInquiry
from app.repositories.interfaces.inquiry_repository import InquiryRepositoryInterface


class InquiryRepository(InquiryRepositoryInterface):
    """SQLAlchemy implementation of inquiry repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, inquiry: ProductInquiry) -> ProductInquiry:
        """Persist a new product inquiry."""
        self._session.add(inquiry)
        self._session.flush()
        self._session.refresh(inquiry)
        return inquiry

    def get_by_id(self, inquiry_id: str) -> ProductInquiry | None:
        """Fetch inquiry by ID with relationships."""
        return (
            self._session.query(ProductInquiry)
            .options(joinedload(ProductInquiry.product), joinedload(ProductInquiry.retailer))
            .filter(ProductInquiry.id == inquiry_id)
            .first()
        )

    def list_for_retailer(self, retailer_id: str) -> list[ProductInquiry]:
        """List inquiries strictly for a specific retailer in chronological order."""
        return (
            self._session.query(ProductInquiry)
            .options(joinedload(ProductInquiry.product), joinedload(ProductInquiry.retailer))
            .filter(ProductInquiry.retailer_id == retailer_id)
            .order_by(ProductInquiry.created_at.desc())
            .all()
        )

    def list_all(
        self,
        status: str | None = None,
        product_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProductInquiry]:
        """List inquiries for staff with optional status/product filters."""
        query = (
            self._session.query(ProductInquiry)
            .options(joinedload(ProductInquiry.product), joinedload(ProductInquiry.retailer))
        )
        if status:
            query = query.filter(ProductInquiry.status == status)
        if product_id:
            query = query.filter(ProductInquiry.product_id == product_id)
        return query.order_by(ProductInquiry.created_at.desc()).offset(skip).limit(limit).all()

    def update(self, inquiry: ProductInquiry) -> ProductInquiry:
        """Update an existing inquiry."""
        self._session.flush()
        self._session.refresh(inquiry)
        return inquiry


class InMemoryInquiryRepository(InquiryRepositoryInterface):
    """In-memory implementation of inquiry repository for unit tests."""

    def __init__(self) -> None:
        self._inquiries: dict[str, ProductInquiry] = {}

    def create(self, inquiry: ProductInquiry) -> ProductInquiry:
        """Persist a new product inquiry."""
        if not inquiry.id:
            inquiry.id = str(uuid.uuid4())
        if not getattr(inquiry, "created_at", None):
            inquiry.created_at = datetime.now(timezone.utc)
        self._inquiries[inquiry.id] = inquiry
        return inquiry

    def get_by_id(self, inquiry_id: str) -> ProductInquiry | None:
        """Fetch inquiry by ID."""
        return self._inquiries.get(inquiry_id)

    def list_for_retailer(self, retailer_id: str) -> list[ProductInquiry]:
        """List inquiries strictly for a specific retailer in chronological order."""
        res = [inq for inq in self._inquiries.values() if inq.retailer_id == retailer_id]
        return sorted(res, key=lambda i: i.created_at, reverse=True)

    def list_all(
        self,
        status: str | None = None,
        product_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProductInquiry]:
        """List inquiries for staff with optional filters."""
        res = list(self._inquiries.values())
        if status:
            res = [i for i in res if i.status == status]
        if product_id:
            res = [i for i in res if i.product_id == product_id]
        res = sorted(res, key=lambda i: i.created_at, reverse=True)
        return res[skip : skip + limit]

    def update(self, inquiry: ProductInquiry) -> ProductInquiry:
        """Update an existing inquiry."""
        self._inquiries[inquiry.id] = inquiry
        return inquiry
