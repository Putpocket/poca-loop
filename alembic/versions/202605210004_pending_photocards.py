"""pending photocards

Revision ID: 202605210004
Revises: 202605210003
Create Date: 2026-05-21 22:22:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605210004"
down_revision: str | None = "202605210003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOURCE_TYPE_CHECK = (
    "source_type IN ("
    "'album', 'preorder_benefit', 'store_benefit', 'lucky_draw', 'fansign', "
    "'broadcast', 'popup', 'concert', 'fanmeeting', 'merch', 'season_greeting', "
    "'fanclub', 'collab', 'magazine', 'event', 'other'"
    ")"
)


def upgrade() -> None:
    op.create_table(
        "pending_photocards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("group_name", sa.String(length=120), nullable=True),
        sa.Column("member_id", sa.Integer(), nullable=True),
        sa.Column("member_name", sa.String(length=120), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_title", sa.String(length=160), nullable=False),
        sa.Column("retailer_or_event", sa.String(length=160), nullable=True),
        sa.Column("venue", sa.String(length=160), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("round", sa.String(length=80), nullable=True),
        sa.Column("detail", sa.String(length=255), nullable=True),
        sa.Column("card_description", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=120), nullable=True),
        sa.Column("memo", sa.String(length=500), nullable=True),
        sa.Column("catalog_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(SOURCE_TYPE_CHECK, name="ck_pending_photocard_source_type"),
        sa.CheckConstraint("catalog_status = 'pending'", name="ck_pending_photocard_status"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("user_haves", sa.Column("pending_photocard_id", sa.Integer(), nullable=True))
    op.add_column("user_wants", sa.Column("pending_photocard_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_user_haves_pending_photocard_id",
        "user_haves",
        "pending_photocards",
        ["pending_photocard_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_user_wants_pending_photocard_id",
        "user_wants",
        "pending_photocards",
        ["pending_photocard_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("user_haves", "photocard_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("user_wants", "photocard_id", existing_type=sa.Integer(), nullable=True)
    op.create_check_constraint(
        "ck_have_exactly_one_card_ref",
        "user_haves",
        "(photocard_id IS NOT NULL AND pending_photocard_id IS NULL) OR "
        "(photocard_id IS NULL AND pending_photocard_id IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_want_exactly_one_card_ref",
        "user_wants",
        "(photocard_id IS NOT NULL AND pending_photocard_id IS NULL) OR "
        "(photocard_id IS NULL AND pending_photocard_id IS NOT NULL)",
    )
    op.create_unique_constraint(
        "uq_have_user_pending_card_grade",
        "user_haves",
        ["user_id", "pending_photocard_id", "condition_grade_id"],
    )
    op.create_unique_constraint(
        "uq_want_user_pending_card",
        "user_wants",
        ["user_id", "pending_photocard_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_want_user_pending_card", "user_wants", type_="unique")
    op.drop_constraint("uq_have_user_pending_card_grade", "user_haves", type_="unique")
    op.drop_constraint("ck_want_exactly_one_card_ref", "user_wants", type_="check")
    op.drop_constraint("ck_have_exactly_one_card_ref", "user_haves", type_="check")
    op.alter_column("user_wants", "photocard_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("user_haves", "photocard_id", existing_type=sa.Integer(), nullable=False)
    op.drop_constraint("fk_user_wants_pending_photocard_id", "user_wants", type_="foreignkey")
    op.drop_constraint("fk_user_haves_pending_photocard_id", "user_haves", type_="foreignkey")
    op.drop_column("user_wants", "pending_photocard_id")
    op.drop_column("user_haves", "pending_photocard_id")
    op.drop_table("pending_photocards")
