"""SQLAlchemy + In-Memory implementations of LeadRepositoryInterface."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadScanRun
from app.repositories.interfaces.lead_repository import LeadRepositoryInterface


class SqlAlchemyLeadRepository(LeadRepositoryInterface):
    """Database-backed lead repository implementation."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_lead_by_id(self, lead_id: str) -> Lead | None:
        """Return a lead by its primary key id, or None if not found."""
        stmt = select(Lead).where(Lead.id == lead_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_lead_by_place_id(self, place_id: str) -> Lead | None:
        """Return a lead by its Google Places place_id, or None if not found."""
        stmt = select(Lead).where(Lead.place_id == place_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_all_place_ids(self) -> set[str]:
        """Return all known place_ids for fast deduplication lookups."""
        stmt = select(Lead.place_id)
        rows = self._session.execute(stmt).scalars().all()
        return set(rows)

    def create_lead(self, lead: Lead) -> Lead:
        """Persist a new lead row."""
        self._session.add(lead)
        self._session.flush()
        return lead

    def update_lead(self, lead: Lead) -> Lead:
        """Merge and flush updated lead fields."""
        self._session.merge(lead)
        self._session.flush()
        return lead

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
        """Return paginated, filtered leads."""
        stmt = select(Lead)
        count_stmt = select(func.count(Lead.id))

        if is_new is not None:
            stmt = stmt.where(Lead.is_new == is_new)
            count_stmt = count_stmt.where(Lead.is_new == is_new)
        if contacted is not None:
            stmt = stmt.where(Lead.contacted == contacted)
            count_stmt = count_stmt.where(Lead.contacted == contacted)
        if category:
            stmt = stmt.where(Lead.category == category)
            count_stmt = count_stmt.where(Lead.category == category)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(or_(Lead.name.ilike(term), Lead.address.ilike(term)))
            count_stmt = count_stmt.where(or_(Lead.name.ilike(term), Lead.address.ilike(term)))
        if min_lat is not None:
            stmt = stmt.where(Lead.lat >= min_lat)
            count_stmt = count_stmt.where(Lead.lat >= min_lat)
        if max_lat is not None:
            stmt = stmt.where(Lead.lat <= max_lat)
            count_stmt = count_stmt.where(Lead.lat <= max_lat)
        if min_lng is not None:
            stmt = stmt.where(Lead.lng >= min_lng)
            count_stmt = count_stmt.where(Lead.lng >= min_lng)
        if max_lng is not None:
            stmt = stmt.where(Lead.lng <= max_lng)
            count_stmt = count_stmt.where(Lead.lng <= max_lng)

        total = self._session.execute(count_stmt).scalar() or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Lead.first_seen_at.desc()).offset(offset).limit(page_size)
        leads = list(self._session.execute(stmt).scalars().all())
        return leads, total

    def create_scan_run(self, scan_run: LeadScanRun) -> LeadScanRun:
        """Persist a scan run audit record."""
        self._session.add(scan_run)
        self._session.flush()
        return scan_run

    def list_scan_runs(self, page: int = 1, page_size: int = 20) -> tuple[list[LeadScanRun], int]:
        """Return paginated scan history."""
        count_stmt = select(func.count(LeadScanRun.id))
        total = self._session.execute(count_stmt).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(LeadScanRun).order_by(LeadScanRun.run_at.desc()).offset(offset).limit(page_size)
        )
        runs = list(self._session.execute(stmt).scalars().all())
        return runs, total

    def mark_lead_contacted(
        self, lead_id: str, notes: str | None = None, contacted: bool = True
    ) -> Lead | None:
        """Mark lead as contacted and clear is_new highlight."""
        stmt = select(Lead).where(Lead.id == lead_id)
        lead = self._session.execute(stmt).scalar_one_or_none()
        if not lead:
            return None
        lead.contacted = contacted
        if contacted:
            lead.is_new = False
        if notes is not None:
            lead.contact_notes = notes
        self._session.flush()
        return lead

    def link_converted_retailer(self, lead_id: str, retailer_id: str) -> Lead | None:
        """Link lead to a created retailer record, marking contacted=True and is_new=False."""
        stmt = select(Lead).where(Lead.id == lead_id)
        lead = self._session.execute(stmt).scalar_one_or_none()
        if not lead:
            return None
        lead.converted_retailer_id = retailer_id
        lead.contacted = True
        lead.is_new = False
        self._session.flush()
        return lead


