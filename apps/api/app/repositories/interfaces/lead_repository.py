"""Lead repository interface — data-access contract for leads and scan runs."""

from abc import ABC, abstractmethod

from app.models.lead import Lead, LeadScanRun


class LeadRepositoryInterface(ABC):
    """Interface for managing leads and scan run audit records."""

    @abstractmethod
    def get_lead_by_id(self, lead_id: str) -> Lead | None:
        """Return a lead by its primary key id, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def get_lead_by_place_id(self, place_id: str) -> Lead | None:
        """Return a lead by its Google Places place_id, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def get_all_place_ids(self) -> set[str]:
        """Return the set of all known place_ids for fast deduplication."""
        raise NotImplementedError

    @abstractmethod
    def create_lead(self, lead: Lead) -> Lead:
        """Persist a new lead and return it."""
        raise NotImplementedError

    @abstractmethod
    def update_lead(self, lead: Lead) -> Lead:
        """Update an existing lead's mutable fields and return it."""
        raise NotImplementedError

    @abstractmethod
    def list_leads(
        self,
        is_new: bool | None = None,
        contacted: bool | None = None,
        category: str | None = None,
        search: str | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lng: float | None = None,
        max_lng: float | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Lead], int]:
        """Return paginated leads with optional filters, text search, bounding box, and total count."""
        raise NotImplementedError

    @abstractmethod
    def create_scan_run(self, scan_run: LeadScanRun) -> LeadScanRun:
        """Persist a scan run audit log and return it."""
        raise NotImplementedError

    @abstractmethod
    def list_scan_runs(self, page: int = 1, page_size: int = 20) -> tuple[list[LeadScanRun], int]:
        """Return paginated scan run history and total count."""
        raise NotImplementedError

    @abstractmethod
    def mark_lead_contacted(
        self, lead_id: str, notes: str | None = None, contacted: bool = True
    ) -> Lead | None:
        """Mark a lead as contacted (clearing is_new). Return updated lead or None."""
        raise NotImplementedError

    @abstractmethod
    def link_converted_retailer(self, lead_id: str, retailer_id: str) -> Lead | None:
        """Link lead to a newly created retailer, marking contacted=True and is_new=False."""
        raise NotImplementedError
