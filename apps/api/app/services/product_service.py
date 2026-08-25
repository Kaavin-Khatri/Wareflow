"""
Product domain service.

Contains core business logic for catalog products, categories, price updates,
image storage associations, and deactivation rules.
Strictly adheres to the Dependency Inversion Principle (DIP).
"""

from typing import Any

from fastapi import HTTPException, status

from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.schemas.categories import CategoryCreateRequest, CategoryUpdateRequest
from app.schemas.products import ProductCreateRequest, ProductUpdateRequest
from app.services.audit_service import AuditService
from app.services.barcode_service import BarcodeService, generate_internal_ean13
from app.services.storage_service import StorageServiceInterface


class ProductService:
    """Service handling product business rules and catalog workflows."""

    def __init__(
        self,
        repository: ProductRepositoryInterface,
        audit_service: AuditService | None = None,
        storage_service: StorageServiceInterface | None = None,
    ) -> None:
        self._repo = repository
        self._audit = audit_service
        self._storage = storage_service

    def get_product(self, product_id: str) -> Any:
        """Fetch a product by unique ID."""
        if not product_id or not product_id.strip():
            raise ValueError("Product ID cannot be empty.")
        product = self._repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found.",
            )
        return product

    def get_product_by_sku(self, sku: str) -> Any:
        """Fetch a product by its SKU natural key."""
        if not sku or not sku.strip():
            raise ValueError("SKU cannot be empty.")
        product = self._repo.get_by_sku(sku)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with SKU '{sku}' not found.",
            )
        return product

    def get_product_by_barcode(self, barcode: str) -> Any:
        """Fetch a product by its exact barcode or fallback SKU match."""
        if not barcode or not barcode.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Barcode query cannot be empty.",
            )
        barcode_clean = barcode.strip()
        product = self._repo.get_by_barcode(barcode_clean)
        if not product:
            # Fallback check against SKU in case an alphanumeric SKU was scanned
            product = self._repo.get_by_sku(barcode_clean)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with barcode or SKU '{barcode_clean}' not found.",
            )
        return product

    def get_product_barcode_image(self, product_id: str) -> bytes:
        """Generate high-resolution PNG barcode image for product."""
        product = self.get_product(product_id)
        barcode_val = (
            getattr(product, "barcode", None)
            or (product.get("barcode") if isinstance(product, dict) else None)
        )
        if not barcode_val or not str(barcode_val).strip():
            sku = (
                getattr(product, "sku", None)
                or (product.get("sku") if isinstance(product, dict) else None)
            )
            barcode_val = sku or product_id
        return BarcodeService.render_barcode_png(str(barcode_val).strip())

    def get_product_qr_image(self, product_id: str) -> bytes:
        """Generate high-resolution PNG QR code image for product."""
        product = self.get_product(product_id)
        barcode_val = (
            getattr(product, "barcode", None)
            or (product.get("barcode") if isinstance(product, dict) else None)
        )
        sku = (
            getattr(product, "sku", None)
            or (product.get("sku") if isinstance(product, dict) else None)
        )
        payload_data = barcode_val or sku or product_id
        return BarcodeService.render_qr_code_png(str(payload_data).strip())

    def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Any]:
        """List products with pagination, category filter, search, and active state filters."""
        return self._repo.list_products(
            skip=skip,
            limit=limit,
            category_id=category_id,
            search=search,
            is_active=is_active,
        )

    def create_product(self, payload: ProductCreateRequest, actor_id: str | None = None) -> Any:
        """Create a new catalog product ensuring SKU uniqueness, price sanity, and auto-EAN-13 generation."""
        sku_clean = payload.sku.strip()

        # Business Rule 1: SKU Natural Key Uniqueness
        existing = self._repo.get_by_sku(sku_clean)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{sku_clean}' already exists.",
            )

        # Business Rule 2: Non-negative price validation
        if payload.wholesale_price < 0 or payload.cost_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price values cannot be negative.",
            )

        product_dict = payload.model_dump(exclude_unset=True)
        product_dict["sku"] = sku_clean

        # Auto-generate EAN-13 barcode if omitted
        raw_barcode = payload.barcode.strip() if payload.barcode and payload.barcode.strip() else None
        if not raw_barcode:
            raw_barcode = generate_internal_ean13()
        product_dict["barcode"] = raw_barcode

        created = self._repo.create_product(product_dict)

        prod_id = created.id if hasattr(created, "id") else created["id"]
        prod_name = created.name if hasattr(created, "name") else created["name"]

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="product_created",
                entity_type="product",
                entity_id=prod_id,
                before=None,
                after={
                    "sku": sku_clean,
                    "name": prod_name,
                    "barcode": raw_barcode,
                    "wholesale_price": float(payload.wholesale_price),
                    "cost_price": float(payload.cost_price),
                },
            )

        return created

    def update_product(
        self, product_id: str, payload: ProductUpdateRequest, actor_id: str | None = None
    ) -> Any:
        """Update an existing product with uniqueness checks, price sanity, and open order checks."""
        product = self.get_product(product_id)
        update_dict = payload.model_dump(exclude_unset=True)

        if not update_dict:
            return product

        # Check SKU uniqueness if changing SKU
        if "sku" in update_dict and update_dict["sku"]:
            new_sku = update_dict["sku"].strip()
            existing_sku = self._repo.get_by_sku(new_sku)
            existing_id = (
                existing_sku.id
                if hasattr(existing_sku, "id")
                else existing_sku.get("id")
                if existing_sku
                else None
            )
            if existing_sku and existing_id != product_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with SKU '{new_sku}' already exists.",
                )
            update_dict["sku"] = new_sku

        # Validate non-negative prices
        if (
            "wholesale_price" in update_dict
            and update_dict["wholesale_price"] is not None
            and update_dict["wholesale_price"] < 0
        ) or (
            "cost_price" in update_dict
            and update_dict["cost_price"] is not None
            and update_dict["cost_price"] < 0
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price values cannot be negative.",
            )

        # Business Rule 3: Deactivation Guard
        if (
            "is_active" in update_dict
            and update_dict["is_active"] is False
            and self._repo.has_open_orders(product_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate product with open Purchase Orders or Sales Orders.",
            )

        updated = self._repo.update_product(product_id, update_dict)

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="product_updated",
                entity_type="product",
                entity_id=product_id,
                before={
                    "name": getattr(
                        product, "name", product.get("name") if isinstance(product, dict) else ""
                    )
                },
                after=update_dict,
            )

        return updated

    def update_price(
        self,
        product_id: str,
        wholesale_price: float,
        cost_price: float | None = None,
        actor_id: str | None = None,
    ) -> Any:
        """Update product wholesale and/or cost prices and log audit trail."""
        if wholesale_price < 0 or (cost_price is not None and cost_price < 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price values cannot be negative.",
            )

        product = self.get_product(product_id)
        old_wholesale = (
            float(product.wholesale_price)
            if hasattr(product, "wholesale_price")
            else float(product.get("wholesale_price", 0))
        )
        old_cost = (
            float(product.cost_price)
            if hasattr(product, "cost_price")
            else float(product.get("cost_price", 0))
        )
        prod_name = product.name if hasattr(product, "name") else product.get("name", product_id)
        prod_sku = product.sku if hasattr(product, "sku") else product.get("sku", "")

        updated = self._repo.update_prices(
            product_id=product_id,
            wholesale_price=wholesale_price,
            cost_price=cost_price,
        )

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="product_price_updated",
                entity_type="product",
                entity_id=product_id,
                before={
                    "name": prod_name,
                    "sku": prod_sku,
                    "wholesale_price": old_wholesale,
                    "cost_price": old_cost,
                },
                after={
                    "name": prod_name,
                    "sku": prod_sku,
                    "wholesale_price": float(wholesale_price),
                    "cost_price": float(cost_price if cost_price is not None else old_cost),
                },
            )

        return updated

    def deactivate_product(self, product_id: str, actor_id: str | None = None) -> Any:
        """Deactivate a product, strictly blocking if open POs or SOs exist."""
        product = self.get_product(product_id)

        # Guard: Check open orders
        if self._repo.has_open_orders(product_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate product with open Purchase Orders or Sales Orders.",
            )

        deactivated = self._repo.deactivate_product(product_id)

        if self._audit:
            prod_name = (
                product.name if hasattr(product, "name") else product.get("name", product_id)
            )
            self._audit.log(
                actor_id=actor_id,
                action="product_deactivated",
                entity_type="product",
                entity_id=product_id,
                before={"name": prod_name, "is_active": True},
                after={"name": prod_name, "is_active": False},
            )

        return deactivated

    def upload_image(
        self,
        product_id: str,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        actor_id: str | None = None,
    ) -> str:
        """Upload product image to object storage and persist the URL."""
        self.get_product(product_id)

        if not self._storage:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage service is not configured.",
            )

        image_url = self._storage.upload_image(
            file_bytes=file_bytes,
            original_filename=filename,
            content_type=content_type,
            bucket="product-images",
        )

        self._repo.set_image_url(product_id, image_url)

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="product_image_updated",
                entity_type="product",
                entity_id=product_id,
                before=None,
                after={"image_url": image_url},
            )

        return image_url

    def delete_product(self, product_id: str, actor_id: str | None = None) -> bool:
        """Delete a product permanently."""
        product = self.get_product(product_id)
        prod_name = product.name if hasattr(product, "name") else product.get("name", product_id)

        deleted = self._repo.delete(product_id)
        if deleted and self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="product_deleted",
                entity_type="product",
                entity_id=product_id,
                before={"name": prod_name},
                after=None,
            )
        return deleted

    # Category domain operations
    def list_categories(self) -> list[Any]:
        """List all product categories."""
        return self._repo.list_categories()

    def get_category(self, category_id: str) -> Any:
        """Fetch a category by ID."""
        cat = self._repo.get_category_by_id(category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID '{category_id}' not found.",
            )
        return cat

    def create_category(self, payload: CategoryCreateRequest, actor_id: str | None = None) -> Any:
        """Create a new product category."""
        data = payload.model_dump(exclude_unset=True)
        created = self._repo.create_category(data)

        if self._audit:
            cat_id = created.id if hasattr(created, "id") else created["id"]
            self._audit.log(
                actor_id=actor_id,
                action="category_created",
                entity_type="category",
                entity_id=cat_id,
                before=None,
                after=data,
            )
        return created

    def update_category(
        self, category_id: str, payload: CategoryUpdateRequest, actor_id: str | None = None
    ) -> Any:
        """Update a product category."""
        self.get_category(category_id)
        data = payload.model_dump(exclude_unset=True)
        updated = self._repo.update_category(category_id, data)

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="category_updated",
                entity_type="category",
                entity_id=category_id,
                before=None,
                after=data,
            )
        return updated

    def delete_category(self, category_id: str, actor_id: str | None = None) -> bool:
        """Delete a product category."""
        self.get_category(category_id)
        deleted = self._repo.delete_category(category_id)

        if deleted and self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="category_deleted",
                entity_type="category",
                entity_id=category_id,
                before=None,
                after=None,
            )
        return deleted
