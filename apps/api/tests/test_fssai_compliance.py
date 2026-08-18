"""Unit and integration tests for FSSAI License Compliance Tracking & Alerts (Step 7.4)."""

from datetime import date, timedelta

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.routers import alerts as alerts_router
from app.api.routers import business_settings as settings_router
from app.core.security import CurrentUser, get_current_user, require_permission
from app.models.audit_and_settings import BusinessSettings
from app.models.supplier import Supplier
from app.repositories.impl.business_settings_repository import (
    InMemoryBusinessSettingsRepository,
)
from app.repositories.impl.supplier_repository import InMemorySupplierRepository
from app.schemas.alerts import AlertSeverityEnum, AlertTypeEnum
from app.schemas.business_settings import BusinessSettingsUpdateRequest
from app.services.alert_engine_service import AlertEngineService, ExpiringLicenseRule
from app.services.business_settings_service import BusinessSettingsService


@pytest.fixture
def mock_owner_user() -> CurrentUser:
    """Fixture providing a mock Owner user with full permissions."""
    return CurrentUser(
        id="usr-owner-1",
        email="owner@wareflow.io",
        role="Owner",
        permissions={"*", "settings:manage"},
        display_name="Business Owner",
    )


@pytest.fixture
def test_app(mock_owner_user: CurrentUser) -> FastAPI:
    """Fixture assembling isolated FastAPI app with overridden security and repository dependencies."""
    application = FastAPI()
    application.include_router(settings_router.router)
    application.include_router(alerts_router.router)

    biz_repo = InMemoryBusinessSettingsRepository()
    sup_repo = InMemorySupplierRepository()

    biz_service = BusinessSettingsService(repository=biz_repo)
    engine = AlertEngineService(
        rules=[ExpiringLicenseRule(business_repo=biz_repo, supplier_repo=sup_repo)],
        business_repo=biz_repo,
        supplier_repo=sup_repo,
    )

    from app.core.di import get_alert_engine_service, get_business_settings_service

    application.dependency_overrides[get_current_user] = lambda: mock_owner_user
    application.dependency_overrides[require_permission("settings:manage")] = lambda: (
        mock_owner_user
    )
    application.dependency_overrides[get_business_settings_service] = lambda: biz_service
    application.dependency_overrides[get_alert_engine_service] = lambda: engine

    return application


def test_business_settings_service_crud_and_status_computation() -> None:
    """Test BusinessSettingsService profile update, validation, and FSSAI status logic."""
    repo = InMemoryBusinessSettingsRepository()
    service = BusinessSettingsService(repository=repo)

    # 1. Default when uninitialized
    initial = service.get_settings()
    assert initial.fssai_status == "missing"
    assert initial.days_until_fssai_expiry is None

    # 2. Update with valid 60-day expiry
    valid_expiry = date.today() + timedelta(days=60)
    update_payload = BusinessSettingsUpdateRequest(
        business_name="Shree Ganesh Food Traders",
        gstin="27ABCDE1234F1Z5",
        fssai_license_no="10020030040050",
        fssai_expiry_date=valid_expiry,
        address="APMC Market 1, Vashi, Navi Mumbai",
        phone="+91 98765 43210",
        email="compliance@ganeshtraders.com",
    )
    res = service.update_settings(payload=update_payload, actor_id="usr-1")
    assert res.business_name == "Shree Ganesh Food Traders"
    assert res.gstin == "27ABCDE1234F1Z5"
    assert res.fssai_status == "valid"
    assert res.days_until_fssai_expiry == 60

    # 3. Update with expiring-soon (20 days)
    update_payload.fssai_expiry_date = date.today() + timedelta(days=20)
    res_soon = service.update_settings(payload=update_payload)
    assert res_soon.fssai_status == "expiring_soon"
    assert res_soon.days_until_fssai_expiry == 20

    # 4. Update with expired date (-5 days)
    update_payload.fssai_expiry_date = date.today() - timedelta(days=5)
    res_expired = service.update_settings(payload=update_payload)
    assert res_expired.fssai_status == "expired"
    assert res_expired.days_until_fssai_expiry == -5


def test_expiring_license_rule_20_days_trigger_warning() -> None:
    """
    QA Checklist requirement:
    Setting business_settings' FSSAI expiry to 20 days from today triggers the expiring-soon alert.
    """
    today = date.today()
    target_expiry = today + timedelta(days=20)

    business = BusinessSettings(
        id="biz-1",
        business_name="Apex Spices & Grains",
        fssai_license_no="12345678901234",
        fssai_expiry_date=target_expiry,
    )
    business_repo = InMemoryBusinessSettingsRepository(initial_settings=business)
    supplier_repo = InMemorySupplierRepository()

    rule = ExpiringLicenseRule(
        business_repo=business_repo,
        supplier_repo=supplier_repo,
    )

    alerts = rule.evaluate(reference_date=today)

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_type == AlertTypeEnum.FSSAI_EXPIRING_SOON
    assert alert.severity == AlertSeverityEnum.WARNING
    assert alert.days_remaining == 20
    assert alert.is_escalated is False
    assert "20 Days" in alert.title
    assert alert.entity_type == "business_settings"


