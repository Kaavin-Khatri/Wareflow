"""Reorder suggestions domain service (Step 14.2).

Calculates actionable purchase replenishment recommendations based on on-hand inventory,
configured reorder points, supplier lead times, and AI demand forecasting.
"""

import contextlib
import logging
import math
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.purchase_order_repository import PurchaseOrderRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.schemas.analytics import (
    CreatePOFromSuggestionsRequest,
    ReorderSuggestionItem,
    ReorderSuggestionsResponse,
)
from app.schemas.purchase_orders import POCreateRequest, POItemCreateRequest, PurchaseOrderResponse
from app.services.forecasting_service import ForecastingService
from app.services.purchase_order_service import PurchaseOrderService

logger = logging.getLogger(__name__)


class ReorderSuggestionService:
    """Domain service calculating automated reorder recommendations and draft PO synthesis."""

    def __init__(
        self,
        product_repo: ProductRepositoryInterface,
        stock_repo: StockRepositoryInterface,
        forecasting_service: ForecastingService,
        supplier_repo: SupplierRepositoryInterface | None = None,
        po_repo: PurchaseOrderRepositoryInterface | None = None,
        po_service: PurchaseOrderService | None = None,
    ) -> None:
        self._product_repo = product_repo
        self._stock_repo = stock_repo
        self._forecasting_service = forecasting_service
        self._supplier_repo = supplier_repo
        self._po_repo = po_repo
        self._po_service = po_service

    def get_reorder_suggestions(
        self,
        supplier_id: str | None = None,
        urgency: str | None = None,
        lead_time_buffer_days: int = 14,
    ) -> ReorderSuggestionsResponse:
        """Compute catalog reorder suggestions where on_hand <= reorder_point."""
        if hasattr(self._product_repo, "list_products"):
            active_products = self._product_repo.list_products(limit=1000, is_active=True)
        else:
            products = self._product_repo.list()
            active_products = [
                p
                for p in products
                if (p.get("is_active", True) if isinstance(p, dict) else getattr(p, "is_active", True))
            ]

        items: list[ReorderSuggestionItem] = []
        critical_count = 0
        high_count = 0

        # Build supplier lookup map
        supplier_map: dict[str, str] = {}
        if self._supplier_repo:
            try:
                if hasattr(self._supplier_repo, "list_suppliers"):
                    all_suppliers = self._supplier_repo.list_suppliers(limit=500)
                else:
                    all_suppliers = self._supplier_repo.list()
                for s in all_suppliers:
                    s_id = s.get("id") if isinstance(s, dict) else getattr(s, "id", None)
                    s_name = s.get("name") if isinstance(s, dict) else getattr(s, "name", None)
                    if s_id and s_name:
                        supplier_map[s_id] = s_name
            except Exception as e:
                logger.warning("Failed to load suppliers for name resolution: %s", e)

        # Build product-to-last-supplier mapping from PO history if available
        product_supplier_map: dict[str, tuple[str, str]] = {}
        if self._po_repo:
            try:
                if hasattr(self._po_repo, "list_purchase_orders"):
                    orders = self._po_repo.list_purchase_orders()
                else:
                    orders = self._po_repo.list()
                for o in orders:
                    s_id = (
                        o.get("supplier_id") if isinstance(o, dict) else getattr(o, "supplier_id", None)
                    )
                    s_name = supplier_map.get(s_id, "Supplier") if s_id else "Supplier"
                    po_items = (
                        o.get("items", []) if isinstance(o, dict) else (getattr(o, "items", []) or [])
                    )
                    for item in po_items:
                        p_id = (
                            item.get("product_id")
                            if isinstance(item, dict)
                            else getattr(item, "product_id", None)
                        )
                        if p_id and s_id:
                            product_supplier_map[p_id] = (s_id, s_name)
            except Exception as e:
                logger.warning("Failed to inspect PO history for supplier mapping: %s", e)

        for prod in active_products:
            p_id = prod.get("id") if isinstance(prod, dict) else getattr(prod, "id", None)
            p_name = prod.get("name") if isinstance(prod, dict) else getattr(prod, "name", "Product")
            sku = prod.get("sku") if isinstance(prod, dict) else getattr(prod, "sku", "SKU")
            cat_name = (
                prod.get("category_name")
                if isinstance(prod, dict)
                else getattr(prod, "category_name", None)
            )
            if not cat_name and hasattr(prod, "category") and prod.category:
                cat_name = getattr(prod.category, "name", None)
            raw_unit = prod.get("unit") if isinstance(prod, dict) else getattr(prod, "unit", None)
            unit = str(raw_unit) if raw_unit else "Piece"

            cost_price = float(
                prod.get("cost_price", 0.0)
                if isinstance(prod, dict)
                else getattr(prod, "cost_price", 0.0) or 0.0
            )
            wholesale_price = float(
                prod.get("wholesale_price", 0.0)
                if isinstance(prod, dict)
                else getattr(prod, "wholesale_price", 0.0) or 0.0
            )
            unit_cost = cost_price if cost_price > 0 else wholesale_price

            reorder_point = int(
                prod.get("reorder_point", 10)
                if isinstance(prod, dict)
                else getattr(prod, "reorder_point", 10) or 10
            )
            reorder_qty = int(
                prod.get("reorder_qty", 50)
                if isinstance(prod, dict)
                else getattr(prod, "reorder_qty", 50) or 50
            )
            if reorder_qty <= 0:
                reorder_qty = 50

            on_hand = float(self._stock_repo.get_on_hand(p_id))

            # Trigger condition: on_hand <= reorder_point
            if on_hand <= reorder_point:
                # 1. Fetch forecasted daily demand
                forecast_res = self._forecasting_service.get_product_forecast(
                    product_id=p_id, horizon_days=30
                )
                daily_demand = max(0.0, float(forecast_res.predicted_daily_demand))

                # 2. Formula: max(reorder_qty, ceil(daily_demand * lead_time_days_buffer))
                buffered_demand = math.ceil(daily_demand * lead_time_buffer_days)
                suggested_qty = max(reorder_qty, buffered_demand)

                # 3. Urgency calculation
                if on_hand <= 0 or (daily_demand > 0 and (on_hand / daily_demand) <= 3.0):
                    item_urgency = "critical"
                    critical_count += 1
                elif on_hand <= (reorder_point / 2.0):
                    item_urgency = "high"
                    high_count += 1
                else:
                    item_urgency = "medium"

                # 4. Days of stock remaining
                days_remaining = (
                    round(on_hand / daily_demand, 1) if daily_demand > 0 else (999.0 if on_hand > 0 else 0.0)
                )

                # 5. Resolve primary supplier
                supp_tuple = product_supplier_map.get(p_id)
                primary_sup_id = supp_tuple[0] if supp_tuple else None
                primary_sup_name = supp_tuple[1] if supp_tuple else None

                if not primary_sup_id and supplier_map:
                    # Fallback to first available supplier
                    first_id, first_name = next(iter(supplier_map.items()))
                    primary_sup_id = first_id
                    primary_sup_name = first_name

                # Filter checks
                if supplier_id and primary_sup_id != supplier_id:
                    continue
                if urgency and item_urgency != urgency.lower():
                    continue

                estimated_cost = round(suggested_qty * unit_cost, 2)

                items.append(
                    ReorderSuggestionItem(
                        product_id=p_id,
                        product_name=p_name,
                        sku=sku,
                        category_name=cat_name,
                        unit=unit,
                        on_hand=on_hand,
                        reorder_point=reorder_point,
                        reorder_qty=reorder_qty,
                        forecasted_daily_demand=round(daily_demand, 2),
                        lead_time_days_buffer=lead_time_buffer_days,
                        suggested_reorder_qty=suggested_qty,
                        unit_cost=unit_cost,
                        estimated_cost=estimated_cost,
                        days_of_stock_remaining=days_remaining,
                        urgency=item_urgency,
                        primary_supplier_id=primary_sup_id,
                        primary_supplier_name=primary_sup_name,
                    )
                )

        # Sort items: critical -> high -> medium, then estimated_cost descending
        urgency_rank = {"critical": 0, "high": 1, "medium": 2}
        items.sort(key=lambda x: (urgency_rank.get(x.urgency, 3), -x.estimated_cost))

        total_cost = round(sum(i.estimated_cost for i in items), 2)

        return ReorderSuggestionsResponse(
            items=items,
            total_suggested_items=len(items),
            total_estimated_cost=total_cost,
            critical_count=critical_count,
            high_count=high_count,
            generated_at=datetime.now(UTC),
        )

    def create_po_from_suggestions(
        self,
        request: CreatePOFromSuggestionsRequest,
        created_by_name: str | None = None,
    ) -> PurchaseOrderResponse:
        """Synthesize and persist a draft Purchase Order from recommended suggestions."""
        if not self._po_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PurchaseOrderService is not wired into ReorderSuggestionService",
            )

        po_items: list[POItemCreateRequest] = []
        for item in request.items:
            po_items.append(
                POItemCreateRequest(
                    product_id=item.product_id,
                    qty_ordered=item.qty_ordered,
                    unit_cost=item.unit_cost,
                    uom_id=item.uom_id,
                )
            )

        parsed_expected_date = None
        if request.expected_date:
            with contextlib.suppress(ValueError):
                parsed_expected_date = datetime.strptime(request.expected_date, "%Y-%m-%d").date()

        po_create = POCreateRequest(
            supplier_id=request.supplier_id,
            expected_date=parsed_expected_date,
            items=po_items,
        )

        return self._po_service.create_draft_po(
            payload=po_create,
            actor_id=created_by_name or "AI Reorder Engine",
        )
