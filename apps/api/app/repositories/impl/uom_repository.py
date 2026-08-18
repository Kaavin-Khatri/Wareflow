"""UoM Repository implementations: SQLAlchemy and In-Memory."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import Product
from app.models.uom import ProductUOMConversion, UnitOfMeasure
from app.repositories.interfaces.uom_repository import UomRepositoryInterface


class SqlAlchemyUomRepository(UomRepositoryInterface):
    """PostgreSQL SQLAlchemy implementation of UomRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_uoms(self) -> list[UnitOfMeasure]:
        stmt = select(UnitOfMeasure).order_by(UnitOfMeasure.name.asc())
        return list(self.session.scalars(stmt).all())

    def get_uom_by_id(self, uom_id: str) -> UnitOfMeasure | None:
        return self.session.get(UnitOfMeasure, uom_id)

    def get_uom_by_abbreviation(self, abbreviation: str) -> UnitOfMeasure | None:
        stmt = select(UnitOfMeasure).where(
            func.lower(UnitOfMeasure.abbreviation) == abbreviation.strip().lower()
        )
        return self.session.scalars(stmt).first()

    def create_uom(self, name: str, abbreviation: str) -> UnitOfMeasure:
        uom = UnitOfMeasure(
            id=str(uuid.uuid4()),
            name=name.strip(),
            abbreviation=abbreviation.strip(),
        )
        self.session.add(uom)
        self.session.flush()
        return uom

    def update_uom(
        self, uom_id: str, name: str | None = None, abbreviation: str | None = None
    ) -> UnitOfMeasure | None:
        uom = self.get_uom_by_id(uom_id)
        if not uom:
            return None
        if name is not None:
            uom.name = name.strip()
        if abbreviation is not None:
            uom.abbreviation = abbreviation.strip()
        self.session.flush()
        return uom

    def delete_uom(self, uom_id: str) -> bool:
        uom = self.get_uom_by_id(uom_id)
        if not uom:
            return False
        self.session.delete(uom)
        self.session.flush()
        return True

    def list_product_conversions(self, product_id: str) -> list[ProductUOMConversion]:
        stmt = (
            select(ProductUOMConversion)
            .options(
                joinedload(ProductUOMConversion.from_uom),
                joinedload(ProductUOMConversion.to_uom),
            )
            .where(ProductUOMConversion.product_id == product_id)
            .order_by(ProductUOMConversion.created_at.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_conversion_by_id(self, conversion_id: str) -> ProductUOMConversion | None:
        stmt = (
            select(ProductUOMConversion)
            .options(
                joinedload(ProductUOMConversion.from_uom),
                joinedload(ProductUOMConversion.to_uom),
            )
            .where(ProductUOMConversion.id == conversion_id)
        )
        return self.session.scalars(stmt).first()

    def get_conversion_between(
        self, product_id: str, from_uom_id: str, to_uom_id: str
    ) -> ProductUOMConversion | None:
        stmt = select(ProductUOMConversion).where(
            ProductUOMConversion.product_id == product_id,
            ProductUOMConversion.from_uom_id == from_uom_id,
            ProductUOMConversion.to_uom_id == to_uom_id,
        )
        return self.session.scalars(stmt).first()

    def create_or_update_conversion(
        self, product_id: str, from_uom_id: str, to_uom_id: str, factor: float
    ) -> ProductUOMConversion:
        existing = self.get_conversion_between(product_id, from_uom_id, to_uom_id)
        if existing:
            existing.factor = factor
            self.session.flush()
            return existing

        conversion = ProductUOMConversion(
            id=str(uuid.uuid4()),
            product_id=product_id,
            from_uom_id=from_uom_id,
            to_uom_id=to_uom_id,
            factor=factor,
        )
        self.session.add(conversion)
        self.session.flush()
        # reload relationships
        return self.get_conversion_by_id(conversion.id) or conversion

    def delete_conversion(self, conversion_id: str) -> bool:
        stmt = delete(ProductUOMConversion).where(ProductUOMConversion.id == conversion_id)
        result = self.session.execute(stmt)
        self.session.flush()
        return (result.rowcount or 0) > 0

    def get_product_base_uom_id(self, product_id: str) -> str | None:
        stmt = select(Product.base_uom_id).where(Product.id == product_id)
        return self.session.scalars(stmt).first()


class InMemoryUomRepository(UomRepositoryInterface):
    """In-Memory mock implementation of UomRepositoryInterface for zero-dependency tests."""

    def __init__(
        self,
        seed_uoms: list[dict[str, Any]] | None = None,
        seed_conversions: list[dict[str, Any]] | None = None,
        seed_products: list[dict[str, Any]] | None = None,
    ) -> None:
        self.uoms: dict[str, dict[str, Any]] = {}
        self.conversions: dict[str, dict[str, Any]] = {}
        self.products: dict[str, dict[str, Any]] = {}

        if seed_uoms:
            for u in seed_uoms:
                self.uoms[u["id"]] = {
                    "id": u["id"],
                    "name": u["name"],
                    "abbreviation": u["abbreviation"],
                    "created_at": datetime.now(UTC),
                }

        if seed_conversions:
            for c in seed_conversions:
                self.conversions[c["id"]] = {
                    "id": c["id"],
                    "product_id": c["product_id"],
                    "from_uom_id": c["from_uom_id"],
                    "to_uom_id": c["to_uom_id"],
                    "factor": float(c["factor"]),
                    "created_at": datetime.now(UTC),
                }

        if seed_products:
            for p in seed_products:
                self.products[p["id"]] = {
                    "id": p["id"],
                    "base_uom_id": p.get("base_uom_id"),
                }

    def _to_uom_model(self, data: dict[str, Any]) -> UnitOfMeasure:
        uom = UnitOfMeasure(
            id=data["id"],
            name=data["name"],
            abbreviation=data["abbreviation"],
        )
        uom.created_at = data.get("created_at", datetime.now(UTC))
        return uom

    def _to_conversion_model(self, data: dict[str, Any]) -> ProductUOMConversion:
        conv = ProductUOMConversion(
            id=data["id"],
            product_id=data["product_id"],
            from_uom_id=data["from_uom_id"],
            to_uom_id=data["to_uom_id"],
            factor=data["factor"],
        )
        conv.created_at = data.get("created_at", datetime.now(UTC))
        if data["from_uom_id"] in self.uoms:
            conv.from_uom = self._to_uom_model(self.uoms[data["from_uom_id"]])
        if data["to_uom_id"] in self.uoms:
            conv.to_uom = self._to_uom_model(self.uoms[data["to_uom_id"]])
        return conv

    def list_uoms(self) -> list[UnitOfMeasure]:
        sorted_items = sorted(self.uoms.values(), key=lambda x: x["name"])
        return [self._to_uom_model(u) for u in sorted_items]

    def get_uom_by_id(self, uom_id: str) -> UnitOfMeasure | None:
        data = self.uoms.get(uom_id)
        return self._to_uom_model(data) if data else None

    def get_uom_by_abbreviation(self, abbreviation: str) -> UnitOfMeasure | None:
        abbr = abbreviation.strip().lower()
        for u in self.uoms.values():
            if u["abbreviation"].lower() == abbr:
                return self._to_uom_model(u)
        return None

    def create_uom(self, name: str, abbreviation: str) -> UnitOfMeasure:
        uom_id = str(uuid.uuid4())
        data = {
            "id": uom_id,
            "name": name.strip(),
            "abbreviation": abbreviation.strip(),
            "created_at": datetime.now(UTC),
        }
        self.uoms[uom_id] = data
        return self._to_uom_model(data)

    def update_uom(
        self, uom_id: str, name: str | None = None, abbreviation: str | None = None
    ) -> UnitOfMeasure | None:
        data = self.uoms.get(uom_id)
        if not data:
            return None
        if name is not None:
            data["name"] = name.strip()
        if abbreviation is not None:
            data["abbreviation"] = abbreviation.strip()
        return self._to_uom_model(data)

    def delete_uom(self, uom_id: str) -> bool:
        if uom_id in self.uoms:
            del self.uoms[uom_id]
            return True
        return False

    def list_product_conversions(self, product_id: str) -> list[ProductUOMConversion]:
        items = [c for c in self.conversions.values() if c["product_id"] == product_id]
        return [self._to_conversion_model(c) for c in items]

    def get_conversion_by_id(self, conversion_id: str) -> ProductUOMConversion | None:
        data = self.conversions.get(conversion_id)
        return self._to_conversion_model(data) if data else None

    def get_conversion_between(
        self, product_id: str, from_uom_id: str, to_uom_id: str
    ) -> ProductUOMConversion | None:
        for c in self.conversions.values():
            if (
                c["product_id"] == product_id
                and c["from_uom_id"] == from_uom_id
                and c["to_uom_id"] == to_uom_id
            ):
                return self._to_conversion_model(c)
        return None

    def create_or_update_conversion(
        self, product_id: str, from_uom_id: str, to_uom_id: str, factor: float
    ) -> ProductUOMConversion:
        existing = self.get_conversion_between(product_id, from_uom_id, to_uom_id)
        if existing:
            self.conversions[existing.id]["factor"] = float(factor)
            return self._to_conversion_model(self.conversions[existing.id])

        conv_id = str(uuid.uuid4())
        data = {
            "id": conv_id,
            "product_id": product_id,
            "from_uom_id": from_uom_id,
            "to_uom_id": to_uom_id,
            "factor": float(factor),
            "created_at": datetime.now(UTC),
        }
        self.conversions[conv_id] = data
        return self._to_conversion_model(data)

    def delete_conversion(self, conversion_id: str) -> bool:
        if conversion_id in self.conversions:
            del self.conversions[conversion_id]
            return True
        return False

    def get_product_base_uom_id(self, product_id: str) -> str | None:
        prod = self.products.get(product_id)
        return prod.get("base_uom_id") if prod else None