def test_expiring_license_rule_7_day_escalation_and_expired_supplier() -> None:
    """
    QA Checklist requirement:
    - 7-day escalation triggers critical severity.
    - Expired supplier license triggers critical expired alert.
    """
    today = date.today()

    # Business expiring in 4 days (critical escalation)
    business = BusinessSettings(
        id="biz-1",
        business_name="Apex Spices & Grains",
        fssai_license_no="12345678901234",
        fssai_expiry_date=today + timedelta(days=4),
    )
    business_repo = InMemoryBusinessSettingsRepository(initial_settings=business)

    # Supplier 1: Expired 10 days ago
    sup_expired = Supplier(
        id="sup-1",
        name="Tata Consumer Products",
        fssai_license_no="11122233344455",
        fssai_expiry_date=today - timedelta(days=10),
        is_active=True,
    )
    # Supplier 2: Valid for 90 days
    sup_valid = Supplier(
        id="sup-2",
        name="Fortune Agro Mills",
        fssai_license_no="99988877766655",
        fssai_expiry_date=today + timedelta(days=90),
        is_active=True,
    )

    supplier_repo = InMemorySupplierRepository([sup_expired, sup_valid])

    rule = ExpiringLicenseRule(
        business_repo=business_repo,
        supplier_repo=supplier_repo,
    )

    alerts = rule.evaluate(reference_date=today)

    assert len(alerts) == 2

    # 1. Distributor 4-day critical alert
    biz_alert = next(a for a in alerts if a.entity_type == "business_settings")
    assert biz_alert.severity == AlertSeverityEnum.CRITICAL
    assert biz_alert.days_remaining == 4
    assert biz_alert.is_escalated is True
    assert "URGENT" in biz_alert.title

    # 2. Supplier expired critical alert
    sup_alert = next(a for a in alerts if a.entity_type == "supplier")
    assert sup_alert.severity == AlertSeverityEnum.CRITICAL
    assert sup_alert.alert_type == AlertTypeEnum.FSSAI_EXPIRED
    assert sup_alert.days_remaining == -10
    assert sup_alert.entity_name == "Tata Consumer Products"


def test_alert_engine_ocp_extensibility_and_summary() -> None:
    """
    QA Checklist requirement:
    Adding ExpiringLicenseRule required zero changes to the alert engine (OCP proof).
    """
    today = date.today()

    business = BusinessSettings(
        id="biz-1",
        business_name="Apex Spices",
        fssai_license_no="12345678901234",
        fssai_expiry_date=today + timedelta(days=15),
    )
    business_repo = InMemoryBusinessSettingsRepository(initial_settings=business)

    sup1 = Supplier(
        id="sup-1",
        name="Expired Supplier",
        fssai_expiry_date=today - timedelta(days=2),
        is_active=True,
    )
    sup2 = Supplier(
        id="sup-2",
        name="Soon Supplier",
        fssai_expiry_date=today + timedelta(days=25),
        is_active=True,
    )
    sup3 = Supplier(
        id="sup-3",
        name="Compliant Supplier",
        fssai_expiry_date=today + timedelta(days=120),
        is_active=True,
    )
    sup4 = Supplier(
        id="sup-4",
        name="No License Supplier",
        fssai_expiry_date=None,
        is_active=True,
    )

    supplier_repo = InMemorySupplierRepository([sup1, sup2, sup3, sup4])

    license_rule = ExpiringLicenseRule(business_repo=business_repo, supplier_repo=supplier_repo)

    # Engine initialized with rules
    engine = AlertEngineService(
        rules=[license_rule],
        business_repo=business_repo,
        supplier_repo=supplier_repo,
    )

    summary = engine.get_compliance_summary(reference_date=today)

    assert summary.business_fssai_status == "expiring_soon"
    assert summary.business_days_remaining == 15
    assert summary.total_suppliers == 4
    assert summary.suppliers_compliant == 1
    assert summary.suppliers_expiring_soon == 1
    assert summary.suppliers_expired == 1
    assert summary.suppliers_missing_license == 1
    assert summary.active_alerts_count == 3  # 1 biz + 1 expired sup + 1 expiring sup


def test_api_endpoints_business_settings_and_alerts(test_app: FastAPI) -> None:
    """Test HTTP API endpoints for business settings and alert summary."""
    client = TestClient(test_app)

    # 1. Update business settings via PUT
    put_res = client.put(
        "/settings/business",
        json={
            "business_name": "WareFlow Central Depot",
            "gstin": "27ABCDE1234F1Z5",
            "fssai_license_no": "10020030040050",
            "fssai_expiry_date": str(date.today() + timedelta(days=20)),
            "address": "Navi Mumbai Main Highway",
            "phone": "+91 9988776655",
            "email": "ops@wareflow.io",
        },
    )
    assert put_res.status_code == status.HTTP_200_OK
    data = put_res.json()
    assert data["business_name"] == "WareFlow Central Depot"
    assert data["fssai_status"] == "expiring_soon"
    assert data["days_until_fssai_expiry"] == 20

    # 2. Get business settings via GET
    get_res = client.get("/settings/business")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["business_name"] == "WareFlow Central Depot"

    # 3. Get compliance summary
    comp_res = client.get("/alerts/compliance")
    assert comp_res.status_code == status.HTTP_200_OK
    comp_data = comp_res.json()
    assert "business_fssai_status" in comp_data
    assert "alerts" in comp_data

    # 4. Trigger alert evaluation via POST
    eval_res = client.post("/alerts/evaluate")
    assert eval_res.status_code == status.HTTP_200_OK
    assert isinstance(eval_res.json(), list)
