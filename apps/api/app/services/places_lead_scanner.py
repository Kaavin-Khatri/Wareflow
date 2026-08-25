"""
Google Places Lead Scanner service — discovers retail leads via Places API.

Scans for local wholesale-relevant businesses (gruh udyog, kirana stores, snack shops,
grocery stores) using Google Places Text Search and Nearby Search, deduplicates by
place_id, and applies first-seen-ever upsert logic to detect genuinely new shops.

SRP: This service owns only lead discovery + upsert. Notification dispatch is delegated
to NotificationService (which it receives via dependency injection).
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings
from app.models.lead import Lead, LeadCategoryEnum, LeadScanRun
from app.repositories.interfaces.lead_repository import LeadRepositoryInterface
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Keyword/type configurations for Indian wholesale territory scanning
# --------------------------------------------------------------------------- #

TEXT_SEARCH_KEYWORDS: list[tuple[str, LeadCategoryEnum]] = [
    ("gruh udyog", LeadCategoryEnum.GRUH_UDYOG),
    ("home industry food", LeadCategoryEnum.GRUH_UDYOG),
    ("kirana store", LeadCategoryEnum.GROCERY_KIRANA),
    ("grocery store", LeadCategoryEnum.GROCERY_KIRANA),
    ("namkeen shop", LeadCategoryEnum.SNACK_STORE),
    ("snacks shop", LeadCategoryEnum.SNACK_STORE),
    ("farsan shop", LeadCategoryEnum.SNACK_STORE),
    ("general store", LeadCategoryEnum.GROCERY_KIRANA),
]

NEARBY_SEARCH_TYPES: list[str] = [
    "grocery_or_supermarket",
    "convenience_store",
]

GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"

MAX_RESULTS_PER_QUERY = 20


class GooglePlacesLeadService:
    """
    Discovers retail leads near a given center point using Google Places API (New).

    Follows SRP: responsible only for scanning and upserting leads.
    Notification of new leads is delegated to the injected NotificationService.
    """

    def __init__(
        self,
        lead_repo: LeadRepositoryInterface,
        notification_service: NotificationService,
        settings: Settings,
    ) -> None:
        self._lead_repo = lead_repo
        self._notification_service = notification_service
        self._api_key = settings.google_places_api_key
        self._lead_scan_interval_days = settings.lead_scan_interval_days

    # ----------------------------------------------------------------------- #
    # Public API
    # ----------------------------------------------------------------------- #

    def scan(
        self,
        center_lat: float,
        center_lng: float,
        radius_km: float = 15.0,
    ) -> LeadScanRun:
        """
        Execute a full lead scan around the given center point.

        1. Run text searches for each keyword + nearby searches for relevant types.
        2. Deduplicate all results by place_id.
        3. Upsert: first-ever place_id → insert with is_new=True; seen before → update details only.
        4. If any new leads found, fire notification to users with leads.view permission.
        5. Record and return the scan run audit log.
        """
        radius_m = int(radius_km * 1000)
        discovered: dict[str, dict[str, Any]] = {}

        # Collect from text searches
        for keyword, category in TEXT_SEARCH_KEYWORDS:
            try:
                results = self._text_search(keyword, center_lat, center_lng, radius_m)
                for place in results:
                    pid = place.get("id", "")
                    if pid and pid not in discovered:
                        discovered[pid] = self._normalize_place(place, category)
            except Exception as exc:
                logger.warning("Text search for '%s' failed: %s", keyword, exc)

        # Collect from nearby searches
        for place_type in NEARBY_SEARCH_TYPES:
            try:
                results = self._nearby_search(place_type, center_lat, center_lng, radius_m)
                for place in results:
                    pid = place.get("id", "")
                    if pid and pid not in discovered:
                        discovered[pid] = self._normalize_place(
                            place, LeadCategoryEnum.GROCERY_KIRANA
                        )
            except Exception as exc:
                logger.warning("Nearby search for type '%s' failed: %s", place_type, exc)

        # Upsert against existing data
        known_place_ids = self._lead_repo.get_all_place_ids()
        new_count = 0
        total_count = len(discovered)

        for place_id, place_data in discovered.items():
            if place_id in known_place_ids:
                # Update details only — never re-flag as new
                existing = self._lead_repo.get_lead_by_place_id(place_id)
                if existing:
                    existing.name = place_data["name"]
                    existing.address = place_data.get("address")
                    existing.phone = place_data.get("phone")
                    existing.lat = place_data.get("lat")
                    existing.lng = place_data.get("lng")
                    existing.google_maps_url = place_data.get("google_maps_url")
                    self._lead_repo.update_lead(existing)
            else:
                # First time seeing this place_id — new lead
                lead = Lead(
                    id=str(uuid.uuid4()),
                    place_id=place_id,
                    name=place_data["name"],
                    category=place_data.get("category", LeadCategoryEnum.OTHER),
                    address=place_data.get("address"),
                    lat=place_data.get("lat"),
                    lng=place_data.get("lng"),
                    phone=place_data.get("phone"),
                    google_maps_url=place_data.get("google_maps_url"),
                    first_seen_at=datetime.now(UTC),
                    is_new=True,
                    contacted=False,
                )
                self._lead_repo.create_lead(lead)
                new_count += 1

        # Record scan run
        scan_run = LeadScanRun(
            id=str(uuid.uuid4()),
            run_at=datetime.now(UTC),
            center_lat=center_lat,
            center_lng=center_lng,
            radius_m=radius_m,
            results_count=total_count,
            new_count=new_count,
        )
        self._lead_repo.create_scan_run(scan_run)

        # Notify if new leads found
        if new_count > 0:
            self._notify_new_leads(new_count)

        logger.info(
            "Lead scan complete: %d total results, %d new leads (center=%.4f,%.4f radius=%dm)",
            total_count,
            new_count,
            center_lat,
            center_lng,
            radius_m,
        )

        return scan_run

    # ----------------------------------------------------------------------- #
    # Google Places API calls (New API)
    # ----------------------------------------------------------------------- #

    def _text_search(
        self, query: str, lat: float, lng: float, radius_m: int
    ) -> list[dict[str, Any]]:
        """Execute a Google Places Text Search (New) request."""
        if not self._api_key:
            logger.warning("No Google Places API key configured — skipping text search.")
            return []

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.location,places.internationalPhoneNumber,"
                "places.googleMapsUri"
            ),
        }

        body = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": float(radius_m),
                }
            },
            "maxResultCount": MAX_RESULTS_PER_QUERY,
            "languageCode": "en",
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(GOOGLE_PLACES_TEXT_SEARCH_URL, json=body, headers=headers)
            resp.raise_for_status()

        data = resp.json()
        return data.get("places", [])

    def _nearby_search(
        self, place_type: str, lat: float, lng: float, radius_m: int
    ) -> list[dict[str, Any]]:
        """Execute a Google Places Nearby Search (New) request."""
        if not self._api_key:
            logger.warning("No Google Places API key configured — skipping nearby search.")
            return []

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.location,places.internationalPhoneNumber,"
                "places.googleMapsUri"
            ),
        }

        body = {
            "includedTypes": [place_type],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": float(min(radius_m, 50000)),
                }
            },
            "maxResultCount": MAX_RESULTS_PER_QUERY,
            "languageCode": "en",
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(GOOGLE_PLACES_NEARBY_SEARCH_URL, json=body, headers=headers)
            resp.raise_for_status()

        data = resp.json()
        return data.get("places", [])

    # ----------------------------------------------------------------------- #
    # Helpers
    # ----------------------------------------------------------------------- #

    @staticmethod
    def _normalize_place(
        place: dict[str, Any], default_category: LeadCategoryEnum
    ) -> dict[str, Any]:
        """Normalize a Google Places API (New) response object into a flat dict."""
        location = place.get("location", {})
        display_name = place.get("displayName", {})

        return {
            "place_id": place.get("id", ""),
            "name": display_name.get("text", "Unknown"),
            "category": default_category,
            "address": place.get("formattedAddress"),
            "lat": location.get("latitude"),
            "lng": location.get("longitude"),
            "phone": place.get("internationalPhoneNumber"),
            "google_maps_url": place.get("googleMapsUri"),
        }

    def _notify_new_leads(self, new_count: int) -> None:
        """Send notification to owners/managers about newly discovered leads."""
        plural = "shop" if new_count == 1 else "shops"
        title = f"🆕 {new_count} new {plural} found near you"
        body = (
            f"{new_count} new retail {plural} discovered in your area — "
            f"tap to view on the lead map and be the first to reach out."
        )
        try:
            # Notify all staff users — the permission guard on the leads page
            # controls visibility; here we broadcast to owner-level users.
            self._notification_service.notify(
                user_id="__broadcast_owners__",
                type="new_leads_discovered",
                title=title,
                body=body,
                channels=["in_app", "whatsapp", "email"],
                metadata={"new_count": new_count},
            )
        except Exception as exc:
            logger.warning("Failed to dispatch new-leads notification: %s", exc)
