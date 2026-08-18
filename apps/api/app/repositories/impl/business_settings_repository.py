"""SQLAlchemy and In-Memory implementations for BusinessSettings repository."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_and_settings import BusinessSettings
from app.repositories.interfaces.business_settings_repository import (
    BusinessSettingsRepositoryInterface,
)
from app.schemas.business_settings import BusinessSettingsUpdateRequest


class SqlAlchemyBusinessSettingsRepository(BusinessSettingsRepositoryInterface):
    """SQLAlchemy implementation of BusinessSettingsRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_settings(self) -> BusinessSettings | None:
        """Fetch the first/singleton business settings row."""
        stmt = select(BusinessSettings).limit(1)
        return self._session.scalars(stmt).first()

    def update_settings(self, payload: BusinessSettingsUpdateRequest) -> BusinessSettings:
        """Upsert the single business settings record."""
        existing = self.get_settings()
        if existing:
            existing.business_name = payload.business_name
            existing.gstin = payload.gstin
            existing.fssai_license_no = payload.fssai_license_no
            existing.fssai_expiry_date = payload.fssai_expiry_date
            existing.address = payload.address
            existing.phone = payload.phone
            existing.email = payload.email
            existing.updated_at = datetime.now(UTC)
            self._session.add(existing)
            self._session.commit()
            self._session.refresh(existing)
            return existing

        new_settings = BusinessSettings(
            id=str(uuid.uuid4()),
            business_name=payload.business_name,
            gstin=payload.gstin,
            fssai_license_no=payload.fssai_license_no,
            fssai_expiry_date=payload.fssai_expiry_date,
            address=payload.address,
            phone=payload.phone,
            email=payload.email,
        )
        self._session.add(new_settings)
        self._session.commit()
        self._session.refresh(new_settings)
        return new_settings


class InMemoryBusinessSettingsRepository(BusinessSettingsRepositoryInterface):
    """In-memory mock implementation for unit testing."""

    def __init__(self, initial_settings: BusinessSettings | None = None) -> None:
        self._settings: BusinessSettings | None = initial_settings

    def get_settings(self) -> BusinessSettings | None:
        return self._settings

    def update_settings(self, payload: BusinessSettingsUpdateRequest) -> BusinessSettings:
        if self._settings:
            self._settings.business_name = payload.business_name
            self._settings.gstin = payload.gstin
            self._settings.fssai_license_no = payload.fssai_license_no
            self._settings.fssai_expiry_date = payload.fssai_expiry_date
            self._settings.address = payload.address
            self._settings.phone = payload.phone
            self._settings.email = payload.email
            self._settings.updated_at = datetime.now(UTC)
            return self._settings

        self._settings = BusinessSettings(
            id=str(uuid.uuid4()),
            business_name=payload.business_name,
            gstin=payload.gstin,
            fssai_license_no=payload.fssai_license_no,
            fssai_expiry_date=payload.fssai_expiry_date,
            address=payload.address,
            phone=payload.phone,
            email=payload.email,
            updated_at=datetime.now(UTC),
        )
        return self._settings
