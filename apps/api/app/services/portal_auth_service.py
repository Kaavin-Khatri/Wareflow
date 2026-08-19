"""Retailer Portal authentication, self-service scoping, and tenant isolation service."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.core.security import CurrentUser

from app.models.portal import RetailerUser
from app.models.retailer import SalesOrder
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.retailer_user_repository import RetailerUserRepository
from app.repositories.interfaces.sales_order_repository import (
    SalesOrderRepositoryInterface,
)
from app.schemas.portal import (
    PortalInvoiceListItemResponse,
    PortalOrderListItemResponse,
    RetailerPortalMeResponse,
)


class PortalAuthService:
    """Service enforcing retailer authentication, invite acceptance, and server-side data wall."""

    def __init__(
        self,
        retailer_user_repo: RetailerUserRepository,
        retailer_repo: RetailerRepository,
        profile_repo: ProfileRepository,
        sales_order_repo: SalesOrderRepositoryInterface | None = None,
        invoice_repo: InvoiceRepositoryInterface | None = None,
    ) -> None:
        self._user_repo = retailer_user_repo
        self._retailer_repo = retailer_repo
        self._profile_repo = profile_repo
        self._order_repo = sales_order_repo
        self._invoice_repo = invoice_repo

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
