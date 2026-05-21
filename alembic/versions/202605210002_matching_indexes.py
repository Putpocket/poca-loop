"""matching lookup indexes

Revision ID: 202605210002
Revises: 202605210001
Create Date: 2026-05-21 10:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202605210002"
down_revision: str | None = "202605210001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_user_haves_user_id", "user_haves", ["user_id"], unique=False)
    op.create_index("ix_user_haves_photocard_id", "user_haves", ["photocard_id"], unique=False)
    op.create_index(
        "ix_user_haves_condition_grade_id",
        "user_haves",
        ["condition_grade_id"],
        unique=False,
    )
    op.create_index("ix_user_wants_user_id", "user_wants", ["user_id"], unique=False)
    op.create_index("ix_user_wants_photocard_id", "user_wants", ["photocard_id"], unique=False)
    op.create_index(
        "ix_user_wants_minimum_condition_grade_id",
        "user_wants",
        ["minimum_condition_grade_id"],
        unique=False,
    )
    op.create_index("ix_photocards_member_id", "photocards", ["member_id"], unique=False)
    op.create_index("ix_photocards_release_id", "photocards", ["release_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_photocards_release_id", table_name="photocards")
    op.drop_index("ix_photocards_member_id", table_name="photocards")
    op.drop_index("ix_user_wants_minimum_condition_grade_id", table_name="user_wants")
    op.drop_index("ix_user_wants_photocard_id", table_name="user_wants")
    op.drop_index("ix_user_wants_user_id", table_name="user_wants")
    op.drop_index("ix_user_haves_condition_grade_id", table_name="user_haves")
    op.drop_index("ix_user_haves_photocard_id", table_name="user_haves")
    op.drop_index("ix_user_haves_user_id", table_name="user_haves")
