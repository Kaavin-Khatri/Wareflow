"""Administrator Audit Service.

Manages recording and synthesizing human-readable audit timelines
for sensitive administrative actions and compliance logs.
"""

import math
from datetime import datetime
from typing import Any

from app.models.audit_and_settings import AdminAuditLog
from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.profile_repository import ProfileRepository
from app.schemas.audit import AuditLogEntryResponse, AuditLogListResponse


class AuditService:
    """Service handling audit logging, human-readable description synthesis, and querying."""

    def __init__(
        self,
        audit_repo: AuditRepository,
        profile_repo: ProfileRepository,
    ) -> None:
        self._audit_repo = audit_repo
        self._profile_repo = profile_repo

    def log(
        self,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> AdminAuditLog:
        """Record an immutable admin action in the audit log."""
        return self._audit_repo.create_log(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_value=before,
            after_value=after,
        )

    def list_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        entity_type: str | None = None,
        actor_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        action: str | None = None,
    ) -> AuditLogListResponse:
        """Query paginated audit logs and attach actor context and humanized descriptions."""
        page = max(1, page)
        page_size = min(max(1, page_size), 200)
        skip = (page - 1) * page_size

        entries, total = self._audit_repo.list_logs(
            skip=skip,
            limit=page_size,
            entity_type=entity_type,
            actor_id=actor_id,
            start_date=start_date,
            end_date=end_date,
            action=action,
        )

        actor_ids = {e.actor_id for e in entries if e.actor_id}
        profile_map: dict[str, Any] = {}
        for aid in actor_ids:
            profile = self._profile_repo.get_by_id(aid)
            if profile:
                profile_map[aid] = profile

        items: list[AuditLogEntryResponse] = []
        for entry in entries:
            actor = profile_map.get(entry.actor_id) if entry.actor_id else None
            actor_name = actor.display_name if actor else None
            actor_email = actor.email if actor else None

            description = self._generate_description(
                action=entry.action,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                before=entry.before_value,
                after=entry.after_value,
                actor_label=actor_name or actor_email or "System",
            )

            items.append(
                AuditLogEntryResponse(
                    id=entry.id,
                    actor_id=entry.actor_id,
                    actor_email=actor_email,
                    actor_name=actor_name,
                    action=entry.action,
                    entity_type=entry.entity_type,
                    entity_id=entry.entity_id,
                    description=description,
                    before_value=entry.before_value,
                    after_value=entry.after_value,
                    created_at=entry.created_at,
                )
            )

        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

        return AuditLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def _generate_description(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
        actor_label: str,
    ) -> str:
        """Synthesize a clear, readable English sentence explaining the action and diff."""
        before = before or {}
        after = after or {}

        # 1. Product Price Edits
        if action == "product_price_updated" or (
            entity_type == "product" and "wholesale_price" in after
        ):
            name = after.get("name") or before.get("name") or entity_id
            b_price = before.get("wholesale_price", 0)
            a_price = after.get("wholesale_price", 0)
            return f"{actor_label} changed wholesale price of '{name}' from ₹{b_price:,.2f} to ₹{a_price:,.2f}."

        # 2. Retailer Credit Limit Edits
        if action == "retailer_credit_limit_updated" or (
            entity_type == "retailer" and "credit_limit" in after
        ):
            name = after.get("name") or before.get("name") or entity_id
            b_lim = before.get("credit_limit", 0)
            a_lim = after.get("credit_limit", 0)
            return f"{actor_label} changed Retailer '{name}' credit limit from ₹{b_lim:,.2f} to ₹{a_lim:,.2f}."

        # 3. Role Permission Matrix Edits
        if action == "role_permissions_updated" or entity_type == "role_permissions":
            role_name = after.get("role_name") or before.get("role_name") or entity_id
            b_perms = set(before.get("permissions") or [])
            a_perms = set(after.get("permissions") or [])
            added = a_perms - b_perms
            removed = b_perms - a_perms

            diff_parts = []
            if added:
                diff_parts.append(f"added {', '.join(sorted(added))}")
            if removed:
                diff_parts.append(f"removed {', '.join(sorted(removed))}")

            diff_summary = "; ".join(diff_parts) if diff_parts else "re-saved permissions"
            return f"{actor_label} modified permissions for role '{role_name}': {diff_summary}."

        # 4. Staff Role / Status Edits
        if action == "staff_role_updated":
            email = after.get("email") or before.get("email") or entity_id
            b_role = before.get("role_name", "Unknown")
            a_role = after.get("role_name", "Unknown")
            return f"{actor_label} changed role of staff member '{email}' from '{b_role}' to '{a_role}'."

        if action == "staff_status_updated":
            email = after.get("email") or before.get("email") or entity_id
            is_active = after.get("is_active", False)
            verb = "Activated" if is_active else "Suspended"
            return f"{actor_label} {verb.lower()} staff account for '{email}'."

        # 5. Entity Deletions
        if "delete" in action:
            return f"{actor_label} deleted {entity_type} '{entity_id}'."

        # 6. Fallback
        return f"{actor_label} performed '{action}' on {entity_type} '{entity_id}'."
