"""Smart Alert Rule Engine and Compliance Monitoring Service (Step 7.4 & Step 13.2)."""

from datetime import UTC, date, datetime
import logging
from typing import Any, Protocol, runtime_checkable

from app.models.audit_and_settings import BusinessSettings
from app.models.supplier import Supplier
from app.repositories.interfaces.alert_log_repository import AlertLogRepositoryInterface
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
from app.services.alert_rules.base import AlertEvaluationContext, AlertResult, BaseAlertRule
from app.services.alert_rules.critical_stock_rule import CriticalStockRule
from app.services.alert_rules.expiring_batch_rule import ExpiringBatchRule
from app.services.alert_rules.low_stock_rule import LowStockRule
from app.services.alert_rules.overdue_invoice_rule import OverdueInvoiceRule
from app.services.alert_rules.restock_alert_rule import RestockAlertRule
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@runtime_checkable
class AlertRule(Protocol):
    """Protocol contract for compliance alert rules (Step 7.4)."""

    @property
    def name(self) -> str:
        """Rule name identifier."""
        ...

    def evaluate(self, reference_date: date | None = None) -> list[AlertItemResponse]:
        """Execute rule evaluation and return compliance alert items."""
        ...


class ExpiringLicenseRule:
    """Evaluates FSSAI license validity across business settings and active suppliers."""

    def __init__(
        self,
        business_repo: BusinessSettingsRepositoryInterface | None = None,
        supplier_repo: SupplierRepositoryInterface | None = None,
    ) -> None:
        self._business_repo = business_repo
        self._supplier_repo = supplier_repo

    @property
    def name(self) -> str:
        return "expiring_license_rule"

    @property
    def rule_name(self) -> str:
        return self.name

    def evaluate(self, reference_date: date | None = None, *args: Any, **kwargs: Any) -> list[AlertItemResponse]:
        today = reference_date or date.today()
        alerts: list[AlertItemResponse] = []

        if self._business_repo:
            business = self._business_repo.get_settings()
            if business and business.fssai_expiry_date:
                days = (business.fssai_expiry_date - today).days
                lic = business.fssai_license_no or "N/A"
                b_name = business.business_name or "WareFlow Distributor"

                if days < 0:
                    alerts.append(
                        AlertItemResponse(
                            rule_name=self.name,
                            alert_type=AlertTypeEnum.FSSAI_EXPIRED,
                            severity=AlertSeverityEnum.CRITICAL,
                            title=f"CRITICAL: Distributor FSSAI License Expired",
                            message=(
                                f"Your distributor FSSAI license ({lic}) expired on "
                                f"{business.fssai_expiry_date} ({abs(days)} days ago). "
                                "Dispatch operations should be halted until renewed."
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
                                f"Your distributor FSSAI license ({lic}) expires on "
                                f"{business.fssai_expiry_date} (in {days} days). "
                                "Immediate license renewal required to prevent operational halt."
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

        if self._supplier_repo:
            suppliers = self._supplier_repo.list_suppliers(skip=0, limit=1000)
            for s in suppliers:
                if not s.is_active or not s.fssai_expiry_date:
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
    Central alert orchestration engine (Step 7.4 & Step 13.2).
    Evaluates operational (stock, batches, invoices, restocks) and regulatory rules with 24-hour deduplication.
    """

    def __init__(
        self,
        alert_log_repo: AlertLogRepositoryInterface | None = None,
        notification_service: NotificationService | None = None,
        product_repo: Any = None,
        stock_repo: Any = None,
        invoice_repo: Any = None,
        profile_repo: Any = None,
        retailer_repo: Any = None,
        stock_subscription_repo: Any = None,
        supplier_repo: SupplierRepositoryInterface | None = None,
        business_repo: BusinessSettingsRepositoryInterface | None = None,
        rules: list[Any] | None = None,
        dedup_window_hours: int = 24,
    ) -> None:
        self.alert_log_repo = alert_log_repo
        self.notification_service = notification_service
        self.product_repo = product_repo
        self.stock_repo = stock_repo
        self.invoice_repo = invoice_repo
        self.profile_repo = profile_repo
        self.retailer_repo = retailer_repo
        self.stock_subscription_repo = stock_subscription_repo
        self._supplier_repo = supplier_repo
        self._business_repo = business_repo
        self.dedup_window_hours = dedup_window_hours

        if rules is not None:
            self._rules = list(rules)
        else:
            self._rules = [
                CriticalStockRule(),
                LowStockRule(),
                RestockAlertRule(),
                ExpiringBatchRule(),
                OverdueInvoiceRule(),
                ExpiringLicenseRule(business_repo=business_repo, supplier_repo=supplier_repo),
            ]

    def add_rule(self, rule: Any) -> None:
        """Register a new AlertRule without modifying engine core."""
        self._rules.append(rule)

    def register_rule(self, rule: Any) -> None:
        """Alias for add_rule (OCP)."""
        self.add_rule(rule)

    def _build_context(self) -> AlertEvaluationContext:
        return AlertEvaluationContext(
            product_repo=self.product_repo,
            stock_repo=self.stock_repo,
            invoice_repo=self.invoice_repo,
            retailer_repo=self.retailer_repo,
            supplier_repo=self._supplier_repo,
            stock_subscription_repo=self.stock_subscription_repo,
            notification_service=self.notification_service,
        )

    def evaluate_all(self, reference_date: date | None = None) -> list[Any]:
        """
        Execute all registered alert rules and aggregate results.
        Enforces 24-hour deduplication and dispatches notifications for AlertResult objects.
        """
        context = self._build_context()
        all_alerts: list[Any] = []

        for rule in self._rules:
            try:
                if isinstance(rule, BaseAlertRule):
                    candidates = rule.evaluate(context)
                    for res in candidates:
                        if self._process_alert_result(res):
                            all_alerts.append(res)
                elif hasattr(rule, "evaluate"):
                    # Step 7.4 rule (ExpiringLicenseRule)
                    results = rule.evaluate(reference_date=reference_date)
                    all_alerts.extend(results)
            except Exception as exc:
                logger.error("Error evaluating alert rule %s: %s", getattr(rule, "rule_name", rule), exc)

        return all_alerts

    def evaluate_product_stock_inline(self, product_id: str) -> list[AlertResult]:
        """Fast inline trigger: Evaluates stock rules immediately after inventory deduction or addition."""
        context = self._build_context()
        fired_alerts: list[AlertResult] = []

        stock_rules = [r for r in self._rules if isinstance(r, (CriticalStockRule, LowStockRule, RestockAlertRule))]
        for rule in stock_rules:
            try:
                candidates = rule.evaluate_entity(product_id, context)
                for res in candidates:
                    if self._process_alert_result(res):
                        fired_alerts.append(res)
            except Exception as exc:
                logger.error("Error evaluating inline stock rule for product %s: %s", product_id, exc)

        return fired_alerts

    def evaluate_restock_inline(self, product_id: str) -> list[AlertResult]:
        """Fast inline trigger: Evaluates restock subscriber rules immediately after goods receipt/inbound movement."""
        context = self._build_context()
        fired_alerts: list[AlertResult] = []

        restock_rules = [r for r in self._rules if isinstance(r, RestockAlertRule)]
        for rule in restock_rules:
            try:
                candidates = rule.evaluate_entity(product_id, context)
                for res in candidates:
                    if self._process_alert_result(res):
                        fired_alerts.append(res)
            except Exception as exc:
                logger.error("Error evaluating inline restock rule for product %s: %s", product_id, exc)

        return fired_alerts

    def evaluate_invoices_inline(self) -> list[AlertResult]:
        """Fast inline trigger: Evaluates overdue invoice rules after invoice status updates."""
        context = self._build_context()
        fired_alerts: list[AlertResult] = []

        invoice_rules = [r for r in self._rules if isinstance(r, OverdueInvoiceRule)]
        for rule in invoice_rules:
            try:
                candidates = rule.evaluate(context)
                for res in candidates:
                    if self._process_alert_result(res):
                        fired_alerts.append(res)
            except Exception as exc:
                logger.error("Error evaluating inline invoice rule: %s", exc)

        return fired_alerts

    def _process_alert_result(self, result: AlertResult) -> bool:
        """Check 24-hour deduplication and dispatch notifications."""
        if self.alert_log_repo:
            is_duplicate = self.alert_log_repo.has_recent_alert(
                rule_name=result.rule_name,
                entity_type=result.entity_type,
                entity_id=result.entity_id,
                window_hours=self.dedup_window_hours,
            )
            if is_duplicate:
                logger.debug(
                    "Suppressed duplicate alert '%s' for %s:%s",
                    result.rule_name,
                    result.entity_type,
                    result.entity_id,
                )
                return False

            self.alert_log_repo.record_alert(
                rule_name=result.rule_name,
                entity_type=result.entity_type,
                entity_id=result.entity_id,
            )

        if self.notification_service:
            self._dispatch_notifications(result)

        return True

    def _dispatch_notifications(self, result: AlertResult) -> None:
        """Route alert to permitted users via NotificationService (in-app & email)."""
        if result.rule_name == "restock_alert":
            # RestockAlertRule dispatches directly to targeted subscribers
            return

        recipients: list[tuple[str, str | None]] = []

        if self.profile_repo:
            try:
                profiles = self.profile_repo.list_all(limit=100)
                for p in profiles:
                    if getattr(p, "is_active", True):
                        recipients.append((p.id, getattr(p, "email", None)))
            except Exception as exc:
                logger.warning("Failed to list profiles for alert dispatch: %s", exc)

        if not recipients:
            recipients = [("admin-system-user", "admin@wareflow.io")]

        for user_id, email in recipients:
            try:
                self.notification_service.notify(
                    user_id=user_id,
                    type=result.alert_type,
                    title=result.title,
                    body=result.body,
                    channels=["in_app", "email"],
                    recipient_email=email,
                    metadata=result.metadata,
                )
            except Exception as exc:
                logger.error("Failed to deliver alert to user %s: %s", user_id, exc)

    def get_compliance_summary(
        self, reference_date: date | None = None
    ) -> ComplianceSummaryResponse:
        """Compute aggregate compliance health breakdown (Step 7.4)."""
        today = reference_date or date.today()

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

        active_alerts: list[AlertItemResponse] = []
        for r in self._rules:
            if isinstance(r, ExpiringLicenseRule) or (hasattr(r, "evaluate") and not isinstance(r, BaseAlertRule)):
                res = r.evaluate(reference_date=reference_date)
                active_alerts.extend(res)

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
