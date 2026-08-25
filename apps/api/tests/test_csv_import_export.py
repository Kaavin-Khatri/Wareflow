"""Unit and API integration tests for bulk CSV product import, preview, upsert, and export."""

from decimal import Decimal
import io
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.di import get_product_import_service, get_product_service
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.repositories.impl.product_repository import InMemoryProductRepository
from app.schemas.products import ProductCreateRequest
from app.services.import_service import ProductImportService
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
def import_service(product_repo: InMemoryProductRepository) -> ProductImportService:
    """ProductImportService with in-memory repository."""
    return ProductImportService(repository=product_repo)


@pytest.fixture()
def sample_csv() -> str:
    """Sample CSV payload with valid, create, and invalid rows."""
    return (
        "sku,name,wholesale_price,cost_price,category,unit,hsn_code,barcode,reorder_point,reorder_qty,description\n"
        "NAMKEEN-SEV-500G,Ratlam Sev 500g,120.00,85.00,Namkeen & Snacks,Packet,21069099,,20,100,Crispy spiced gram flour\n"
        "GRAIN-RICE-25KG,Basmati Rice 25kg,2450.00,2100.00,Grains & Staples,Bag,10063020,,10,30,Premium aged rice\n"
    )


@pytest.fixture()
def client(product_service: ProductService, import_service: ProductImportService) -> TestClient:
    """FastAPI TestClient with overridden dependencies."""
    test_user = CurrentUser(
        id="user-admin-1",
        email="admin@wareflow.local",
        role="Admin",
        permissions=["inventory:read", "inventory:manage"],
    )

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_product_service] = lambda: product_service
    app.dependency_overrides[get_product_import_service] = lambda: import_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# Unit Tests: ProductImportService
# --------------------------------------------------------------------------- #


class TestProductImportService:
    """Unit test suite for CSV import parsing, validation, dry-run, and upsert."""

    def test_preview_valid_csv_dry_run(
        self, import_service: ProductImportService, sample_csv: str
    ) -> None:
        """Dry-run preview marks new SKUs as 'create' without writing to repository."""
        preview = import_service.preview_import(sample_csv)

        assert preview.dry_run is True
        assert preview.summary.total_rows == 2
        assert preview.summary.create_count == 2
        assert preview.summary.update_count == 0
        assert preview.summary.reject_count == 0

        assert len(preview.rows) == 2
        assert preview.rows[0].action == "create"
        assert preview.rows[0].sku == "NAMKEEN-SEV-500G"
        assert preview.rows[0].wholesale_price == 120.0
        assert len(preview.rows[0].errors) == 0

    def test_execute_import_persists_products_and_categories(
        self,
        import_service: ProductImportService,
        product_repo: InMemoryProductRepository,
        sample_csv: str,
    ) -> None:
        """Executing import creates products in repository and auto-creates categories and EAN-13."""
        result = import_service.execute_import(sample_csv, actor_id="user-1")

        assert result.dry_run is False
        assert result.summary.create_count == 2
        assert result.summary.reject_count == 0

        # Verify products in repo
        prod1 = product_repo.get_by_sku("NAMKEEN-SEV-500G")
        assert prod1 is not None
        assert prod1["name"] == "Ratlam Sev 500g"
        assert float(prod1["wholesale_price"]) == 120.0
        assert len(prod1["barcode"]) == 13
        assert prod1["barcode"].startswith("20")

        # Verify category created
        categories = product_repo.list_categories()
        assert any(c["name"] == "Namkeen & Snacks" for c in categories)

    def test_idempotent_reimport_updates_existing_sku(
        self,
        import_service: ProductImportService,
        product_repo: InMemoryProductRepository,
        sample_csv: str,
    ) -> None:
        """Re-importing a CSV updates existing products instead of duplicating or failing."""
        # First import
        import_service.execute_import(sample_csv, actor_id="user-1")

        # Second import with updated price
        updated_csv = (
            "sku,name,wholesale_price,cost_price,category,unit,hsn_code,barcode,reorder_point,reorder_qty,description\n"
            "NAMKEEN-SEV-500G,Ratlam Sev 500g Premium,135.00,90.00,Namkeen & Snacks,Packet,21069099,,25,120,Updated desc\n"
        )
        preview = import_service.preview_import(updated_csv)
        assert preview.summary.update_count == 1
        assert preview.summary.create_count == 0
        assert preview.rows[0].action == "update"

        res = import_service.execute_import(updated_csv, actor_id="user-1")
        assert res.summary.update_count == 1

        # Check updated values
        prod = product_repo.get_by_sku("NAMKEEN-SEV-500G")
        assert prod["name"] == "Ratlam Sev 500g Premium"
        assert float(prod["wholesale_price"]) == 135.0
        assert prod["reorder_point"] == 25

    def test_invalid_rows_are_rejected_with_specific_errors(
        self, import_service: ProductImportService
    ) -> None:
        """Invalid rows (missing SKU, negative price, bad numbers) are rejected with clear reasons."""
        bad_csv = (
            "sku,name,wholesale_price,cost_price,category,unit,hsn_code,barcode,reorder_point,reorder_qty,description\n"
            ",Missing SKU Item,100.00,80.00,,,,,,,\n"
            "SKU-BAD-PRICE,Bad Price Item,-50.00,40.00,,,,,,,\n"
            "SKU-NO-NAME,,150.00,100.00,,,,,,,\n"
            "SKU-VALID,Valid Item,200.00,150.00,,,,,,,\n"
        )
        preview = import_service.preview_import(bad_csv)

        assert preview.summary.total_rows == 4
        assert preview.summary.valid_count == 1
        assert preview.summary.reject_count == 3
        assert preview.summary.create_count == 1

        # Row 1 error: missing SKU
        assert preview.rows[0].action == "reject"
        assert any("SKU" in err for err in preview.rows[0].errors)

        # Row 2 error: negative price
        assert preview.rows[1].action == "reject"
        assert any("negative" in err for err in preview.rows[1].errors)

        # Row 3 error: missing name
        assert preview.rows[2].action == "reject"
        assert any("name" in err.lower() for err in preview.rows[2].errors)

        # Row 4: valid
        assert preview.rows[3].action == "create"

    def test_generate_csv_template(self, import_service: ProductImportService) -> None:
        """Template generation produces valid CSV with headers and sample rows."""
        template = import_service.generate_csv_template()
        lines = template.strip().split("\n")
        assert len(lines) >= 3
        assert "sku,name,wholesale_price" in lines[0]
        assert "NAMKEEN-SEV-500G" in lines[1]

    def test_export_catalog_csv(
        self,
        import_service: ProductImportService,
        product_repo: InMemoryProductRepository,
    ) -> None:
        """Export generates CSV string containing existing catalog items."""
        product_repo.create_product({
            "sku": "SKU-EXPORT-1",
            "name": "Exported Biscuit 100g",
            "wholesale_price": 25.0,
            "cost_price": 18.0,
            "unit": "Packet",
            "barcode": "2000000009999",
            "is_active": True,
        })

        csv_content = import_service.export_catalog_csv()
        assert "sku,name,category,wholesale_price" in csv_content
        assert "SKU-EXPORT-1" in csv_content
        assert "Exported Biscuit 100g" in csv_content


