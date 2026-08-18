"""
Alert rules engine and compliance monitoring service.

Follows Open/Closed Principle (OCP): New operational alert rules implement
the AlertRule protocol without modifying the AlertEngineService runner.
"""

from datetime import date
from typing import Protocol, runtime_checkable

from app.repositories.interfaces.business_settings_repository import (
    BusinessSettingsRepositoryInterface,
)
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.schemas.alerts import (
    AlertItemResponse,
    AlertSeverityEnum,
    AlertTypeEnum,
    ComplianceSummaryResponse,
)


@runtime_checkable
class AlertRule(Protocol):
    """Protocol for concrete alert evaluation rules (OCP)."""

    name: str

    def evaluate(self, reference_date: date | None = None) -> list[AlertItemResponse]:
        """Evaluate the rule against domain data and produce active alerts."""
        ...


class ExpiringLicenseRule:
    """
    Alert rule checking FSSAI food safety licenses for distributor and suppliers.

    Alert Windows:
    - 30-day early warning (Warning severity)
    - 7-day escalation (Critical severity, urgent notifications)
    - Expired (<0 days, Critical severity, compliance breach)
    """

    name = "expiring_license_rule"

    def __init__(
        self,
        business_repo: BusinessSettingsRepositoryInterface,
        supplier_repo: SupplierRepositoryInterface,
    ) -> None:
        self._business_repo = business_repo
        self._supplier_repo = supplier_repo

    def evaluate(self, reference_date: date | None = None) -> list[AlertItemResponse]:
        """Evaluate business settings and supplier FSSAI expiration dates."""
        today = reference_date or date.today()
        alerts: list[AlertItemResponse] = []

        # 1. Evaluate Distributor's Own Business Profile
        business = self._business_repo.get_settings()
        if business and business.fssai_expiry_date:
            days = (business.fssai_expiry_date - today).days
            lic = business.fssai_license_no or "N/A"
            b_name = business.business_name or "Distributor Business"

            if days < 0:
                alerts.append(
                    AlertItemResponse(
                        rule_name=self.name,
                        alert_type=AlertTypeEnum.FSSAI_EXPIRED,
                        severity=AlertSeverityEnum.CRITICAL,
                        title=f"Distributor FSSAI License Expired: {b_name}",
                        message=(
                            f"Your business FSSAI license ({lic}) expired on "
                            f"{business.fssai_expiry_date} ({abs(days)} days ago). "
                            "Immediate renewal is legally required to distribute food products."
                        ),
                        entity_type="business_settings",
                        entity_id=business.id,
                        entity_name=b_name,
                        license_no=lic,
                        expiry_date=business.fssai_expiry_date,
                        days_remaining=days,
                        is_escalated=True,
                        metadata={"is_distributor": True},
                    )
                )
            elif days <= 7:
                alerts.append(
                    AlertItemResponse(
                        rule_name=self.name,
                        alert_type=AlertTypeEnum.FSSAI_EXPIRING_SOON,
                        severity=AlertSeverityEnum.CRITICAL,
                        title=f"URGENT: Distributor FSSAI Expiring in {days} Days",
                        message=(
                            f"Your business FSSAI license ({lic}) expires on "
                            f"{business.fssai_expiry_date} (in {days} days). "
                            "Final 7-day escalation active — please complete renewal immediately."
                        ),
                        entity_type="business_settings",
                        entity_id=business.id,
                        entity_name=b_name,
                        license_no=lic,
                        expiry_date=business.fssai_expiry_date,
                        days_remaining=days,
                        is_escalated=True,
                        metadata={"is_distributor": True},
                    )
                )
            elif days <= 30:
                alerts.append(
                    AlertItemResponse(
                        rule_name=self.name,
                        alert_type=AlertTypeEnum.FSSAI_EXPIRING_SOON,
                        severity=AlertSeverityEnum.WARNING,
                        title=f"Distributor FSSAI Expiring in {days} Days",
                        message=(
                            f"Your business FSSAI license ({lic}) expires on "
                            f"{business.fssai_expiry_date} (in {days} days). "
                            "Please initiate renewal documentation with the food authority."
                        ),
                        entity_type="business_settings",
                        entity_id=business.id,
                        entity_name=b_name,
                        license_no=lic,
                        expiry_date=business.fssai_expiry_date,
                        days_remaining=days,
                        is_escalated=False,
                        metadata={"is_distributor": True},
                    )
                )

        # 2. Evaluate All Active Suppliers
        suppliers = self._supplier_repo.list_suppliers(skip=0, limit=1000)
        for s in suppliers:

            if not s.is_active:
                continue

            if not s.fssai_expiry_date:
                continue

            days = (s.fssai_expiry_date - today).days
            lic = s.fssai_license_no or "N/A"

            if days < 0:
                alerts.append(
                    AlertItemResponse(
                        rule_name=self.name,
                        alert_type=AlertTypeEnum.FSSAI_EXPIRED,
                        severity=AlertSeverityEnum.CRITICAL,
                        title=f"Supplier FSSAI License Expired: {s.name}",
                        message=(
                            f"Supplier '{s.name}' FSSAI license ({lic}) expired on "
                            f"{s.fssai_expiry_date} ({abs(days)} days ago). "
                            "PO placement requires human compliance acknowledgment."
                        ),
                        entity_type="supplier",
                        entity_id=s.id,
                        entity_name=s.name,
                        license_no=lic,
                        expiry_date=s.fssai_expiry_date,
                        days_remaining=days,
                        is_escalated=True,
                        metadata={"supplier_id": s.id},
                    )
                )
            elif days <= 7:
                alerts.append(
                    AlertItemResponse(
                        rule_name=self.name,
                        alert_type=AlertTypeEnum.FSSAI_EXPIRING_SOON,
                        severity=AlertSeverityEnum.CRITICAL,
                        title=f"URGENT: Supplier FSSAI Expiring in {days} Days: {s.name}",
                        message=(
                            f"Supplier '{s.name}' FSSAI license ({lic}) expires on "
                            f"{s.fssai_expiry_date} (in {days} days). "
                            "Follow up with supplier for renewed certificate copy."
                        ),
                        entity_type="supplier",
                        entity_id=s.id,
                        entity_name=s.name,
                        license_no=lic,
                        expiry_date=s.fssai_expiry_date,
                        days_remaining=days,
                        is_escalated=True,
                        metadata={"supplier_id": s.id},
                    )
                )
            elif days <= 30:
                alerts.append(
                    AlertItemResponse(
                        rule_name=self.name,
                        alert_type=AlertTypeEnum.FSSAI_EXPIRING_SOON,
                        severity=AlertSeverityEnum.WARNING,
                        title=f"Supplier FSSAI Expiring Soon: {s.name}",
                        message=(
                            f"Supplier '{s.name}' FSSAI license ({lic}) expires on "
                            f"{s.fssai_expiry_date} (in {days} days)."
                        ),
                        entity_type="supplier",
                        entity_id=s.id,
                        entity_name=s.name,
                        license_no=lic,
                        expiry_date=s.fssai_expiry_date,
                        days_remaining=days,
                        is_escalated=False,
                        metadata={"supplier_id": s.id},
                    )
                )

        return alerts


