"""
Unified Global Search API Router.

Exposes GET /search endpoint querying across products, orders, invoices, retailers, and suppliers.
Follows SOLID principles — HTTP concerns only, delegates business logic to SearchService.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.di import get_search_service
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Global ERP Search",
    description="Cross-domain search across products (name/SKU), orders (SO/PO numbers), invoices (invoice_no), and parties (retailers/suppliers).",
)
def global_search(
    q: Annotated[str, Query(description="Search keyword or identifier query")] = "",
    limit: Annotated[int, Query(ge=1, le=100, description="Max results to return")] = 30,
    search_service: Annotated[SearchService, Depends(get_search_service)] = None,
) -> SearchResponse:
    """Execute unified multi-domain search with relevance ranking."""
    return search_service.search(query=q, limit=limit)
