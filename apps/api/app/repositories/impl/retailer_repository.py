"""SQLAlchemy implementation of RetailerRepository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.retailer import Retailer
from app.repositories.interfaces.retailer_repository import RetailerRepository


class SqlAlchemyRetailerRepository(RetailerRepository):
    """Concrete repository persisting and querying Retailer records via SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, retailer_id: str) -> Retailer | None:
        return self._session.scalar(select(Retailer).where(Retailer.id == retailer_id))

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Retailer]:
        return list(self._session.scalars(select(Retailer).offset(skip).limit(limit)).all())

    def update_credit_limit(self, retailer_id: str, new_limit: float) -> Retailer | None:
        retailer = self.get_by_id(retailer_id)
        if not retailer:
            return None
        retailer.credit_limit = new_limit
        self._session.commit()
        self._session.refresh(retailer)
        return retailer