class InMemoryLeadRepository(LeadRepositoryInterface):
    """In-memory lead repository for testing without a database."""

    def __init__(self) -> None:
        self._leads: dict[str, Lead] = {}
        self._scan_runs: list[LeadScanRun] = []

    def get_lead_by_id(self, lead_id: str) -> Lead | None:
        """Lookup lead by ID in memory."""
        return self._leads.get(lead_id)

    def get_lead_by_place_id(self, place_id: str) -> Lead | None:
        """Lookup lead by place_id."""
        for lead in self._leads.values():
            if lead.place_id == place_id:
                return lead
        return None

    def get_all_place_ids(self) -> set[str]:
        """Return all known place_ids."""
        return {lead.place_id for lead in self._leads.values()}

    def create_lead(self, lead: Lead) -> Lead:
        """Add lead to in-memory store."""
        self._leads[lead.id] = lead
        return lead

    def update_lead(self, lead: Lead) -> Lead:
        """Update lead in in-memory store."""
        self._leads[lead.id] = lead
        return lead

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
        """Paginated listing with filters."""
        results = list(self._leads.values())
        if is_new is not None:
            results = [r for r in results if r.is_new == is_new]
        if contacted is not None:
            results = [r for r in results if r.contacted == contacted]
        if category:
            results = [r for r in results if r.category == category]
        if search:
            q = search.lower()
            results = [
                r
                for r in results
                if (r.name and q in r.name.lower()) or (r.address and q in r.address.lower())
            ]
        if min_lat is not None:
            results = [r for r in results if r.lat is not None and r.lat >= min_lat]
        if max_lat is not None:
            results = [r for r in results if r.lat is not None and r.lat <= max_lat]
        if min_lng is not None:
            results = [r for r in results if r.lng is not None and r.lng >= min_lng]
        if max_lng is not None:
            results = [r for r in results if r.lng is not None and r.lng <= max_lng]

        total = len(results)
        results.sort(key=lambda r: r.first_seen_at or "", reverse=True)
        offset = (page - 1) * page_size
        return results[offset : offset + page_size], total

    def create_scan_run(self, scan_run: LeadScanRun) -> LeadScanRun:
        """Store scan run record."""
        self._scan_runs.append(scan_run)
        return scan_run

    def list_scan_runs(self, page: int = 1, page_size: int = 20) -> tuple[list[LeadScanRun], int]:
        """Paginated scan history."""
        total = len(self._scan_runs)
        runs = sorted(self._scan_runs, key=lambda r: r.run_at or "", reverse=True)
        offset = (page - 1) * page_size
        return runs[offset : offset + page_size], total

    def mark_lead_contacted(
        self, lead_id: str, notes: str | None = None, contacted: bool = True
    ) -> Lead | None:
        """Mark lead as contacted in memory and clear is_new."""
        lead = self._leads.get(lead_id)
        if not lead:
            return None
        lead.contacted = contacted
        if contacted:
            lead.is_new = False
        if notes is not None:
            lead.contact_notes = notes
        return lead

    def link_converted_retailer(self, lead_id: str, retailer_id: str) -> Lead | None:
        """Link lead to a created retailer in memory."""
        lead = self._leads.get(lead_id)
        if not lead:
            return None
        lead.converted_retailer_id = retailer_id
        lead.contacted = True
        lead.is_new = False
        return lead

