"""release source metadata

Revision ID: 202605210003
Revises: 202605210002
Create Date: 2026-05-21 17:27:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605210003"
down_revision: str | None = "202605210002"
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
    op.add_column("releases", sa.Column("source_type", sa.String(length=40), nullable=True))
    op.add_column("releases", sa.Column("retailer_or_event", sa.String(length=160), nullable=True))
    op.add_column("releases", sa.Column("venue", sa.String(length=160), nullable=True))
    op.add_column("releases", sa.Column("country", sa.String(length=80), nullable=True))
    op.add_column("releases", sa.Column("round", sa.String(length=80), nullable=True))
    op.add_column("releases", sa.Column("detail", sa.String(length=255), nullable=True))
    op.add_column("releases", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("releases", sa.Column("end_date", sa.Date(), nullable=True))
    op.add_column("releases", sa.Column("notes", sa.String(length=500), nullable=True))
    op.execute(
        "UPDATE releases SET source_type = CASE "
        "WHEN release_type IN ("
        "'album', 'preorder_benefit', 'store_benefit', 'lucky_draw', 'fansign', "
        "'broadcast', 'popup', 'concert', 'fanmeeting', 'merch', 'season_greeting', "
        "'fanclub', 'collab', 'magazine', 'event', 'other'"
        ") THEN release_type ELSE 'other' END"
    )
    op.alter_column("releases", "source_type", existing_type=sa.String(length=40), nullable=False)
    op.create_check_constraint("ck_release_source_type", "releases", SOURCE_TYPE_CHECK)
    op.drop_constraint("uq_release_group_title", "releases", type_="unique")
    op.create_unique_constraint(
        "uq_release_source_identity",
        "releases",
        [
            "group_id",
            "title",
            "source_type",
            "retailer_or_event",
            "venue",
            "country",
            "round",
            "detail",
            "start_date",
            "end_date",
        ],
    )


def downgrade() -> None:
    op.drop_constraint("uq_release_source_identity", "releases", type_="unique")
    op.create_unique_constraint("uq_release_group_title", "releases", ["group_id", "title"])
    op.drop_constraint("ck_release_source_type", "releases", type_="check")
    op.drop_column("releases", "notes")
    op.drop_column("releases", "end_date")
    op.drop_column("releases", "start_date")
    op.drop_column("releases", "detail")
    op.drop_column("releases", "round")
    op.drop_column("releases", "country")
    op.drop_column("releases", "venue")
    op.drop_column("releases", "retailer_or_event")
    op.drop_column("releases", "source_type")
