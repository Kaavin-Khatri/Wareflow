"""Alert and compliance notification schemas."""

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AlertSeverityEnum(StrEnum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertTypeEnum(StrEnum):
    """Types of system and compliance alerts."""

    FSSAI_EXPIRING_SOON = "fssai_expiring_soon"
    FSSAI_EXPIRED = "fssai_expired"
    REORDER_ALERT = "reorder_alert"
    BATCH_EXPIRY = "batch_expiry"
    OVERDUE_INVOICE = "overdue_invoice"


class AlertItemResponse(BaseModel):
    """Single compliance or operational alert item."""

    rule_name: str
    alert_type: str
    severity: AlertSeverityEnum
    title: str
    message: str
    entity_type: str  # "business_settings" | "supplier" | "product" | "batch"
    entity_id: str
    entity_name: str
    license_no: str | None = None
    expiry_date: date | None = None
    days_remaining: int | None = None
    is_escalated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class ComplianceSummaryResponse(BaseModel):
    """Overview summary of compliance health."""

    business_fssai_status: str
    business_days_remaining: int | None
    total_suppliers: int
    suppliers_compliant: int
    suppliers_expiring_soon: int
    suppliers_expired: int
    suppliers_missing_license: int
    active_alerts_count: int
    alerts: list[AlertItemResponse] = Field(default_factory=list)


class SmartAlertItemResponse(BaseModel):
    """Fired smart alert item from rule engine."""

    rule_name: str
    entity_type: str
    entity_id: str
    alert_type: str
    title: str
    body: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    target_permissions: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

