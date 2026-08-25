"""leads + lead_scan_runs tables for Google Places lead scanner

Revision ID: 0007_leads_and_scan_runs
Revises: 0006_profile_appearance
Create Date: 2026-08-24 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_leads_and_scan_runs"
down_revision: str | Sequence[str] | None = "0006_profile_appearance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("place_id", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "category",
            sa.String(50),
            nullable=False,
            server_default="other",
        ),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("lat", sa.Float, nullable=True),
        sa.Column("lng", sa.Float, nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("google_maps_url", sa.String(500), nullable=True),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("is_new", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("contacted", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("contact_notes", sa.Text, nullable=True),
        sa.Column(
            "converted_retailer_id",
            sa.String(36),
            sa.ForeignKey("retailers.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_leads_place_id", "leads", ["place_id"], unique=True)
    op.create_index("ix_leads_category", "leads", ["category"])
    op.create_index("ix_leads_is_new", "leads", ["is_new"])
    op.create_index("ix_leads_first_seen_at", "leads", ["first_seen_at"])

    op.create_table(
        "lead_scan_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("center_lat", sa.Float, nullable=False),
        sa.Column("center_lng", sa.Float, nullable=False),
        sa.Column("radius_m", sa.Integer, nullable=False),
        sa.Column("results_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("new_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_lead_scan_runs_run_at", "lead_scan_runs", ["run_at"])


def downgrade() -> None:
    op.drop_index("ix_lead_scan_runs_run_at", table_name="lead_scan_runs")
    op.drop_table("lead_scan_runs")
    op.drop_index("ix_leads_first_seen_at", table_name="leads")
    op.drop_index("ix_leads_is_new", table_name="leads")
    op.drop_index("ix_leads_category", table_name="leads")
    op.drop_index("ix_leads_place_id", table_name="leads")
    op.drop_table("leads")
