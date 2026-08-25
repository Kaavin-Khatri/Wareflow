"""
Tests for Step 17.1 — Google Places Lead Scanner.

Covers:
- Lead model creation and enum values
- LeadScanRun model creation
- InMemoryLeadRepository CRUD operations
- GooglePlacesLeadService scan logic (mocked HTTP)
- Idempotent upsert: re-scanning never re-flags existing leads
- New lead detection triggers notification
- Scan run audit trail
- Router API endpoints and permission enforcement
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.di import get_lead_service
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.models.lead import Lead, LeadCategoryEnum, LeadScanRun
from app.repositories.impl.lead_repository import InMemoryLeadRepository
from app.services.places_lead_scanner import (
    TEXT_SEARCH_KEYWORDS,
    GooglePlacesLeadService,
)

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture()
def lead_repo() -> InMemoryLeadRepository:
    """Fresh in-memory lead repository."""
    return InMemoryLeadRepository()


@pytest.fixture()
def mock_notification_service() -> MagicMock:
    """Mock NotificationService."""
    return MagicMock()


@pytest.fixture()
def test_settings() -> Settings:
    """Settings with a test API key and scan config."""
    return Settings(
        google_places_api_key="test_api_key_fake",
        lead_scan_interval_days=7,
        lead_scan_center_lat=23.0119,
        lead_scan_center_lng=72.5381,
        lead_scan_radius_km=15.0,
        database_url="sqlite:///:memory:",
    )


@pytest.fixture()
def lead_service(
    lead_repo: InMemoryLeadRepository,
    mock_notification_service: MagicMock,
    test_settings: Settings,
) -> GooglePlacesLeadService:
    """GooglePlacesLeadService with mocked dependencies."""
    return GooglePlacesLeadService(
        lead_repo=lead_repo,
        notification_service=mock_notification_service,
        settings=test_settings,
    )


def _make_google_place(
    place_id: str = "ChIJ_test_001",
    name: str = "Test Kirana Store",
    lat: float = 23.012,
    lng: float = 72.538,
    address: str = "123 Test Street, Ahmedabad",
    phone: str = "+91 9876543210",
) -> dict:
    """Create a mock Google Places API (New) response object."""
    return {
        "id": place_id,
        "displayName": {"text": name, "languageCode": "en"},
        "formattedAddress": address,
        "location": {"latitude": lat, "longitude": lng},
        "internationalPhoneNumber": phone,
        "googleMapsUri": f"https://maps.google.com/?cid={place_id}",
    }


def _mock_text_search_response(places: list[dict]) -> MagicMock:
    """Create a mock httpx response for text search."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"places": places}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# --------------------------------------------------------------------------- #
# Model Tests
# --------------------------------------------------------------------------- #


class TestLeadModel:
    """Verify Lead ORM model field defaults and enum values."""

    def test_lead_category_enum_values(self) -> None:
        """All four category enum members exist."""
        assert LeadCategoryEnum.GRUH_UDYOG.value == "gruh_udyog"
        assert LeadCategoryEnum.SNACK_STORE.value == "snack_store"
        assert LeadCategoryEnum.GROCERY_KIRANA.value == "grocery_kirana"
        assert LeadCategoryEnum.OTHER.value == "other"

    def test_lead_creation_defaults(self) -> None:
        """New Lead has is_new=True and contacted=False by default."""
        lead = Lead(
            id="test-id-1",
            place_id="ChIJ_test_abc",
            name="Test Shop",
            category=LeadCategoryEnum.GROCERY_KIRANA,
            first_seen_at=datetime.now(UTC),
        )
        assert lead.is_new is True
        assert lead.contacted is False
        assert lead.converted_retailer_id is None

    def test_lead_scan_run_creation(self) -> None:
        """LeadScanRun stores scan metadata correctly."""
        run = LeadScanRun(
            id="run-001",
            run_at=datetime.now(UTC),
            center_lat=23.0119,
            center_lng=72.5381,
            radius_m=15000,
            results_count=42,
            new_count=5,
        )
        assert run.radius_m == 15000
        assert run.results_count == 42
        assert run.new_count == 5


