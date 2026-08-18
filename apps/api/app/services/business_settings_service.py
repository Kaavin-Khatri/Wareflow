"""Business settings domain service."""

import contextlib
import re
from datetime import date

from fastapi import HTTPException, status

from app.models.audit_and_settings import BusinessSettings
from app.repositories.interfaces.business_settings_repository import (
    BusinessSettingsRepositoryInterface,
)
from app.schemas.business_settings import (
    BusinessSettingsResponse,
    BusinessSettingsUpdateRequest,
)
from app.services.audit_service import AuditService

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


class BusinessSettingsService:
    """Service managing distributor profile, GSTIN/FSSAI compliance, and PDF headers."""

    def __init__(
        self,
        repository: BusinessSettingsRepositoryInterface,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repo = repository
        self._audit = audit_service

    @staticmethod
    def validate_gstin(gstin: str | None) -> None:
        """Validate Indian 15-character GSTIN format if provided."""
        if not gstin:
            return
        cleaned = gstin.strip().upper()
        if not GSTIN_REGEX.match(cleaned):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid GSTIN format. Expected standard 15-character Indian GSTIN (e.g. 27ABCDE1234F1Z5).",
            )

    @staticmethod
    def validate_contact_info(phone: str | None, email: str | None) -> None:
        """Validate phone and email syntax if provided."""
        if email and email.strip() and not EMAIL_REGEX.match(email.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid email address format: '{email}'.",
            )
        if phone and phone.strip():
            digits = re.sub(r"\D", "", phone)
            if len(digits) < 7 or len(digits) > 15:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid phone number '{phone}'. Expected between 7 and 15 digits.",
                )

    def _to_response(self, settings: BusinessSettings | None) -> BusinessSettingsResponse:
        """Enrich model with computed FSSAI compliance metadata."""
        if not settings:
            return BusinessSettingsResponse(
                id="default",
                business_name="WareFlow Wholesale Distributors",
                fssai_status="missing",
                days_until_fssai_expiry=None,
            )

        fssai_status = "missing"
        days_remaining = None

        if settings.fssai_license_no and settings.fssai_expiry_date:
            today = date.today()
            days_remaining = (settings.fssai_expiry_date - today).days
            if days_remaining < 0:
                fssai_status = "expired"
            elif days_remaining <= 30:
                fssai_status = "expiring_soon"
            else:
                fssai_status = "valid"

        return BusinessSettingsResponse(
            id=settings.id,
            business_name=settings.business_name,
            gstin=settings.gstin,
            fssai_license_no=settings.fssai_license_no,
            fssai_expiry_date=settings.fssai_expiry_date,
            address=settings.address,
            phone=settings.phone,
            email=settings.email,
            updated_at=settings.updated_at,
            fssai_status=fssai_status,
            days_until_fssai_expiry=days_remaining,
        )

    def get_settings(self) -> BusinessSettingsResponse:
        """Fetch current business profile & regulatory license status."""
        settings = self._repo.get_settings()
        return self._to_response(settings)

    def update_settings(
        self,
        payload: BusinessSettingsUpdateRequest,
        actor_id: str | None = None,
    ) -> BusinessSettingsResponse:
        """Update or initialize distributor profile with validation & audit logging."""
        self.validate_gstin(payload.gstin)
        self.validate_contact_info(payload.phone, payload.email)

        before_settings = self._repo.get_settings()
        before_dict = (
            {
                "business_name": before_settings.business_name,
                "gstin": before_settings.gstin,
                "fssai_license_no": before_settings.fssai_license_no,
                "fssai_expiry_date": str(before_settings.fssai_expiry_date)
                if before_settings.fssai_expiry_date
                else None,
            }
            if before_settings
            else None
        )

        updated = self._repo.update_settings(payload)

        if self._audit and actor_id:
            with contextlib.suppress(Exception):
                self._audit.log_action(
                    actor_id=actor_id,
                    action="business_settings_updated",
                    entity_type="business_settings",
                    entity_id=updated.id,
                    before_value=before_dict,
                    after_value={
                        "business_name": updated.business_name,
                        "gstin": updated.gstin,
                        "fssai_license_no": updated.fssai_license_no,
                        "fssai_expiry_date": str(updated.fssai_expiry_date)
                        if updated.fssai_expiry_date
                        else None,
                    },
                )

        return self._to_response(updated)
