"""Business settings repository interface Protocol."""

from typing import Protocol, runtime_checkable

from app.models.audit_and_settings import BusinessSettings
from app.schemas.business_settings import BusinessSettingsUpdateRequest


@runtime_checkable
class BusinessSettingsRepositoryInterface(Protocol):
    """Protocol contract for managing distributor business settings and compliance profile."""

    def get_settings(self) -> BusinessSettings | None:
        """Fetch the single business settings record, if it exists."""
        ...

    def update_settings(self, payload: BusinessSettingsUpdateRequest) -> BusinessSettings:
        """Create or update the distributor business settings profile."""
        ...