class AlertEngineService:
    """
    Central alert orchestration engine.

    Collects and runs configured AlertRule strategies without modification (OCP).
    """

    def __init__(
        self,
        rules: list[AlertRule] | None = None,
        business_repo: BusinessSettingsRepositoryInterface | None = None,
        supplier_repo: SupplierRepositoryInterface | None = None,
    ) -> None:
        self._rules: list[AlertRule] = rules or []
        self._business_repo = business_repo
        self._supplier_repo = supplier_repo

    def add_rule(self, rule: AlertRule) -> None:
        """Register a new AlertRule without modifying engine core."""
        self._rules.append(rule)

    def evaluate_all(self, reference_date: date | None = None) -> list[AlertItemResponse]:
        """Execute all registered alert rules and aggregate results."""
        all_alerts: list[AlertItemResponse] = []
        for rule in self._rules:
            results = rule.evaluate(reference_date=reference_date)
            all_alerts.extend(results)

        # Sort: critical first, then warning, then lowest days remaining
        def sort_key(item: AlertItemResponse) -> tuple[int, int]:
            severity_order = {
                AlertSeverityEnum.CRITICAL: 0,
                AlertSeverityEnum.WARNING: 1,
                AlertSeverityEnum.INFO: 2,
            }
            rem = item.days_remaining if item.days_remaining is not None else 9999
            return (severity_order.get(item.severity, 3), rem)

        all_alerts.sort(key=sort_key)
        return all_alerts

    def get_compliance_summary(
        self, reference_date: date | None = None
    ) -> ComplianceSummaryResponse:
        """Compute aggregate compliance health breakdown."""
        today = reference_date or date.today()

        # Business status
        b_status = "missing"
        b_days = None
        if self._business_repo:
            b = self._business_repo.get_settings()
            if b and b.fssai_expiry_date:
                b_days = (b.fssai_expiry_date - today).days
                if b_days < 0:
                    b_status = "expired"
                elif b_days <= 30:
                    b_status = "expiring_soon"
                else:
                    b_status = "valid"

        # Supplier counts
        total_suppliers = 0
        compliant = 0
        expiring_soon = 0
        expired = 0
        missing = 0

        if self._supplier_repo:
            suppliers = self._supplier_repo.list_suppliers(skip=0, limit=1000)
            for s in suppliers:

                if not s.is_active:
                    continue
                total_suppliers += 1
                if not s.fssai_expiry_date:
                    missing += 1
                else:
                    d = (s.fssai_expiry_date - today).days
                    if d < 0:
                        expired += 1
                    elif d <= 30:
                        expiring_soon += 1
                    else:
                        compliant += 1

        active_alerts = self.evaluate_all(reference_date=reference_date)

        return ComplianceSummaryResponse(
            business_fssai_status=b_status,
            business_days_remaining=b_days,
            total_suppliers=total_suppliers,
            suppliers_compliant=compliant,
            suppliers_expiring_soon=expiring_soon,
            suppliers_expired=expired,
            suppliers_missing_license=missing,
            active_alerts_count=len(active_alerts),
            alerts=active_alerts,
        )