# --------------------------------------------------------------------------- #
# Endpoint Tests: FastAPI Routes
# --------------------------------------------------------------------------- #


class TestProductImportExportEndpoints:
    """API endpoint tests for POST /products/import, GET /products/export.csv, and template."""

    def test_import_endpoint_dry_run_preview(self, client: TestClient, sample_csv: str) -> None:
        """POST /products/import?dry_run=true returns 200 with preview schema."""
        files = {"file": ("products.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv")}
        res = client.post("/products/import?dry_run=true", files=files)

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["dry_run"] is True
        assert data["summary"]["total_rows"] == 2
        assert data["summary"]["create_count"] == 2
        assert len(data["rows"]) == 2

    def test_import_endpoint_commit_creates_products(
        self, client: TestClient, sample_csv: str
    ) -> None:
        """POST /products/import?dry_run=false commits rows to database."""
        files = {"file": ("products.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv")}
        res = client.post("/products/import?dry_run=false", files=files)

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["dry_run"] is False
        assert data["summary"]["create_count"] == 2

        # Verify created product can be fetched via API
        fetch_res = client.get("/products/by-barcode/NAMKEEN-SEV-500G")
        assert fetch_res.status_code == status.HTTP_200_OK
        assert fetch_res.json()["sku"] == "NAMKEEN-SEV-500G"

    def test_export_catalog_csv_endpoint(self, client: TestClient, sample_csv: str) -> None:
        """GET /products/export.csv streams CSV file with attachment header."""
        # Commit products first
        files = {"file": ("products.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv")}
        client.post("/products/import?dry_run=false", files=files)

        res = client.get("/products/export.csv")
        assert res.status_code == status.HTTP_200_OK
        assert "text/csv" in res.headers["content-type"]
        assert 'filename="wareflow_products_catalog.csv"' in res.headers["content-disposition"]
        assert b"NAMKEEN-SEV-500G" in res.content

    def test_download_template_csv_endpoint(self, client: TestClient) -> None:
        """GET /products/template.csv streams sample CSV template."""
        res = client.get("/products/template.csv")
        assert res.status_code == status.HTTP_200_OK
        assert "text/csv" in res.headers["content-type"]
        assert 'filename="wareflow_product_import_template.csv"' in res.headers["content-disposition"]
        assert b"sku,name,wholesale_price" in res.content
