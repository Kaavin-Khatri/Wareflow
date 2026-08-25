"""Bulk CSV Product Catalog Import & Export Service."""

import csv
from decimal import Decimal, InvalidOperation
import io
import re
from typing import Any

from fastapi import HTTPException, status

from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.schemas.imports import (
    ProductImportResponse,
    ProductImportRowPreview,
    ProductImportSummary,
)
from app.services.audit_service import AuditService
from app.services.barcode_service import generate_internal_ean13


def normalize_header(header: str) -> str:
    """Normalize raw CSV column header string to canonical field name."""
    clean = re.sub(r"[^a-zA-Z0-9]", "", header).lower()

    if clean in ("sku", "productsku", "itemsku", "itemcode", "code"):
        return "sku"
    if clean in ("name", "productname", "itemname", "title", "producttitle"):
        return "name"
    if clean in (
        "wholesaleprice",
        "price",
        "wholesalepriceinr",
        "rate",
        "sellingprice",
        "saleprice",
    ):
        return "wholesale_price"
    if clean in ("costprice", "cost", "purchaseprice", "buyingprice", "costpriceinr"):
        return "cost_price"
    if clean in ("category", "categoryname", "productcategory", "cat"):
        return "category_name"
    if clean in ("unit", "uom", "baseuom", "unitofmeasure", "packunit"):
        return "unit"
    if clean in ("hsn", "hsncode", "hsnnumber", "gstcode", "sac"):
        return "hsn_code"
    if clean in ("barcode", "ean", "ean13", "upc", "barcodeno"):
        return "barcode"
    if clean in ("reorderpoint", "minstock", "threshold", "reorderthreshold", "minquantity"):
        return "reorder_point"
    if clean in ("reorderqty", "reorderquantity", "batchqty", "defaultbatchqty", "batchquantity"):
        return "reorder_qty"
    if clean in ("description", "desc", "details", "productdetails", "notes"):
        return "description"

    return clean


