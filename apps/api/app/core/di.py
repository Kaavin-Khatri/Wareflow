"""
Dependency injection container and provider factories.

Wires FastAPI Depends() factories to hand services their repository
ABSTRACTIONS (interfaces), never concrete implementation classes directly.

Swapping an implementation here requires modifying zero service code (DIP).
"""

from functools import lru_cache

from fastapi import Depends

from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.services.product_service import ProductService


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
