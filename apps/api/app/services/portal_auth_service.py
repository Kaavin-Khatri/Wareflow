"""Retailer Portal authentication, self-service scoping, and tenant isolation service."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.core.security import CurrentUser

from app.models.portal import RetailerUser
from app.models.retailer import BuyerTypeEnum, SalesOrder
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.retailer_user_repository import RetailerUserRepository
from app.repositories.interfaces.sales_order_repository import (
    SalesOrderRepositoryInterface,
)
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.schemas.portal import (
    PortalCatalogProductResponse,
    PortalCategoryResponse,
    PortalCreateOrderRequest,
    PortalInvoiceListItemResponse,
    PortalOrderItemRequest,
    PortalOrderListItemResponse,
    PortalOrderPlacementResponse,
    RetailerPortalMeResponse,
)
from app.schemas.sales_orders import (
    SalesOrderCreateRequest,
    SalesOrderItemCreateRequest,
)
from app.services.pricing_strategy import PricingEngineService


class PortalAuthService:
    """Service enforcing retailer authentication, invite acceptance, and server-side data wall."""

    def __init__(
        self,
        retailer_user_repo: RetailerUserRepository,
        retailer_repo: RetailerRepository,
        profile_repo: ProfileRepository,
        sales_order_repo: SalesOrderRepositoryInterface | None = None,
        invoice_repo: InvoiceRepositoryInterface | None = None,
        product_repo: ProductRepositoryInterface | None = None,
        stock_repo: StockRepositoryInterface | None = None,
        pricing_engine: PricingEngineService | None = None,
    ) -> None:
        self._user_repo = retailer_user_repo
        self._retailer_repo = retailer_repo
        self._profile_repo = profile_repo
        self._order_repo = sales_order_repo
        self._invoice_repo = invoice_repo
        self._product_repo = product_repo
        self._stock_repo = stock_repo
        self._pricing_engine = pricing_engine or PricingEngineService()

    def bootstrap_retailer_user(
        self,
        uid: str,
        email: str,
        invite_token: str | None = None,
        display_name: str | None = None,
        phone: str | None = None,
    ) -> RetailerPortalMeResponse:
        """
        Onboard or authenticate a retailer portal user.

        Guarantees:
        1. Staff members (in profiles) cannot access retailer portal.
        2. Existing retailer users return their scoped retailer profile.
        3. Pending invites by token or email bind the Firebase UID to the retailer record.
        """
        # Cross-boundary check: Reject staff accounts
        staff_profile = self._profile_repo.get_by_id(uid)
        if staff_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff accounts cannot log into the Retailer Portal. Please use the Admin Dashboard.",
            )

        # Check if already registered
        existing_user = self._user_repo.get_user_by_id(uid)
        if existing_user:
            retailer = self._retailer_repo.get_by_id(existing_user.retailer_id)
            if not retailer or not retailer.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Retailer account is deactivated or not found. Contact your distributor.",
                )
            return self._build_me_response(existing_user, retailer)

        # Attempt to find pending invite
        invite = None
        if invite_token:
            invite = self._user_repo.get_invite_by_token(invite_token)
        if not invite and email:
            invite = self._user_repo.get_pending_invite_by_email(email)

        if not invite:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No portal invitation found for this email. Please request an invite from your distributor.",
            )

        now = datetime.now(UTC)
        if invite.expires_at.tzinfo is not None and invite.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Portal invitation link has expired. Request a new invite link.",
            )

        retailer = self._retailer_repo.get_by_id(invite.retailer_id)
        if not retailer or not retailer.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer account is deactivated. Contact your distributor.",
            )

        new_user = RetailerUser(
            id=uid,
            retailer_id=retailer.id,
            email=email.strip().lower(),
            display_name=display_name or retailer.contact_person,
            phone=phone or retailer.phone,
            is_active=True,
        )
        saved_user = self._user_repo.create_user(new_user)
        self._user_repo.mark_invite_accepted(invite.token)

        return self._build_me_response(saved_user, retailer)

    def get_portal_me(self, current_user: CurrentUser) -> RetailerPortalMeResponse:
        """Fetch current authenticated retailer's identity and credit state."""
        if current_user.account_type != "retailer" or not current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer portal access only. Staff accounts cannot access customer portal.",
            )

        retailer = self._retailer_repo.get_by_id(current_user.retailer_id)
        if not retailer or not retailer.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer account is inactive. Contact distributor.",
            )

        user = self._user_repo.get_user_by_id(current_user.id)
        return self._build_me_response(user, retailer, current_user)

    def list_retailer_orders(
        self, current_user: CurrentUser
    ) -> list[PortalOrderListItemResponse]:
        """Fetch sales orders strictly scoped to caller's retailer_id."""
        if current_user.account_type != "retailer" or not current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer portal access only.",
            )

        if not self._order_repo:
            return []

        res = self._order_repo.list_all(retailer_id=current_user.retailer_id, limit=100)
        orders = res[0] if isinstance(res, tuple) else res
        return [
            PortalOrderListItemResponse(
                id=o.id,
                so_number=o.so_number,
                status=o.status.value if hasattr(o.status, "value") else str(o.status),
                order_date=o.order_date,
                total_amount=float(o.total_amount),
                items_count=len(o.items) if hasattr(o, "items") and o.items else 0,
                created_at=o.created_at,
            )
            for o in orders
        ]

    def place_retailer_order(
        self,
        current_user: CurrentUser,
        payload: PortalCreateOrderRequest,
        sales_order_service: Any,
        notification_service: Any | None = None,
    ) -> PortalOrderPlacementResponse:
        """
        Place a wholesale order from the retailer self-service portal.

        Reuses SalesOrderService.create_order and confirm_order verbatim (Zero Duplicated Logic).
        Enforces server-side retailer scoping to prevent cross-account ordering.
        If credit limit or stock verification fails, retains the order in DRAFT status
        and dispatches a notification for staff review.
        """
        if current_user.account_type != "retailer" or not current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer portal access only.",
            )

        retailer = self._retailer_repo.get_by_id(current_user.retailer_id)
        if not retailer or not retailer.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer account is inactive or not found.",
            )

        # 1. Build SalesOrderCreateRequest with server-side retailer_id
        so_create_req = SalesOrderCreateRequest(
            buyer_type=BuyerTypeEnum.RETAILER,
            retailer_id=current_user.retailer_id,
            customer_id=None,
            items=[
                SalesOrderItemCreateRequest(
                    product_id=it.product_id,
                    qty=it.qty,
                )
                for it in payload.items
            ],
        )

        # 2. Create draft order
        draft_order = sales_order_service.create_order(so_create_req, current_user=current_user)

        # 3. Attempt auto-confirmation via SalesOrderService.confirm_order
        try:
            confirmed_order = sales_order_service.confirm_order(
                draft_order.id, current_user=current_user
            )
            return PortalOrderPlacementResponse(
                id=confirmed_order.id,
                so_number=confirmed_order.so_number,
                status=confirmed_order.status.value
                if hasattr(confirmed_order.status, "value")
                else str(confirmed_order.status),
                total_amount=float(confirmed_order.total_amount),
                auto_confirmed=True,
                message="Order placed and confirmed successfully with reserved inventory.",
                reason=None,
                items_count=len(confirmed_order.items),
                created_at=confirmed_order.created_at,
            )
        except HTTPException as exc:
            reason = str(exc.detail) if exc.detail else "Credit or stock review required"
            if notification_service:
                notification_service.send_notification(
                    user_id=current_user.retailer_id,
                    type="portal_order_pending_review",
                    title=f"Order {draft_order.so_number} Placed (Pending Review)",
                    body=f"Your order {draft_order.so_number} was submitted in draft: {reason}",
                )
            return PortalOrderPlacementResponse(
                id=draft_order.id,
                so_number=draft_order.so_number,
                status=draft_order.status.value
                if hasattr(draft_order.status, "value")
                else str(draft_order.status),
                total_amount=float(draft_order.total_amount),
                auto_confirmed=False,
                message="Order received in draft status and queued for staff review.",
                reason=reason,
                items_count=len(draft_order.items),
                created_at=draft_order.created_at,
            )

    def get_retailer_order(self, order_id: str, current_user: CurrentUser) -> SalesOrder:
        """Fetch a specific sales order, enforcing server-side ownership wall."""
        if current_user.account_type != "retailer" or not current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer portal access only.",
            )

        if not self._order_repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order repository not configured."
            )

        order = self._order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales Order with ID '{order_id}' not found.",
            )

        # Server-side tenant isolation data wall
        if order.retailer_id != current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: cannot access another retailer's data.",
            )

        return order

    def list_retailer_invoices(
        self, current_user: CurrentUser
    ) -> list[PortalInvoiceListItemResponse]:
        """Fetch invoices strictly scoped to caller's retailer_id."""
        if current_user.account_type != "retailer" or not current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer portal access only.",
            )

        if not self._invoice_repo:
            return []

        invoices = self._invoice_repo.list_by_retailer_id(current_user.retailer_id)
        now = datetime.now(UTC)
        return [
            PortalInvoiceListItemResponse(
                id=inv.id,
                invoice_number=getattr(inv, "invoice_no", getattr(inv, "invoice_number", "INV")),
                sales_order_id=inv.sales_order_id or "",
                status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
                issue_date=getattr(inv, "invoice_date", getattr(inv, "issue_date", getattr(inv, "created_at", now))),
                due_date=getattr(inv, "due_date", now),
                total_amount=float(inv.total_amount),
                paid_amount=float(getattr(inv, "paid_amount", 0.0)),
                outstanding_balance=(
                    float(inv.outstanding_balance)
                    if hasattr(inv, "outstanding_balance")
                    else float(inv.total_amount)
                ),
                e_invoice_irn=getattr(inv, "e_invoice_irn", None),
                e_way_bill_no=getattr(inv, "e_way_bill_no", None),
            )
            for inv in invoices
        ]

    def _build_me_response(
        self,
        user: RetailerUser | None,
        retailer: Any,
        current_user: CurrentUser | None = None,
    ) -> RetailerPortalMeResponse:
        """Helper to construct the portal me identity response."""
        uid = user.id if user else (current_user.id if current_user else "")
        email = user.email if user else (current_user.email if current_user else "")
        return RetailerPortalMeResponse(
            id=uid,
            email=email,
            retailer_id=retailer.id,
            retailer_name=retailer.name,
            contact_person=retailer.contact_person,
            phone=retailer.phone,
            address=retailer.address,
            gstin=retailer.gstin,
            pricing_tier=retailer.pricing_tier or "standard",
            credit_limit=float(retailer.credit_limit),
            credit_balance=float(retailer.credit_balance),
            is_active=retailer.is_active,
            account_type="retailer",
        )

    def _calculate_product_availability(self, product: Any, on_hand: float) -> str:
        """Compute privacy-preserving availability band without revealing exact inventory counts."""
        if on_hand <= 0:
            return "Out"
        reorder_pt = getattr(product, "reorder_point", 0) if hasattr(product, "reorder_point") else product.get("reorder_point", 0)
        reorder_val = float(reorder_pt or 0)
        if reorder_val > 0 and on_hand <= reorder_val:
            return "Low"
        if reorder_val <= 0 and on_hand <= 10.0:
            return "Low"
        return "Available"

    def _build_catalog_item(
        self, product: Any, pricing_tier: str, cat_map: dict[str, str]
    ) -> PortalCatalogProductResponse:
        """Format product model into tier-priced catalog response with privacy-safe stock band."""
        base_price = float(getattr(product, "wholesale_price", 0.0) if hasattr(product, "wholesale_price") else product.get("wholesale_price", 0.0))
        calc = self._pricing_engine.calculate_line_price(pricing_tier, base_price, 1)
        pid = product.id if hasattr(product, "id") else product.get("id", "")
        on_hand = float(self._stock_repo.get_on_hand(pid)) if self._stock_repo else 100.0
        availability = self._calculate_product_availability(product, on_hand)
        cat_id = getattr(product, "category_id", None) if hasattr(product, "category_id") else product.get("category_id")
        cat_name = cat_map.get(cat_id or "", None) if cat_id else None
        if not cat_name and getattr(product, "category", None) and hasattr(product.category, "name"):
            cat_name = product.category.name
        unit_name = getattr(product, "unit", "Piece") if hasattr(product, "unit") else product.get("unit", "Piece")
        if getattr(product, "base_uom", None) and hasattr(product.base_uom, "name"):
            unit_name = product.base_uom.name

        return PortalCatalogProductResponse(
            id=pid,
            sku=getattr(product, "sku", "") if hasattr(product, "sku") else product.get("sku", ""),
            name=getattr(product, "name", "") if hasattr(product, "name") else product.get("name", ""),
            description=getattr(product, "description", None) if hasattr(product, "description") else product.get("description"),
            content_details=getattr(product, "content_details", None) if hasattr(product, "content_details") else product.get("content_details"),
            image_url=getattr(product, "image_url", None) if hasattr(product, "image_url") else product.get("image_url"),
            category_id=cat_id,
            category_name=cat_name,
            unit=unit_name or "Piece",
            base_price=base_price,
            effective_price=calc.effective_unit_price,
            discount_percentage=calc.discount_percentage,
            pricing_tier=pricing_tier,
            availability=availability,
            hsn_code=getattr(product, "hsn_code", None) if hasattr(product, "hsn_code") else product.get("hsn_code"),
        )

    def get_retailer_catalog(
        self,
        current_user: CurrentUser,
        category_id: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PortalCatalogProductResponse]:
        """Fetch wholesale product catalog customized to caller retailer's pricing tier."""
        if current_user.account_type != "retailer" or not current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer portal access only.",
            )

        retailer = self._retailer_repo.get_by_id(current_user.retailer_id)
        if not retailer or not retailer.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer account is inactive or not found.",
            )

        if not self._product_repo:
            return []

        pricing_tier = getattr(retailer, "pricing_tier", "standard") or "standard"
        products = self._product_repo.list_products(
            skip=skip,
            limit=limit,
            category_id=category_id,
            search=search,
            is_active=True,
        )

        categories = self._product_repo.list_categories() if hasattr(self._product_repo, "list_categories") else []
        cat_map: dict[str, str] = {}
        for c in categories:
            cid = c.id if hasattr(c, "id") else c.get("id", "")
            cname = c.name if hasattr(c, "name") else c.get("name", "")
            if cid:
                cat_map[cid] = cname

        return [self._build_catalog_item(p, pricing_tier, cat_map) for p in products]

    def get_catalog_categories(self, current_user: CurrentUser) -> list[PortalCategoryResponse]:
        """Fetch product categories available in wholesale catalog."""
        if current_user.account_type != "retailer" or not current_user.retailer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Retailer portal access only.",
            )

        if not self._product_repo or not hasattr(self._product_repo, "list_categories"):
            return []

        categories = self._product_repo.list_categories()
        results: list[PortalCategoryResponse] = []
        for c in categories:
            cid = c.id if hasattr(c, "id") else c.get("id", "")
            cname = c.name if hasattr(c, "name") else c.get("name", "")
            if cid:
                results.append(PortalCategoryResponse(id=cid, name=cname))
        return results
