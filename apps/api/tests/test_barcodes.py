"""Tests for EAN-13 barcode generation, QR code rendering, and barcode lookup APIs."""

from decimal import Decimal
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.di import get_product_service
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.catalog import Product
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.schemas.products import ProductCreateRequest
from app.services.barcode_service import (
    BarcodeService,
    calculate_ean13_checksum,
    generate_internal_ean13,
)
from app.services.product_service import ProductService

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture()
def product_repo() -> InMemoryProductRepository:
    """Fresh in-memory product repository."""
    return InMemoryProductRepository()


@pytest.fixture()
def product_service(product_repo: InMemoryProductRepository) -> ProductService:
    """ProductService with in-memory repository."""
    return ProductService(repository=product_repo)


@pytest.fixture()
def sample_product(product_service: ProductService) -> Product:
    """Sample product in catalog with auto EAN-13."""
    req = ProductCreateRequest(
        sku="TEST-NAMKEEN-001",
        name="Ratlam Sev 500g",
        wholesale_price=Decimal("120.00"),
        cost_price=Decimal("85.00"),
        reorder_point=20,
        reorder_qty=100,
    )
    return product_service.create_product(req, actor_id="user-owner-1")


@pytest.fixture()
def client(product_service: ProductService) -> TestClient:
    """FastAPI TestClient with overridden dependencies."""
    test_user = CurrentUser(
        id="user-ops-1",
        email="ops@wareflow.local",
        role="Admin",
        permissions=["inventory:read", "inventory:manage"],
    )

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_product_service] = lambda: product_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# Unit Tests: Barcode Calculation & Rendering
# --------------------------------------------------------------------------- #


class TestBarcodeService:
    """Unit tests for BarcodeService and EAN-13 mathematics."""

    def test_calculate_ean13_checksum_standard(self) -> None:
        """Verify checksum calculation against standard GS1 test vectors."""
        # 890103092523 -> check digit 8 (Full 13-digit EAN-13: 8901030925238)
        chk = calculate_ean13_checksum("890103092523")
        assert chk == 8

        # 200000000001 -> check digit 5
        chk2 = calculate_ean13_checksum("200000000001")
        assert chk2 == 5

    def test_calculate_ean13_checksum_invalid_length_raises(self) -> None:
        """Non-12-digit input must raise ValueError."""
        with pytest.raises(ValueError, match="exactly 12 digits"):
            calculate_ean13_checksum("12345")

    def test_generate_internal_ean13_format(self) -> None:
        """Generated internal barcodes must be 13 digits starting with prefix and valid checksum."""
        barcode_val = generate_internal_ean13(prefix="20", sequence_id=123)
        assert len(barcode_val) == 13
        assert barcode_val.startswith("20")
        assert barcode_val.isdigit()

        # Check digit roundtrip
        computed_check = calculate_ean13_checksum(barcode_val[:12])
        assert int(barcode_val[12]) == computed_check

    def test_render_barcode_png_output(self) -> None:
        """render_barcode_png returns valid PNG bytes with PNG magic header."""
        png_bytes = BarcodeService.render_barcode_png("2000000001239")
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 500
        assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    def test_render_barcode_png_alphanumeric_code128_fallback(self) -> None:
        """Alphanumeric SKUs fallback gracefully to Code 128 barcode."""
        png_bytes = BarcodeService.render_barcode_png("SKU-CHEVDO-250G")
        assert isinstance(png_bytes, bytes)
        assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    def test_render_qr_code_png_output(self) -> None:
        """render_qr_code_png returns valid 2D QR code PNG bytes."""
        png_bytes = BarcodeService.render_qr_code_png("https://wareflow.local/p/TEST-123")
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 200
        assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


# --------------------------------------------------------------------------- #
# Integration Tests: Product Service Barcode Integration
# --------------------------------------------------------------------------- #


