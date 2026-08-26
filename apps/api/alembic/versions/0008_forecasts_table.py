"""forecasts table for demand forecasting cache

Revision ID: 0008_forecasts_table
Revises: 0007_leads_and_scan_runs
Create Date: 2026-08-25 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_forecasts_table"
down_revision: str | Sequence[str] | None = "0007_leads_and_scan_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "forecasts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("strategy", sa.String(50), nullable=False),
        sa.Column("horizon_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("predicted_daily_demand", sa.Numeric(10, 4), nullable=False, server_default="0.0"),
        sa.Column("total_predicted_demand", sa.Numeric(10, 2), nullable=False, server_default="0.0"),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=False, server_default="0.0"),
        sa.Column("trend_direction", sa.String(30), nullable=False, server_default="stable"),
        sa.Column("history_data_points", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="calculated"),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_forecasts_product_id", "forecasts", ["product_id"])
    op.create_index("ix_forecasts_strategy", "forecasts", ["strategy"])
    op.create_index(
        "ix_forecasts_product_strategy_horizon",
        "forecasts",
        ["product_id", "strategy", "horizon_days"],
    )


def downgrade() -> None:
    op.drop_index("ix_forecasts_product_strategy_horizon", table_name="forecasts")
    op.drop_index("ix_forecasts_strategy", table_name="forecasts")
    op.drop_index("ix_forecasts_product_id", table_name="forecasts")
    op.drop_table("forecasts")
