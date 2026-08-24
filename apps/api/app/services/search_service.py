"""
Global Admin Search Service.

Follows SOLID Principles:
- Single Responsibility: Orchestrates domain repositories to perform cross-entity matching & ranking.
- Open/Closed: Extensible to new entity types (e.g. returns, deliveries) without altering existing match algorithms.
- Dependency Inversion: Injects repository interfaces, avoiding concrete DB bindings.
"""

from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.purchase_order_repository import PurchaseOrderRepositoryInterface
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.schemas.search import SearchResponse, SearchResultItem


class SearchService:
    """Service for searching across products, orders, invoices, retailers, and suppliers."""

    def __init__(
        self,
        product_repo: ProductRepositoryInterface,
        sales_order_repo: SalesOrderRepositoryInterface,
        purchase_order_repo: PurchaseOrderRepositoryInterface,
        retailer_repo: RetailerRepository,
        supplier_repo: SupplierRepositoryInterface,
        invoice_repo: InvoiceRepositoryInterface,
    ) -> None:
        self.product_repo = product_repo
        self.sales_order_repo = sales_order_repo
        self.purchase_order_repo = purchase_order_repo
        self.retailer_repo = retailer_repo
        self.supplier_repo = supplier_repo
        self.invoice_repo = invoice_repo

    def search(self, query: str, limit: int = 30) -> SearchResponse:
        """
        Execute unified search across all domains and return ranked results.

        Ranking tiers:
        - 100.0: Exact natural key match (SKU, SO number, PO number, Invoice number)
        - 95.0: Exact party/product name match
        - 85.0: Prefix match on natural key
        - 75.0: Prefix match on name
        - 50.0: Substring match anywhere in key, name, or metadata
        """
        clean_q = query.strip()
        if not clean_q:
            return SearchResponse(query="", total=0, results=[])

        q_lower = clean_q.lower()
        items: list[SearchResultItem] = []

        # 1. Search Products
        self._search_products(q_lower, items)

        # 2. Search Sales Orders
        self._search_sales_orders(q_lower, items)

        # 3. Search Purchase Orders
        self._search_purchase_orders(q_lower, items)

        # 4. Search Invoices
        self._search_invoices(q_lower, items)

        # 5. Search Retailers
        self._search_retailers(q_lower, items)

        # 6. Search Suppliers
        self._search_suppliers(q_lower, items)

        # Sort descending by relevance score, then alphabetically by title
        items.sort(key=lambda x: (-x.score, x.title.lower()))

        trimmed = items[:limit]
        return SearchResponse(query=clean_q, total=len(items), results=trimmed)

    def _search_products(self, q: str, items: list[SearchResultItem]) -> None:
        try:
            products = self.product_repo.list_products(limit=500)
        except Exception:
            return

        for p in products:
            sku_lower = (p.sku or "").lower()
            name_lower = (p.name or "").lower()

            score = 0.0
            if sku_lower == q:
                score = 100.0
            elif name_lower == q:
                score = 95.0
            elif sku_lower.startswith(q):
                score = 85.0
            elif name_lower.startswith(q):
                score = 75.0
            elif q in sku_lower or q in name_lower:
                score = 50.0

            if score > 0:
                cat_name = p.category.name if hasattr(p, "category") and p.category else "PRODUCT"
                items.append(
                    SearchResultItem(
                        id=str(p.id),
                        kind="product",
                        title=p.name,
                        subtitle=f"SKU: {p.sku} • ₹{p.wholesale_price:,.2f}",
                        badge=cat_name,
                        url="/admin/products",
                        score=score,
                    )
                )

    def _search_sales_orders(self, q: str, items: list[SearchResultItem]) -> None:
        try:
            so_tuple = self.sales_order_repo.list_all(limit=500)
            sales_orders = so_tuple[0] if isinstance(so_tuple, tuple) else so_tuple
        except Exception:
            return

        for so in sales_orders:
            so_no_lower = (so.so_number or "").lower()
            party_name = ""
            if getattr(so, "retailer", None):
                party_name = getattr(so.retailer, "name", None) or getattr(so.retailer, "store_name", "") or ""
            elif getattr(so, "customer", None) and getattr(so.customer, "name", None):
                party_name = so.customer.name
            party_lower = party_name.lower()

            score = 0.0
            if so_no_lower == q:
                score = 100.0
            elif party_lower == q:
                score = 95.0
            elif so_no_lower.startswith(q):
                score = 85.0
            elif party_lower.startswith(q):
                score = 75.0
            elif q in so_no_lower or q in party_lower:
                score = 50.0

            if score > 0:
                items.append(
                    SearchResultItem(
                        id=str(so.id),
                        kind="sales_order",
                        title=so.so_number,
                        subtitle=f"{party_name or 'Wholesale Buyer'} • ₹{so.total_amount:,.2f}",
                        badge=str(so.status).upper(),
                        url="/admin/sales-orders",
                        score=score,
                    )
                )

    def _search_purchase_orders(self, q: str, items: list[SearchResultItem]) -> None:
        try:
            pos = self.purchase_order_repo.list_purchase_orders()
        except Exception:
            return

        for po in pos:
            po_no_lower = (po.po_number or "").lower()
            sup_name = po.supplier.name if getattr(po, "supplier", None) else ""
            sup_lower = sup_name.lower()

            score = 0.0
            if po_no_lower == q:
                score = 100.0
            elif sup_lower == q:
                score = 95.0
            elif po_no_lower.startswith(q):
                score = 85.0
            elif sup_lower.startswith(q):
                score = 75.0
            elif q in po_no_lower or q in sup_lower:
                score = 50.0

            if score > 0:
                status_str = (
                    po.status.value if hasattr(po.status, "value") else str(po.status)
                ).upper()
                items.append(
                    SearchResultItem(
                        id=str(po.id),
                        kind="purchase_order",
                        title=po.po_number,
                        subtitle=f"{sup_name or 'Vendor'} • ₹{po.total_amount:,.2f}",
                        badge=status_str,
                        url="/admin/purchase-orders",
                        score=score,
                    )
                )

    def _search_invoices(self, q: str, items: list[SearchResultItem]) -> None:
        try:
            inv_res = self.invoice_repo.list_invoices(page=1, page_size=500)
            invoices = inv_res[0] if isinstance(inv_res, tuple) else inv_res
        except Exception:
            return

        for inv in invoices:
            inv_no_lower = (inv.invoice_no or "").lower()
            buyer_name = ""
            if getattr(inv, "buyer_name", None):
                buyer_name = inv.buyer_name
            elif getattr(inv, "sales_order", None):
                so = inv.sales_order
                if getattr(so, "retailer", None):
                    buyer_name = getattr(so.retailer, "name", None) or getattr(so.retailer, "store_name", "") or ""
                elif getattr(so, "customer", None):
                    buyer_name = getattr(so.customer, "name", "") or ""
            buyer_lower = buyer_name.lower()

            score = 0.0
            if inv_no_lower == q:
                score = 100.0
            elif buyer_lower == q:
                score = 95.0
            elif inv_no_lower.startswith(q):
                score = 85.0
            elif buyer_lower.startswith(q):
                score = 75.0
            elif q in inv_no_lower or q in buyer_lower:
                score = 50.0

            if score > 0:
                items.append(
                    SearchResultItem(
                        id=str(inv.id),
                        kind="invoice",
                        title=inv.invoice_no,
                        subtitle=f"{buyer_name or 'Buyer'} • ₹{inv.total_amount:,.2f}",
                        badge=str(inv.status).upper(),
                        url="/admin/invoices",
                        score=score,
                    )
                )

    def _search_retailers(self, q: str, items: list[SearchResultItem]) -> None:
        try:
            retailers = self.retailer_repo.list_all(limit=500)
        except Exception:
            return

        for r in retailers:
            store_name = getattr(r, "name", None) or getattr(r, "store_name", "") or ""
            name_lower = store_name.lower()
            contact_lower = (r.contact_person or "").lower()
            phone_lower = (r.phone or "").lower()

            score = 0.0
            if name_lower == q:
                score = 95.0
            elif contact_lower == q:
                score = 90.0
            elif name_lower.startswith(q):
                score = 75.0
            elif contact_lower.startswith(q) or phone_lower.startswith(q):
                score = 65.0
            elif q in name_lower or q in contact_lower or q in phone_lower:
                score = 50.0

            if score > 0:
                items.append(
                    SearchResultItem(
                        id=str(r.id),
                        kind="retailer",
                        title=store_name,
                        subtitle=f"{r.contact_person or 'Retailer'} • Credit: ₹{r.credit_limit:,.2f}",
                        badge="RETAILER",
                        url="/admin/retailers",
                        score=score,
                    )
                )

    def _search_suppliers(self, q: str, items: list[SearchResultItem]) -> None:
        try:
            suppliers = self.supplier_repo.list_suppliers(limit=500)
        except Exception:
            return

        for s in suppliers:
            contact = getattr(s, "contact_person", None) or getattr(s, "contact_name", "") or ""
            name_lower = (s.name or "").lower()
            contact_lower = contact.lower()
            phone_lower = (s.phone or "").lower()

            score = 0.0
            if name_lower == q:
                score = 95.0
            elif contact_lower == q:
                score = 90.0
            elif name_lower.startswith(q):
                score = 75.0
            elif contact_lower.startswith(q) or phone_lower.startswith(q):
                score = 65.0
            elif q in name_lower or q in contact_lower or q in phone_lower:
                score = 50.0

            if score > 0:
                loc = getattr(s, "address", None) or getattr(s, "city", "") or "Vendor"
                items.append(
                    SearchResultItem(
                        id=str(s.id),
                        kind="supplier",
                        title=s.name,
                        subtitle=f"{contact or 'Supplier'} • {loc}",
                        badge="SUPPLIER",
                        url="/admin/suppliers",
                        score=score,
                    )
                )
