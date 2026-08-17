"""
Dependency injection container and provider factories.

Wires FastAPI Depends() factories to hand services their repository
ABSTRACTIONS (interfaces), never concrete implementation classes directly.

Swapping an implementation here requires modifying zero service code (DIP).
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.impl.profile_repository import SqlAlchemyProfileRepository
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.services.product_service import ProductService
from app.services.profile_service import ProfileService
from app.services.staff_service import StaffService


@lru_cache
def get_product_repository() -> ProductRepositoryInterface:
    """
    Factory for ProductRepositoryInterface.

    Returns the active repository implementation.
    To swap to SQLAlchemy or another database backend, change only this factory.
    """
    return InMemoryProductRepository()


def get_product_service(
    repo: ProductRepositoryInterface = Depends(get_product_repository),
) -> ProductService:
    """
    Factory for ProductService.

    Injects the repository abstraction via Depends().
    Service never knows which concrete repository is used.
    """
    return ProductService(repository=repo)


def get_profile_repository(db: Session = Depends(get_db_session)) -> ProfileRepository:
    """Factory for ProfileRepository interface."""
    return SqlAlchemyProfileRepository(session=db)


def get_profile_service(
    repo: ProfileRepository = Depends(get_profile_repository),
) -> ProfileService:
    """Factory for ProfileService."""
    return ProfileService(profile_repo=repo)


def get_staff_service(
    repo: ProfileRepository = Depends(get_profile_repository),
) -> StaffService:
    """Factory for StaffService."""
    return StaffService(profile_repo=repo)