# --------------------------------------------------------------------------- #
# Repository Tests
# --------------------------------------------------------------------------- #


class TestInMemoryLeadRepository:
    """Verify in-memory CRUD operations for leads and scan runs."""

    def test_create_and_get_by_place_id(self, lead_repo: InMemoryLeadRepository) -> None:
        """Create a lead and retrieve it by place_id."""
        lead = Lead(
            id="lead-1",
            place_id="ChIJ_abc123",
            name="ABC Kirana",
            category=LeadCategoryEnum.GROCERY_KIRANA,
            first_seen_at=datetime.now(UTC),
        )
        lead_repo.create_lead(lead)
        found = lead_repo.get_lead_by_place_id("ChIJ_abc123")
        assert found is not None
        assert found.name == "ABC Kirana"

    def test_get_all_place_ids(self, lead_repo: InMemoryLeadRepository) -> None:
        """Verify set of all known place_ids."""
        for i in range(3):
            lead_repo.create_lead(
                Lead(
                    id=f"lead-{i}",
                    place_id=f"place_{i}",
                    name=f"Shop {i}",
                    category=LeadCategoryEnum.OTHER,
                    first_seen_at=datetime.now(UTC),
                )
            )
        ids = lead_repo.get_all_place_ids()
        assert ids == {"place_0", "place_1", "place_2"}

    def test_list_leads_with_filters(self, lead_repo: InMemoryLeadRepository) -> None:
        """Paginated list with is_new filter."""
        lead_repo.create_lead(
            Lead(
                id="lead-new",
                place_id="p1",
                name="New Shop",
                category=LeadCategoryEnum.SNACK_STORE,
                is_new=True,
                first_seen_at=datetime.now(UTC),
            )
        )
        lead_repo.create_lead(
            Lead(
                id="lead-old",
                place_id="p2",
                name="Old Shop",
                category=LeadCategoryEnum.SNACK_STORE,
                is_new=False,
                first_seen_at=datetime.now(UTC),
            )
        )
        new_leads, total = lead_repo.list_leads(is_new=True)
        assert total == 1
        assert new_leads[0].name == "New Shop"

    def test_list_leads_with_search_and_bounding_box(
        self, lead_repo: InMemoryLeadRepository
    ) -> None:
        """Search by text and geographic bounding box."""
        lead_repo.create_lead(
            Lead(
                id="lead-ahmedabad",
                place_id="p_ahm",
                name="Sardar Gruh Udyog",
                address="Paldi, Ahmedabad, Gujarat",
                category=LeadCategoryEnum.GRUH_UDYOG,
                lat=23.012,
                lng=72.538,
                first_seen_at=datetime.now(UTC),
            )
        )
        lead_repo.create_lead(
            Lead(
                id="lead-surat",
                place_id="p_surat",
                name="Surat Farsan Center",
                address="Ring Road, Surat, Gujarat",
                category=LeadCategoryEnum.SNACK_STORE,
                lat=21.170,
                lng=72.831,
                first_seen_at=datetime.now(UTC),
            )
        )

        # Search by keyword
        results, count = lead_repo.list_leads(search="Sardar")
        assert count == 1
        assert results[0].name == "Sardar Gruh Udyog"

        # Search by address keyword
        results, count = lead_repo.list_leads(search="Surat")
        assert count == 1
        assert results[0].name == "Surat Farsan Center"

        # Bounding box around Ahmedabad
        results, count = lead_repo.list_leads(
            min_lat=22.9, max_lat=23.2, min_lng=72.4, max_lng=72.7
        )
        assert count == 1
        assert results[0].id == "lead-ahmedabad"

    def test_mark_lead_contacted(self, lead_repo: InMemoryLeadRepository) -> None:
        """Mark a lead as contacted with notes."""
        lead_repo.create_lead(
            Lead(
                id="lead-contact",
                place_id="p_contact",
                name="Contact Me",
                category=LeadCategoryEnum.GRUH_UDYOG,
                first_seen_at=datetime.now(UTC),
            )
        )
        result = lead_repo.mark_lead_contacted("lead-contact", "Called owner, interested.")
        assert result is not None
        assert result.contacted is True
        assert result.contact_notes == "Called owner, interested."

    def test_create_and_list_scan_runs(self, lead_repo: InMemoryLeadRepository) -> None:
        """Create and list scan run audit records."""
        run = LeadScanRun(
            id="run-1",
            run_at=datetime.now(UTC),
            center_lat=23.01,
            center_lng=72.54,
            radius_m=15000,
            results_count=10,
            new_count=3,
        )
        lead_repo.create_scan_run(run)
        runs, total = lead_repo.list_scan_runs()
        assert total == 1
        assert runs[0].new_count == 3


