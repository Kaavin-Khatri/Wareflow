"""two factor authentication columns on profiles

Revision ID: 0005_two_factor_auth
Revises: 0004_user_profiles
Create Date: 2026-08-17 19:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_two_factor_auth"
down_revision: str | Sequence[str] | None = "0004_user_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("totp_secret_encrypted", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "profiles",
        sa.Column("backup_codes_encrypted", sa.String(length=2000), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("totp_enrolled_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("profiles", "totp_enrolled_at")
    op.drop_column("profiles", "backup_codes_encrypted")
    op.drop_column("profiles", "totp_enabled")
    op.drop_column("profiles", "totp_secret_encrypted")