class TestProductServiceBarcode:
    """Integration tests for product barcode auto-generation and resolution."""

    def test_create_product_auto_generates_ean13(self, product_service: ProductService) -> None:
        """When barcode is omitted, ProductService generates a 13-digit EAN-13 barcode."""
        req = ProductCreateRequest(
            sku="SKU-AUTO-EAN-1",
            name="Bhavnagari Gathiya 200g",
            wholesale_price=Decimal("65.00"),
            cost_price=Decimal("42.00"),
            barcode=None,
        )
        prod = product_service.create_product(req)
        barcode_val = prod.get("barcode") if isinstance(prod, dict) else prod.barcode
        assert barcode_val is not None
        assert len(barcode_val) == 13
        assert barcode_val.startswith("20")
        assert barcode_val.isdigit()

    def test_create_product_preserves_explicit_barcode(
        self, product_service: ProductService
    ) -> None:
        """Explicit manufacturer barcode is preserved."""
        req = ProductCreateRequest(
            sku="SKU-CUSTOM-BARCODE",
            name="Custom Packaged Item",
            wholesale_price=Decimal("150.00"),
            cost_price=Decimal("110.00"),
            barcode="8901234567890",
        )
        prod = product_service.create_product(req)
        barcode_val = prod.get("barcode") if isinstance(prod, dict) else prod.barcode
        assert barcode_val == "8901234567890"

    def test_get_product_by_barcode_resolves(
        self, product_service: ProductService, sample_product: Any
    ) -> None:
        """Lookup by barcode resolves the matching product."""
        barcode_val = (
            sample_product.get("barcode")
            if isinstance(sample_product, dict)
            else sample_product.barcode
        )
        resolved = product_service.get_product_by_barcode(barcode_val)
        assert (
            resolved.get("sku") if isinstance(resolved, dict) else resolved.sku
        ) == "TEST-NAMKEEN-001"

    def test_get_product_by_barcode_fallback_sku(
        self, product_service: ProductService, sample_product: Any
    ) -> None:
        """Lookup by SKU string resolves as fallback if barcode matches SKU."""
        resolved = product_service.get_product_by_barcode("TEST-NAMKEEN-001")
        assert (
            resolved.get("name") if isinstance(resolved, dict) else resolved.name
        ) == "Ratlam Sev 500g"


# --------------------------------------------------------------------------- #
# Endpoint Tests: Router APIs
# --------------------------------------------------------------------------- #


class TestProductBarcodeEndpoints:
    """Test suite for barcode/QR endpoints in FastAPI."""

    def test_get_product_by_barcode_endpoint(self, client: TestClient, sample_product: Any) -> None:
        """GET /products/by-barcode/{barcode} returns product record."""
        barcode_val = (
            sample_product.get("barcode")
            if isinstance(sample_product, dict)
            else sample_product.barcode
        )
        res = client.get(f"/products/by-barcode/{barcode_val}")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["sku"] == "TEST-NAMKEEN-001"
        assert data["name"] == "Ratlam Sev 500g"
        assert data["barcode"] == barcode_val

    def test_get_product_by_barcode_not_found(self, client: TestClient) -> None:
        """GET /products/by-barcode/{barcode} returns 404 for unknown barcode."""
        res = client.get("/products/by-barcode/9999999999999")
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_get_product_barcode_png_endpoint(
        self, client: TestClient, sample_product: Any
    ) -> None:
        """GET /products/{id}/barcode.png returns image/png response."""
        prod_id = (
            sample_product.get("id") if isinstance(sample_product, dict) else sample_product.id
        )
        res = client.get(f"/products/{prod_id}/barcode.png")
        assert res.status_code == status.HTTP_200_OK
        assert res.headers["content-type"] == "image/png"
        assert res.content.startswith(b"\x89PNG\r\n\x1a\n")

    def test_get_product_qr_png_endpoint(self, client: TestClient, sample_product: Any) -> None:
        """GET /products/{id}/qr.png returns image/png response."""
        prod_id = (
            sample_product.get("id") if isinstance(sample_product, dict) else sample_product.id
        )
        res = client.get(f"/products/{prod_id}/qr.png")
        assert res.status_code == status.HTTP_200_OK
        assert res.headers["content-type"] == "image/png"
        assert res.content.startswith(b"\x89PNG\r\n\x1a\n")
