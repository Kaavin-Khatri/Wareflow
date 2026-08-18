"""SQLAlchemy and In-Memory implementations for SalesReturnRepositoryInterface."""


from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.retailer import Retailer, SalesOrder
from app.models.returns import SalesReturn, SalesReturnItem, SalesReturnStatusEnum
from app.repositories.interfaces.sales_return_repository import SalesReturnRepositoryInterface


class SqlAlchemySalesReturnRepository(SalesReturnRepositoryInterface):
    """Production SQLAlchemy implementation of SalesReturnRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, return_id: str) -> SalesReturn | None:
        stmt = (
            select(SalesReturn)
            .where(SalesReturn.id == return_id)
            .options(
                selectinload(SalesReturn.items).selectinload(SalesReturnItem.product),
                selectinload(SalesReturn.items).selectinload(SalesReturnItem.batch),
                selectinload(SalesReturn.retailer),
                selectinload(SalesReturn.sales_order),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        retailer_id: str | None = None,
        sales_order_id: str | None = None,
        status: SalesReturnStatusEnum | None = None,
        search: str | None = None,
    ) -> list[SalesReturn]:
        stmt = (
            select(SalesReturn)
            .options(
                selectinload(SalesReturn.items).selectinload(SalesReturnItem.product),
                selectinload(SalesReturn.items).selectinload(SalesReturnItem.batch),
                selectinload(SalesReturn.retailer),
                selectinload(SalesReturn.sales_order),
            )
            .order_by(SalesReturn.requested_at.desc())
        )

        if retailer_id:
            stmt = stmt.where(SalesReturn.retailer_id == retailer_id)
        if sales_order_id:
            stmt = stmt.where(SalesReturn.sales_order_id == sales_order_id)
        if status:
            stmt = stmt.where(SalesReturn.status == status)
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.outerjoin(SalesReturn.retailer).outerjoin(SalesReturn.sales_order).where(
                (SalesReturn.id.ilike(q))
                | (SalesReturn.reason.ilike(q))
                | (Retailer.name.ilike(q))
                | (SalesOrder.so_number.ilike(q))
            )

        stmt = stmt.offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def create(self, sales_return: SalesReturn) -> SalesReturn:
        self.session.add(sales_return)
        self.session.flush()
        return self.get_by_id(sales_return.id) or sales_return

    def update_status(
        self, return_id: str, status: SalesReturnStatusEnum
    ) -> SalesReturn | None:
        ret = self.get_by_id(return_id)
        if ret:
            ret.status = status
            self.session.flush()
        return ret

    def get_returned_quantities_by_order(self, sales_order_id: str) -> dict[str, float]:
        stmt = (
            select(SalesReturn)
            .where(
                SalesReturn.sales_order_id == sales_order_id,
                SalesReturn.status != SalesReturnStatusEnum.REJECTED,
            )
            .options(selectinload(SalesReturn.items))
        )
        returns = list(self.session.execute(stmt).scalars().all())
        totals: dict[str, float] = {}
        for r in returns:
            for it in r.items:
                totals[it.product_id] = round(totals.get(it.product_id, 0.0) + float(it.qty), 2)
        return totals


class InMemorySalesReturnRepository(SalesReturnRepositoryInterface):
    """In-Memory implementation of SalesReturnRepositoryInterface for unit tests."""

    def __init__(self, initial_data: list[SalesReturn] | None = None) -> None:
        self._returns: dict[str, SalesReturn] = {}
        if initial_data:
            for r in initial_data:
                self._returns[r.id] = r

    def get_by_id(self, return_id: str) -> SalesReturn | None:
        return self._returns.get(return_id)

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        retailer_id: str | None = None,
        sales_order_id: str | None = None,
        status: SalesReturnStatusEnum | None = None,
        search: str | None = None,
    ) -> list[SalesReturn]:
        results = list(self._returns.values())
        if retailer_id:
            results = [r for r in results if r.retailer_id == retailer_id]
        if sales_order_id:
            results = [r for r in results if r.sales_order_id == sales_order_id]
        if status:
            results = [r for r in results if r.status == status]
        if search:
            q = search.strip().lower()
            results = [
                r
                for r in results
                if q in r.id.lower()
                or (r.reason and q in r.reason.lower())
                or (hasattr(r, "retailer") and r.retailer and q in getattr(r.retailer, "name", "").lower())
            ]

        results.sort(key=lambda r: getattr(r, "requested_at", None) or "", reverse=True)
        return results[skip : skip + limit]

    def create(self, sales_return: SalesReturn) -> SalesReturn:
        self._returns[sales_return.id] = sales_return
        return sales_return

    def update_status(
        self, return_id: str, status: SalesReturnStatusEnum
    ) -> SalesReturn | None:
        ret = self._returns.get(return_id)
        if ret:
            ret.status = status
        return ret

    def get_returned_quantities_by_order(self, sales_order_id: str) -> dict[str, float]:
        totals: dict[str, float] = {}
        for r in self._returns.values():
            if r.sales_order_id == sales_order_id and r.status != SalesReturnStatusEnum.REJECTED:
                for it in r.items:
                    prod_id = getattr(it, "product_id", None) or (it.product.id if hasattr(it, "product") and it.product else None)
                    if prod_id:
                        totals[prod_id] = round(totals.get(prod_id, 0.0) + float(it.qty), 2)
        return totals
