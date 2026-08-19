"""Retailer domain service with audit logging, bulk pricing, and portal invitations."""

import contextlib
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth

from app.core.firebase import get_firebase_app
from app.models.portal import RetailerPortalInvite, RetailerUser
from app.models.retailer import Retailer
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.retailer_user_repository import RetailerUserRepository
from app.schemas.retailers import (
    RetailerCreateRequest,
    RetailerInviteRequest,
    RetailerInviteResponse,
    RetailerUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.pricing_strategy import PricingCalculationResult, PricingEngineService

logger = logging.getLogger(__name__)


class RetailerService:
    """Service handling wholesale retailer accounts, credit lines, and pricing."""

    def __init__(
        self,
        retailer_repo: RetailerRepository,
        audit_service: AuditService | None = None,
        pricing_engine: PricingEngineService | None = None,
        retailer_user_repo: RetailerUserRepository | None = None,
    ) -> None:
        self._repo = retailer_repo
        self._audit = audit_service
        self._pricing = pricing_engine or PricingEngineService()
        self._user_repo = retailer_user_repo


    def get_retailer(self, retailer_id: str) -> Retailer:
        """Fetch retailer with 404 validation."""
        retailer = self._repo.get_by_id(retailer_id)
        if not retailer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer with ID '{retailer_id}' not found.",
            )
        return retailer

    def list_retailers(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Retailer]:
        """List wholesale retailers with optional search and active status filters."""
        return self._repo.list_all(skip=skip, limit=limit, is_active=is_active, search=search)

    def create_retailer(
        self,
        payload: RetailerCreateRequest,
        actor_id: str | None = None,
    ) -> Retailer:
        """Register a new wholesale retailer with unique name validation."""
        existing = self._repo.get_by_name(payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Retailer with name '{payload.name}' already exists.",
            )

        retailer = Retailer(
            id=str(uuid.uuid4()),
            name=payload.name.strip(),
            contact_person=payload.contact_person.strip() if payload.contact_person else None,
            phone=payload.phone.strip() if payload.phone else None,
            email=payload.email.strip().lower() if payload.email else None,
            address=payload.address.strip() if payload.address else None,
            gstin=payload.gstin.strip().upper() if payload.gstin else None,
            pricing_tier=payload.pricing_tier.value,
            credit_limit=float(payload.credit_limit),
            credit_balance=0.00,
            is_active=payload.is_active,
        )

        saved = self._repo.create(retailer)

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="retailer_created",
                entity_type="retailer",
                entity_id=saved.id,
                before=None,
                after={
                    "name": saved.name,
                    "pricing_tier": saved.pricing_tier,
                    "credit_limit": float(saved.credit_limit),
                    "is_active": saved.is_active,
                },
            )

        return saved

    def update_retailer(
        self,
        retailer_id: str,
        payload: RetailerUpdateRequest,
        actor_id: str | None = None,
    ) -> Retailer:
        """Update retailer profile, pricing tier, or active status with change audit."""
        retailer = self.get_retailer(retailer_id)
        before_state = {
            "name": retailer.name,
            "contact_person": retailer.contact_person,
            "phone": retailer.phone,
            "email": retailer.email,
            "address": retailer.address,
            "gstin": retailer.gstin,
            "pricing_tier": retailer.pricing_tier,
            "credit_limit": float(retailer.credit_limit),
            "is_active": retailer.is_active,
        }

        updates: dict[str, Any] = {}
        if payload.name is not None:
            clean_name = payload.name.strip()
            if clean_name.lower() != retailer.name.lower():
                dup = self._repo.get_by_name(clean_name)
                if dup and dup.id != retailer_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Another retailer with name '{clean_name}' already exists.",
                    )
            updates["name"] = clean_name

        if payload.contact_person is not None:
            updates["contact_person"] = payload.contact_person.strip() or None
        if payload.phone is not None:
            updates["phone"] = payload.phone.strip() or None
        if payload.email is not None:
            updates["email"] = payload.email.strip().lower() or None
        if payload.address is not None:
            updates["address"] = payload.address.strip() or None
        if payload.gstin is not None:
            updates["gstin"] = payload.gstin.strip().upper() or None
        if payload.pricing_tier is not None:
            updates["pricing_tier"] = payload.pricing_tier.value
        if payload.credit_limit is not None:
            updates["credit_limit"] = float(payload.credit_limit)
        if payload.is_active is not None:
            updates["is_active"] = payload.is_active

        updated = self._repo.update(retailer_id, updates)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer with ID '{retailer_id}' not found.",
            )

        if self._audit and updates:
            after_state = {
                "name": updated.name,
                "contact_person": updated.contact_person,
                "phone": updated.phone,
                "email": updated.email,
                "address": updated.address,
                "gstin": updated.gstin,
                "pricing_tier": updated.pricing_tier,
                "credit_limit": float(updated.credit_limit),
                "is_active": updated.is_active,
            }
            action = (
                "retailer_credit_limit_updated"
                if "credit_limit" in updates and len(updates) == 1
                else "retailer_updated"
            )
            self._audit.log(
                actor_id=actor_id,
                action=action,
                entity_type="retailer",
                entity_id=updated.id,
                before=before_state,
                after=after_state,
            )

        return updated

    def update_credit_limit(
        self,
        retailer_id: str,
        new_credit_limit: float,
        actor_id: str | None = None,
    ) -> Retailer:
        """Update credit limit and record immutable audit log entry."""
        if new_credit_limit < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit limit cannot be negative.",
            )

        retailer = self.get_retailer(retailer_id)
        old_limit = float(retailer.credit_limit)

        updated = self._repo.update_credit_limit(retailer_id, new_credit_limit)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer with ID '{retailer_id}' not found.",
            )

        if self._audit and old_limit != new_credit_limit:
            self._audit.log(
                actor_id=actor_id,
                action="retailer_credit_limit_updated",
                entity_type="retailer",
                entity_id=retailer_id,
                before={"name": retailer.name, "credit_limit": old_limit},
                after={"name": retailer.name, "credit_limit": new_credit_limit},
            )

        return updated

    def calculate_price(
        self,
        retailer_id: str,
        base_price: float,
        quantity: int = 1,
    ) -> PricingCalculationResult:
        """Calculate line pricing for a specific retailer based on their configured tier."""
        retailer = self.get_retailer(retailer_id)
        return self._pricing.calculate_line_price(
            tier=retailer.pricing_tier,
            base_price=base_price,
            quantity=quantity,
        )

    def invite_portal_access(
        self,
        retailer_id: str,
        payload: RetailerInviteRequest,
        actor_id: str | None = None,
    ) -> RetailerInviteResponse:
        """Issue portal access invitation for retailer and provision auth credentials."""
        retailer = self.get_retailer(retailer_id)
        if not retailer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot invite inactive retailer '{retailer.name}'. Please activate the retailer first.",
            )

        email = (payload.email or retailer.email or "").strip().lower()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Retailer '{retailer.name}' has no email address configured. Please provide an email in the request.",
            )

        token = f"inv_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.now(UTC) + timedelta(days=7)

        invite = RetailerPortalInvite(
            id=str(uuid.uuid4()),
            retailer_id=retailer.id,
            email=email,
            token=token,
            is_accepted=False,
            expires_at=expires_at,
        )
        if self._user_repo:
            self._user_repo.create_invite(invite)

        uid, sign_in_link = self._provision_firebase_user(
            email=email,
            display_name=payload.contact_person or retailer.contact_person or retailer.name,
            phone=payload.phone or retailer.phone,
        )
        portal_link = sign_in_link or f"/portal/login?invite={token}&email={email}"

        if self._user_repo:
            existing_user = self._user_repo.get_user_by_id(uid)
            if not existing_user:
                ret_user = RetailerUser(
                    id=uid,
                    retailer_id=retailer.id,
                    email=email,
                    display_name=payload.contact_person or retailer.contact_person,
                    phone=payload.phone or retailer.phone,
                    is_active=True,
                )
                self._user_repo.create_user(ret_user)

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="retailer_portal_invite_sent",
                entity_type="retailer_invite",
                entity_id=retailer.id,
                before=None,
                after={"retailer_name": retailer.name, "email": email, "token": token},
            )

        return RetailerInviteResponse(
            retailer_id=retailer.id,
            retailer_name=retailer.name,
            email=email,
            sign_in_link=portal_link,
            invite_token=token,
            message=f"Portal invitation generated for retailer '{retailer.name}'.",
            created_at=datetime.now(UTC),
        )

    def _provision_firebase_user(
        self, email: str, display_name: str | None, phone: str | None
    ) -> tuple[str, str | None]:
        """Create Firebase auth user if app is live, otherwise generate mock UID."""
        uid = f"uid_ret_{uuid.uuid4().hex[:12]}"
        sign_in_link = None

        if get_firebase_app():
            try:
                user_record = firebase_auth.create_user(
                    email=email,
                    display_name=display_name,
                    phone_number=phone,
                )
                uid = user_record.uid
                with contextlib.suppress(Exception):
                    sign_in_link = firebase_auth.generate_password_reset_link(email)
            except firebase_auth.EmailAlreadyExistsError:
                user_record = firebase_auth.get_user_by_email(email)
                uid = user_record.uid
            except Exception as exc:
                logger.warning("Firebase Admin create_user for retailer failed: %s", exc)

        return uid, sign_in_link

