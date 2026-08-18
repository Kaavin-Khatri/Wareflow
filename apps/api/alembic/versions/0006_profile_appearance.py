"""appearance preferences on user profiles

Revision ID: 0006_profile_appearance
Revises: 0005_two_factor_auth
Create Date: 2026-08-17 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_profile_appearance"
down_revision: str | Sequence[str] | None = "0005_two_factor_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "theme_preference",
            sa.String(length=20),
            nullable=False,
            server_default="system",
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "accent_color",
            sa.String(length=30),
            nullable=False,
            server_default="violet",
        ),
    )


def downgrade() -> None:
    op.drop_column("profiles", "accent_color")
    op.drop_column("profiles", "theme_preference")
