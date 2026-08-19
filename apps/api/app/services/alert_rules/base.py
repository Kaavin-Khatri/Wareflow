"""Base interfaces and data structures for Alert Rules."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AlertResult:
    """Standardized result produced when an alert rule triggers."""

    rule_name: str
    entity_type: str  # "product", "batch", "invoice"
    entity_id: str
    alert_type: str  # "low_stock", "critical_stock", "expiring_batch", "overdue_invoice"
    title: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)
    target_permissions: list[str] = field(default_factory=lambda: ["inventory:view"])
    target_roles: list[str] = field(default_factory=lambda: ["Admin", "Manager", "Inventory Officer"])


@dataclass
class AlertEvaluationContext:
    """Context and dependencies passed into alert rule evaluation."""

    product_repo: Any
    stock_repo: Any
    invoice_repo: Any
    retailer_repo: Any = None
    supplier_repo: Any = None


class BaseAlertRule(ABC):
    """Abstract base class for all smart alert rules (Strategy Pattern / OCP)."""

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Unique identifier for this alert rule."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, context: AlertEvaluationContext) -> list[AlertResult]:
        """Evaluate rule across all relevant entities."""
        raise NotImplementedError

    def evaluate_entity(self, entity_id: str, context: AlertEvaluationContext) -> list[AlertResult]:
        """
        Evaluate rule specifically for a single entity (for inline fast triggers).
        Default implementation filters results of full evaluate.
        """
        results = self.evaluate(context)
        return [r for r in results if r.entity_id == str(entity_id)]
