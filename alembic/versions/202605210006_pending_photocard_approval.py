"""pending photocard approval

Revision ID: 202605210006
Revises: 202605210005
Create Date: 2026-05-21 23:25:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605210006"
down_revision: str | None = "202605210005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pending_photocards", sa.Column("approved_photocard_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_pending_photocards_approved_photocard_id",
        "pending_photocards",
        "photocards",
        ["approved_photocard_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("ck_pending_photocard_status", "pending_photocards", type_="check")
    op.create_check_constraint(
        "ck_pending_photocard_status",
        "pending_photocards",
        "catalog_status IN ('pending', 'rejected', 'approved')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_pending_photocard_status", "pending_photocards", type_="check")
    op.create_check_constraint(
        "ck_pending_photocard_status",
        "pending_photocards",
        "catalog_status IN ('pending', 'rejected')",
    )
    op.drop_constraint(
        "fk_pending_photocards_approved_photocard_id",
        "pending_photocards",
        type_="foreignkey",
    )
    op.drop_column("pending_photocards", "approved_photocard_id")