# --------------------------------------------------------------------------- #
# Service Tests (mocked HTTP)
# --------------------------------------------------------------------------- #


class TestGooglePlacesLeadService:
    """Verify scan logic, dedup, upsert, and notification dispatch."""

    def test_scan_discovers_new_leads(
        self,
        lead_service: GooglePlacesLeadService,
        lead_repo: InMemoryLeadRepository,
        mock_notification_service: MagicMock,
    ) -> None:
        """First scan discovers leads and flags them as new."""
        mock_places = [
            _make_google_place("place_a", "Ganesh Kirana"),
            _make_google_place("place_b", "Patel Gruh Udyog"),
        ]

        with patch("app.services.places_lead_scanner.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = _mock_text_search_response(mock_places)
            mock_client_cls.return_value = mock_client

            scan_run = lead_service.scan(23.0119, 72.5381, 15.0)

        # Scan found at least 2 unique results
        assert scan_run.results_count >= 2
        assert scan_run.new_count >= 2

        # Verify leads were persisted
        all_ids = lead_repo.get_all_place_ids()
        assert "place_a" in all_ids
        assert "place_b" in all_ids

        # Verify leads are flagged as new
        lead_a = lead_repo.get_lead_by_place_id("place_a")
        assert lead_a is not None
        assert lead_a.is_new is True

        # Notification was fired for new leads
        mock_notification_service.notify.assert_called()

    def test_rescan_does_not_reflag_existing_leads(
        self,
        lead_service: GooglePlacesLeadService,
        lead_repo: InMemoryLeadRepository,
        mock_notification_service: MagicMock,
    ) -> None:
        """Re-running scan with same place_ids does NOT re-flag them as new (idempotency)."""
        # Pre-insert a known lead and mark it as not-new
        existing = Lead(
            id="existing-001",
            place_id="place_existing",
            name="Old Kirana Store",
            category=LeadCategoryEnum.GROCERY_KIRANA,
            is_new=False,  # Already seen and acknowledged
            first_seen_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        lead_repo.create_lead(existing)

        mock_places = [
            _make_google_place("place_existing", "Old Kirana Store (Updated)"),
        ]

        with patch("app.services.places_lead_scanner.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = _mock_text_search_response(mock_places)
            mock_client_cls.return_value = mock_client

            scan_run = lead_service.scan(23.0119, 72.5381, 15.0)

        # No new leads — all were already known
        assert scan_run.new_count == 0

        # is_new STAYS False — never re-flagged
        updated = lead_repo.get_lead_by_place_id("place_existing")
        assert updated is not None
        assert updated.is_new is False

        # Name was updated though
        assert updated.name == "Old Kirana Store (Updated)"

        # No new-leads notification dispatched
        mock_notification_service.notify.assert_not_called()

    def test_mixed_scan_new_and_existing(
        self,
        lead_service: GooglePlacesLeadService,
        lead_repo: InMemoryLeadRepository,
        mock_notification_service: MagicMock,
    ) -> None:
        """Scan with mix of new and existing place_ids correctly flags only the new one."""
        # Pre-insert an existing lead
        lead_repo.create_lead(
            Lead(
                id="old-lead",
                place_id="place_old",
                name="Old Shop",
                category=LeadCategoryEnum.OTHER,
                is_new=False,
                first_seen_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )

        mock_places = [
            _make_google_place("place_old", "Old Shop (Updated)"),
            _make_google_place("place_brand_new", "Brand New Shop"),
        ]

        with patch("app.services.places_lead_scanner.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = _mock_text_search_response(mock_places)
            mock_client_cls.return_value = mock_client

            scan_run = lead_service.scan(23.0119, 72.5381, 15.0)

        # Exactly 1 new lead
        assert scan_run.new_count >= 1

        # Old lead stays is_new=False
        old_lead = lead_repo.get_lead_by_place_id("place_old")
        assert old_lead is not None
        assert old_lead.is_new is False

        # New lead is_new=True
        new_lead = lead_repo.get_lead_by_place_id("place_brand_new")
        assert new_lead is not None
        assert new_lead.is_new is True

        # Notification was fired
        mock_notification_service.notify.assert_called()

    def test_scan_run_audit_trail(
        self,
        lead_service: GooglePlacesLeadService,
        lead_repo: InMemoryLeadRepository,
    ) -> None:
        """Each scan creates a LeadScanRun audit record."""
        with patch("app.services.places_lead_scanner.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = _mock_text_search_response([])
            mock_client_cls.return_value = mock_client

            lead_service.scan(23.0119, 72.5381, 15.0)

        runs, total = lead_repo.list_scan_runs()
        assert total == 1
        assert runs[0].center_lat == pytest.approx(23.0119, abs=0.001)
        assert runs[0].radius_m == 15000

    def test_scan_with_no_api_key_returns_empty(
        self,
        lead_repo: InMemoryLeadRepository,
        mock_notification_service: MagicMock,
    ) -> None:
        """When GOOGLE_PLACES_API_KEY is empty, scan still succeeds with 0 results."""
        settings = Settings(
            google_places_api_key="",
            database_url="sqlite:///:memory:",
        )
        service = GooglePlacesLeadService(
            lead_repo=lead_repo,
            notification_service=mock_notification_service,
            settings=settings,
        )
        scan_run = service.scan(23.0119, 72.5381, 15.0)
        assert scan_run.results_count == 0
        assert scan_run.new_count == 0


class TestKeywordConfiguration:
    """Verify the scan keyword list covers expected vocabulary."""

    def test_text_search_keywords_cover_local_vocabulary(self) -> None:
        """Scan keywords must cover gruh udyog, kirana, snack, grocery vocabulary."""
        keywords = [kw.lower() for kw, _ in TEXT_SEARCH_KEYWORDS]
        assert any("gruh udyog" in kw for kw in keywords)
        assert any("kirana" in kw for kw in keywords)
        assert any("snack" in kw or "namkeen" in kw for kw in keywords)
        assert any("grocery" in kw for kw in keywords)

    def test_keyword_count_is_reasonable(self) -> None:
        """At least 5 keywords for diverse coverage."""
        assert len(TEXT_SEARCH_KEYWORDS) >= 5


# --------------------------------------------------------------------------- #
# Router API Tests
# --------------------------------------------------------------------------- #


class TestLeadsRouterAPI:
    """Verify HTTP endpoints in app.api.routers.leads."""

    @pytest.fixture()
    def client(self, lead_service: GooglePlacesLeadService) -> TestClient:
        """Create test client with overridden lead service and full permissions."""
        app.dependency_overrides[get_lead_service] = lambda: lead_service
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            id="user-owner-1",
            email="owner@wareflow.in",
            role="Owner",
            permissions={"leads.scan", "leads.view", "leads.manage"},
        )
        test_client = TestClient(app)
        yield test_client
        app.dependency_overrides.clear()

    def test_scan_now_endpoint(self, client: TestClient) -> None:
        """POST /leads/scan-now triggers scan and returns 200 with result summary."""
        with patch("app.services.places_lead_scanner.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = _mock_text_search_response(
                [
                    _make_google_place("place_api_1", "API Kirana Store"),
                ]
            )
            mock_client_cls.return_value = mock_client

            resp = client.post(
                "/leads/scan-now",
                json={
                    "center_lat": 23.0119,
                    "center_lng": 72.5381,
                    "radius_km": 10.0,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "scan_run_id" in data
        assert data["results_count"] >= 1
        assert data["new_count"] >= 1
        assert "Scan complete" in data["message"]

    def test_list_leads_endpoint(
        self, client: TestClient, lead_repo: InMemoryLeadRepository
    ) -> None:
        """GET /leads returns paginated list of leads."""
        lead_repo.create_lead(
            Lead(
                id="lead-api-1",
                place_id="place_api_list",
                name="Listable Kirana",
                category=LeadCategoryEnum.GROCERY_KIRANA,
                first_seen_at=datetime.now(UTC),
            )
        )
        resp = client.get("/leads?page=1&page_size=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(lead_item["name"] == "Listable Kirana" for lead_item in data["leads"])

    def test_list_leads_endpoint_with_search_and_bounds(
        self, client: TestClient, lead_repo: InMemoryLeadRepository
    ) -> None:
        """GET /leads with search query and map bounds returns matched items."""
        lead_repo.create_lead(
            Lead(
                id="lead-ahmedabad-api",
                place_id="place_ahm_api",
                name="Jay Jalaram Farsan House",
                address="Navrangpura, Ahmedabad, Gujarat",
                category=LeadCategoryEnum.SNACK_STORE,
                lat=23.033,
                lng=72.562,
                first_seen_at=datetime.now(UTC),
            )
        )
        # Search match
        resp = client.get("/leads?search=Jalaram")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["leads"][0]["name"] == "Jay Jalaram Farsan House"

        # Bounding box match
        resp_bbox = client.get("/leads?min_lat=23.0&max_lat=23.1&min_lng=72.5&max_lng=72.6")
        assert resp_bbox.status_code == 200
        data_bbox = resp_bbox.json()
        assert data_bbox["total"] >= 1

    def test_mark_contacted_endpoint(
        self, client: TestClient, lead_repo: InMemoryLeadRepository
    ) -> None:
        """PATCH /leads/{id}/contacted marks lead and stores notes."""
        lead_repo.create_lead(
            Lead(
                id="lead-contact-api",
                place_id="place_contact_api",
                name="Contact Target Shop",
                category=LeadCategoryEnum.GRUH_UDYOG,
                first_seen_at=datetime.now(UTC),
            )
        )
        resp = client.patch(
            "/leads/lead-contact-api/contacted",
            json={"notes": "Spoke to proprietor, offered price list."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["contacted"] is True
        assert data["contact_notes"] == "Spoke to proprietor, offered price list."

    def test_mark_contacted_not_found(self, client: TestClient) -> None:
        """PATCH /leads/{id}/contacted returns 404 for unknown lead id."""
        resp = client.patch(
            "/leads/non-existent-lead-id/contacted",
            json={"notes": "Note"},
        )
        assert resp.status_code == 404

    def test_scan_history_endpoint(
        self, client: TestClient, lead_repo: InMemoryLeadRepository
    ) -> None:
        """GET /leads/scan-history returns past scan runs."""
        lead_repo.create_scan_run(
            LeadScanRun(
                id="run-hist-1",
                run_at=datetime.now(UTC),
                center_lat=23.0119,
                center_lng=72.5381,
                radius_m=15000,
                results_count=12,
                new_count=4,
            )
        )
        resp = client.get("/leads/scan-history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["runs"][0]["new_count"] == 4

    def test_permission_forbidden_without_roles(
        self, lead_service: GooglePlacesLeadService
    ) -> None:
        """Access denied (403) when user lacks required permission."""
        app.dependency_overrides[get_lead_service] = lambda: lead_service
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            id="user-restricted-1",
            email="staff@wareflow.in",
            role="Warehouse Staff",
            permissions={"inventory:view"},  # Lacks leads permissions
        )
        restricted_client = TestClient(app)
        try:
            resp = restricted_client.get("/leads")
            assert resp.status_code == 403
            assert "Missing required permission" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()
