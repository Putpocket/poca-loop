"""pending photocard rejection

Revision ID: 202605210005
Revises: 202605210004
Create Date: 2026-05-21 23:14:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605210005"
down_revision: str | None = "202605210004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pending_photocards", sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True))
    op.add_column("pending_photocards", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("pending_photocards", sa.Column("review_reason", sa.String(length=500), nullable=True))
    op.create_foreign_key(
        "fk_pending_photocards_reviewed_by_admin_id",
        "pending_photocards",
        "users",
        ["reviewed_by_admin_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("ck_pending_photocard_status", "pending_photocards", type_="check")
    op.create_check_constraint(
        "ck_pending_photocard_status",
        "pending_photocards",
        "catalog_status IN ('pending', 'rejected')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_pending_photocard_status", "pending_photocards", type_="check")
    op.create_check_constraint(
        "ck_pending_photocard_status",
        "pending_photocards",
        "catalog_status = 'pending'",
    )
    op.drop_constraint(
        "fk_pending_photocards_reviewed_by_admin_id",
        "pending_photocards",
        type_="foreignkey",
    )
    op.drop_column("pending_photocards", "review_reason")
    op.drop_column("pending_photocards", "reviewed_at")
    op.drop_column("pending_photocards", "reviewed_by_admin_id")
