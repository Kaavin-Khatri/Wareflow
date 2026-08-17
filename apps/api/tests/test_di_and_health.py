"""Tests for health endpoint, DB health probe, and DIP container verification."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.di import get_product_repository, get_product_service
from app.main import app
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.services.product_service import ProductService


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify /health returns status: ok."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_db_health_endpoint():
    """Verify /health/db executes SELECT 1 and returns connected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/db")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "connected"}


def test_dip_swappable_repository_zero_service_change():
    """
    DIP Proof: ProductService depends solely on ProductRepositoryInterface.

    Swapping the repository implementation requires zero changes to ProductService code.
    """

    # Custom mock implementation
    class MockCustomRepository(ProductRepositoryInterface):
        def get_by_id(self, product_id: str) -> dict[str, str] | None:
            return {"id": product_id, "name": "Mock Widget", "price": "19.99"}

        def list_all(self) -> list[dict[str, str]]:
            return [{"id": "1", "name": "Mock Widget"}]

    # In-memory implementation
    seed = [{"id": "seed-1", "name": "Seed Item"}]
    in_memory_repo = InMemoryProductRepository(seed_data=seed)

    # Both plug directly into ProductService without any service modifications
    service_with_in_memory = ProductService(repository=in_memory_repo)
    service_with_mock = ProductService(repository=MockCustomRepository())

    assert service_with_in_memory.get_product("seed-1") == {
        "id": "seed-1",
        "name": "Seed Item",
    }
    assert service_with_mock.get_product("any-id") == {
        "id": "any-id",
        "name": "Mock Widget",
        "price": "19.99",
    }


def test_di_container_wires_service():
    """Verify FastAPI Depends container resolves repository and service."""
    repo = get_product_repository()
    assert isinstance(repo, ProductRepositoryInterface)

    service = get_product_service(repo=repo)
    assert isinstance(service, ProductService)
