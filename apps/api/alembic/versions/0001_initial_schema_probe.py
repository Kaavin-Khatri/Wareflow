"""initial schema probe

Revision ID: 0001_initial_schema_probe
Revises:
Create Date: 2026-08-17 17:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema_probe"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial schema probe table to verify migration pipeline."""
    op.create_table(
        "_schema_probe",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ok"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop initial schema probe table."""
    op.drop_table("_schema_probe")
