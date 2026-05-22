"""pending photocard merge

Revision ID: 202605220001
Revises: 202605210006
Create Date: 2026-05-22 09:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605220001"
down_revision: str | None = "202605210006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pending_photocards", sa.Column("merged_photocard_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_pending_photocards_merged_photocard_id",
        "pending_photocards",
        "photocards",
        ["merged_photocard_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("ck_pending_photocard_status", "pending_photocards", type_="check")
    op.create_check_constraint(
        "ck_pending_photocard_status",
        "pending_photocards",
        "catalog_status IN ('pending', 'rejected', 'approved', 'merged')",
    )


def downgrade() -> None:
    op.execute("UPDATE pending_photocards SET catalog_status = 'rejected' WHERE catalog_status = 'merged'")
    op.drop_constraint("ck_pending_photocard_status", "pending_photocards", type_="check")
    op.create_check_constraint(
        "ck_pending_photocard_status",
        "pending_photocards",
        "catalog_status IN ('pending', 'rejected', 'approved')",
    )
    op.drop_constraint(
        "fk_pending_photocards_merged_photocard_id",
        "pending_photocards",
        type_="foreignkey",
    )
    op.drop_column("pending_photocards", "merged_photocard_id")