class ProductImportService:
    """Service handling catalog CSV parsing, dry-run previews, upsert commits, and exports."""

    def __init__(
        self,
        repository: ProductRepositoryInterface,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repo = repository
        self._audit = audit_service

    def _parse_csv_rows(self, csv_content: str | bytes) -> list[tuple[int, dict[str, str]]]:
        """Decode and parse CSV into normalized field dictionaries with line numbers."""
        if isinstance(csv_content, bytes):
            # Try utf-8-sig (handles Excel BOM), fallback to utf-8, then latin1
            try:
                decoded = csv_content.decode("utf-8-sig")
            except UnicodeDecodeError:
                try:
                    decoded = csv_content.decode("utf-8")
                except UnicodeDecodeError:
                    decoded = csv_content.decode("latin1")
        else:
            decoded = csv_content

        f = io.StringIO(decoded)
        reader = csv.reader(f)

        try:
            raw_headers = next(reader)
        except StopIteration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded CSV file is empty.",
            )

        # Normalize headers
        header_map = [normalize_header(h) for h in raw_headers]

        if "sku" not in header_map or "name" not in header_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV must contain at least 'sku' and 'name' header columns.",
            )

        parsed_rows: list[tuple[int, dict[str, str]]] = []
        for line_idx, row in enumerate(reader, start=2):
            if not row or not any(cell.strip() for cell in row):
                continue  # skip blank lines

            row_dict: dict[str, str] = {}
            for col_idx, col_name in enumerate(header_map):
                if col_idx < len(row):
                    row_dict[col_name] = row[col_idx].strip()
                else:
                    row_dict[col_name] = ""

            parsed_rows.append((line_idx, row_dict))

        return parsed_rows

    def preview_import(self, csv_content: str | bytes) -> ProductImportResponse:
        """Perform dry-run parsing and validation against current database state."""
        parsed = self._parse_csv_rows(csv_content)
        if not parsed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV contains no data rows to import.",
            )

        # Build existing catalog SKU map (case-insensitive)
        existing_products = self._repo.list_products(limit=10000)
        existing_skus: dict[str, Any] = {}
        for p in existing_products:
            sku_val = getattr(p, "sku", None) or (p.get("sku") if isinstance(p, dict) else None)
            if sku_val:
                existing_skus[str(sku_val).strip().lower()] = p

        seen_skus_in_batch: set[str] = set()
        preview_rows: list[ProductImportRowPreview] = []

        create_count = 0
        update_count = 0
        reject_count = 0

        for line_num, row in parsed:
            errors: list[str] = []
            sku_raw = row.get("sku", "").strip()
            name_raw = row.get("name", "").strip()

            if not sku_raw:
                errors.append("SKU code is required.")
            if not name_raw:
                errors.append("Product name is required.")

            # Validate Wholesale Price
            wholesale_str = row.get("wholesale_price", "").strip()
            wholesale_price: float | None = None
            if not wholesale_str:
                errors.append("Wholesale price is required.")
            else:
                try:
                    wp_dec = Decimal(wholesale_str)
                    if wp_dec < 0:
                        errors.append("Wholesale price cannot be negative.")
                    else:
                        wholesale_price = float(wp_dec)
                except (InvalidOperation, ValueError):
                    errors.append(f"Invalid wholesale price format: '{wholesale_str}'.")

            # Validate Cost Price (Optional, defaults to 0.0)
            cost_str = row.get("cost_price", "").strip()
            cost_price: float | None = 0.0
            if cost_str:
                try:
                    cp_dec = Decimal(cost_str)
                    if cp_dec < 0:
                        errors.append("Cost price cannot be negative.")
                    else:
                        cost_price = float(cp_dec)
                except (InvalidOperation, ValueError):
                    errors.append(f"Invalid cost price format: '{cost_str}'.")

            # Validate Reorder Thresholds
            rp_str = row.get("reorder_point", "").strip()
            if rp_str:
                try:
                    rp_int = int(rp_str)
                    if rp_int < 0:
                        errors.append("Reorder point must be 0 or greater.")
                except ValueError:
                    errors.append(f"Invalid reorder point: '{rp_str}'.")

            rq_str = row.get("reorder_qty", "").strip()
            if rq_str:
                try:
                    rq_int = int(rq_str)
                    if rq_int < 1:
                        errors.append("Reorder batch quantity must be at least 1.")
                except ValueError:
                    errors.append(f"Invalid reorder quantity: '{rq_str}'.")

            sku_key = sku_raw.lower() if sku_raw else ""

            # Determine Action
            if errors:
                action = "reject"
                reject_count += 1
            elif sku_key in existing_skus or sku_key in seen_skus_in_batch:
                action = "update"
                update_count += 1
            else:
                action = "create"
                create_count += 1

            if sku_key:
                seen_skus_in_batch.add(sku_key)

            preview_rows.append(
                ProductImportRowPreview(
                    row_number=line_num,
                    action=action,
                    sku=sku_raw,
                    name=name_raw,
                    wholesale_price=wholesale_price,
                    cost_price=cost_price,
                    category_name=row.get("category_name") or None,
                    unit=row.get("unit") or "Piece",
                    hsn_code=row.get("hsn_code") or None,
                    barcode=row.get("barcode") or "(auto EAN-13)" if action == "create" else row.get("barcode") or None,
                    errors=errors,
                )
            )

        summary = ProductImportSummary(
            total_rows=len(preview_rows),
            valid_count=create_count + update_count,
            create_count=create_count,
            update_count=update_count,
            reject_count=reject_count,
        )

        return ProductImportResponse(
            dry_run=True,
            summary=summary,
            rows=preview_rows,
        )

    def execute_import(
        self, csv_content: str | bytes, actor_id: str | None = None
    ) -> ProductImportResponse:
        """Validate and commit valid CSV rows to database with upsert logic."""
        preview = self.preview_import(csv_content)
        parsed = self._parse_csv_rows(csv_content)

        # Build existing categories map: {lower_name: id}
        existing_categories = self._repo.list_categories()
        category_map: dict[str, str] = {}
        for cat in existing_categories:
            cat_name = getattr(cat, "name", None) or (cat.get("name") if isinstance(cat, dict) else None)
            cat_id = getattr(cat, "id", None) or (cat.get("id") if isinstance(cat, dict) else None)
            if cat_name and cat_id:
                category_map[str(cat_name).strip().lower()] = str(cat_id)

        committed_rows: list[ProductImportRowPreview] = []
        actual_create_count = 0
        actual_update_count = 0
        actual_reject_count = 0

        for line_num, row_data in parsed:
            # Find matching preview item
            matching_preview = next(
                (p for p in preview.rows if p.row_number == line_num), None
            )
            if not matching_preview or matching_preview.action == "reject":
                actual_reject_count += 1
                if matching_preview:
                    committed_rows.append(matching_preview)
                continue

            sku_clean = row_data.get("sku", "").strip()
            name_clean = row_data.get("name", "").strip()
            wp = Decimal(row_data.get("wholesale_price", "0"))
            cp = Decimal(row_data.get("cost_price", "0")) if row_data.get("cost_price", "").strip() else Decimal("0.00")
            cat_name = row_data.get("category_name", "").strip()
            unit_val = row_data.get("unit", "").strip() or "Piece"
            hsn_val = row_data.get("hsn_code", "").strip() or None
            barcode_val = row_data.get("barcode", "").strip() or None
            desc_val = row_data.get("description", "").strip() or None
            rp_val = int(row_data.get("reorder_point", "10")) if row_data.get("reorder_point", "").strip() else 10
            rq_val = int(row_data.get("reorder_qty", "50")) if row_data.get("reorder_qty", "").strip() else 50

            # Resolve or create Category
            category_id: str | None = None
            if cat_name:
                cat_key = cat_name.lower()
                if cat_key in category_map:
                    category_id = category_map[cat_key]
                else:
                    new_cat = self._repo.create_category({"name": cat_name})
                    new_cat_id = getattr(new_cat, "id", None) or (new_cat.get("id") if isinstance(new_cat, dict) else None)
                    category_id = str(new_cat_id)
                    category_map[cat_key] = category_id

            existing = self._repo.get_by_sku(sku_clean)

            if existing:
                # Update existing product
                prod_id = getattr(existing, "id", None) or (existing.get("id") if isinstance(existing, dict) else None)
                update_payload: dict[str, Any] = {
                    "name": name_clean,
                    "wholesale_price": float(wp),
                    "cost_price": float(cp),
                    "reorder_point": rp_val,
                    "reorder_qty": rq_val,
                    "unit": unit_val,
                }
                if category_id:
                    update_payload["category_id"] = category_id
                if hsn_val:
                    update_payload["hsn_code"] = hsn_val
                if barcode_val:
                    update_payload["barcode"] = barcode_val
                if desc_val:
                    update_payload["description"] = desc_val

                self._repo.update_product(str(prod_id), update_payload)
                actual_update_count += 1

                if self._audit:
                    self._audit.log(
                        actor_id=actor_id,
                        action="product_updated",
                        entity_type="product",
                        entity_id=str(prod_id),
                        before=None,
                        after=update_payload,
                    )

                committed_rows.append(
                    ProductImportRowPreview(
                        row_number=line_num,
                        action="update",
                        sku=sku_clean,
                        name=name_clean,
                        wholesale_price=float(wp),
                        cost_price=float(cp),
                        category_name=cat_name or None,
                        unit=unit_val,
                        hsn_code=hsn_val,
                        barcode=barcode_val,
                    )
                )
            else:
                # Create new product with auto EAN-13 if barcode is omitted
                final_barcode = barcode_val or generate_internal_ean13()
                create_payload: dict[str, Any] = {
                    "sku": sku_clean,
                    "name": name_clean,
                    "wholesale_price": float(wp),
                    "cost_price": float(cp),
                    "reorder_point": rp_val,
                    "reorder_qty": rq_val,
                    "unit": unit_val,
                    "barcode": final_barcode,
                    "is_active": True,
                }
                if category_id:
                    create_payload["category_id"] = category_id
                if hsn_val:
                    create_payload["hsn_code"] = hsn_val
                if desc_val:
                    create_payload["description"] = desc_val

                created = self._repo.create_product(create_payload)
                new_id = getattr(created, "id", None) or (created.get("id") if isinstance(created, dict) else None)
                actual_create_count += 1

                if self._audit:
                    self._audit.log(
                        actor_id=actor_id,
                        action="product_created",
                        entity_type="product",
                        entity_id=str(new_id),
                        before=None,
                        after=create_payload,
                    )

                committed_rows.append(
                    ProductImportRowPreview(
                        row_number=line_num,
                        action="create",
                        sku=sku_clean,
                        name=name_clean,
                        wholesale_price=float(wp),
                        cost_price=float(cp),
                        category_name=cat_name or None,
                        unit=unit_val,
                        hsn_code=hsn_val,
                        barcode=final_barcode,
                    )
                )

        final_summary = ProductImportSummary(
            total_rows=len(committed_rows),
            valid_count=actual_create_count + actual_update_count,
            create_count=actual_create_count,
            update_count=actual_update_count,
            reject_count=actual_reject_count,
        )

        return ProductImportResponse(
            dry_run=False,
            summary=final_summary,
            rows=committed_rows,
        )

    def generate_csv_template(self) -> str:
        """Generate standardized CSV sample template with required headers and example rows."""
        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            "sku",
            "name",
            "wholesale_price",
            "cost_price",
            "category",
            "unit",
            "hsn_code",
            "barcode",
            "reorder_point",
            "reorder_qty",
            "description",
        ]
        writer.writerow(headers)

        # Example FMCG wholesale products
        writer.writerow([
            "NAMKEEN-SEV-500G",
            "Ratlam Sev 500g",
            "120.00",
            "85.00",
            "Namkeen & Snacks",
            "Packet",
            "21069099",
            "",
            "20",
            "100",
            "Crispy spiced gram flour noodles with clove and black pepper",
        ])
        writer.writerow([
            "GRAIN-BASMATI-25KG",
            "Royal Basmati Rice 25kg",
            "2450.00",
            "2100.00",
            "Grains & Staples",
            "Bag",
            "10063020",
            "",
            "10",
            "30",
            "Premium aged long-grain basmati rice",
        ])

        return output.getvalue()

    def export_catalog_csv(self) -> str:
        """Export full catalog products into CSV string."""
        products = self._repo.list_products(limit=10000)

        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            "sku",
            "name",
            "category",
            "wholesale_price",
            "cost_price",
            "unit",
            "hsn_code",
            "barcode",
            "reorder_point",
            "reorder_qty",
            "description",
            "is_active",
        ]
        writer.writerow(headers)

        for p in products:
            sku = getattr(p, "sku", None) or (p.get("sku") if isinstance(p, dict) else "")
            name = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else "")

            cat = getattr(p, "category", None) or (p.get("category") if isinstance(p, dict) else None)
            cat_name = ""
            if cat:
                cat_name = getattr(cat, "name", None) or (cat.get("name") if isinstance(cat, dict) else "")

            wp = getattr(p, "wholesale_price", None) or (p.get("wholesale_price") if isinstance(p, dict) else 0)
            cp = getattr(p, "cost_price", None) or (p.get("cost_price") if isinstance(p, dict) else 0)
            unit = getattr(p, "unit", None) or (p.get("unit") if isinstance(p, dict) else "Piece")
            hsn = getattr(p, "hsn_code", None) or (p.get("hsn_code") if isinstance(p, dict) else "")
            barcode = getattr(p, "barcode", None) or (p.get("barcode") if isinstance(p, dict) else "")
            rp = getattr(p, "reorder_point", None) or (p.get("reorder_point") if isinstance(p, dict) else 10)
            rq = getattr(p, "reorder_qty", None) or (p.get("reorder_qty") if isinstance(p, dict) else 50)
            desc = getattr(p, "description", None) or (p.get("description") if isinstance(p, dict) else "")
            is_active = getattr(p, "is_active", True) if hasattr(p, "is_active") else p.get("is_active", True)

            writer.writerow([
                sku,
                name,
                cat_name,
                f"{float(wp):.2f}",
                f"{float(cp):.2f}",
                unit,
                hsn or "",
                barcode or "",
                rp,
                rq,
                desc or "",
                "Active" if is_active else "Inactive",
            ])

        return output.getvalue()
