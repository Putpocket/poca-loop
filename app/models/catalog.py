from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    members: Mapped[list["Member"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    releases: Mapped[list["Release"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    photocards: Mapped[list["Photocard"]] = relationship(back_populates="group")


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("group_id", "name", name="uq_member_group_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    stage_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    group: Mapped[Group] = relationship(back_populates="members")
    photocards: Mapped[list["Photocard"]] = relationship(back_populates="member")


class Release(Base):
    __tablename__ = "releases"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ("
            "'album', 'preorder_benefit', 'store_benefit', 'lucky_draw', 'fansign', "
            "'broadcast', 'popup', 'concert', 'fanmeeting', 'merch', 'season_greeting', "
            "'fanclub', 'collab', 'magazine', 'event', 'other'"
            ")",
            name="ck_release_source_type",
        ),
        UniqueConstraint(
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
            name="uq_release_source_identity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="album")
    # Legacy alias retained for existing clients. New UI/docs use "release/source".
    release_type: Mapped[str] = mapped_column(String(40), nullable=False)
    retailer_or_event: Mapped[str | None] = mapped_column(String(160))
    venue: Mapped[str | None] = mapped_column(String(160))
    country: Mapped[str | None] = mapped_column(String(80))
    round: Mapped[str | None] = mapped_column(String(80))
    detail: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(String(500))
    released_on: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    group: Mapped[Group] = relationship(back_populates="releases")
    photocards: Mapped[list["Photocard"]] = relationship(back_populates="release")


class Photocard(Base):
    __tablename__ = "photocards"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "member_id",
            "release_id",
            "name",
            "version",
            name="uq_photocard_identity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    release_id: Mapped[int | None] = mapped_column(ForeignKey("releases.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    version: Mapped[str | None] = mapped_column(String(120))
    external_url: Mapped[str | None] = mapped_column(String(2048))
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    group: Mapped[Group] = relationship(back_populates="photocards")
    member: Mapped[Member] = relationship(back_populates="photocards")
    release: Mapped[Release | None] = relationship(back_populates="photocards")


class PendingPhotocard(Base):
    __tablename__ = "pending_photocards"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ("
            "'album', 'preorder_benefit', 'store_benefit', 'lucky_draw', 'fansign', "
            "'broadcast', 'popup', 'concert', 'fanmeeting', 'merch', 'season_greeting', "
            "'fanclub', 'collab', 'magazine', 'event', 'other'"
            ")",
            name="ck_pending_photocard_source_type",
        ),
        CheckConstraint("catalog_status = 'pending'", name="ck_pending_photocard_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"))
    group_name: Mapped[str | None] = mapped_column(String(120))
    member_id: Mapped[int | None] = mapped_column(ForeignKey("members.id", ondelete="SET NULL"))
    member_name: Mapped[str | None] = mapped_column(String(120))
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_title: Mapped[str] = mapped_column(String(160), nullable=False)
    retailer_or_event: Mapped[str | None] = mapped_column(String(160))
    venue: Mapped[str | None] = mapped_column(String(160))
    country: Mapped[str | None] = mapped_column(String(80))
    round: Mapped[str | None] = mapped_column(String(80))
    detail: Mapped[str | None] = mapped_column(String(255))
    card_description: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(120))
    memo: Mapped[str | None] = mapped_column(String(500))
    catalog_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    created_by: Mapped["User"] = relationship()
    group: Mapped[Group | None] = relationship()
    member: Mapped[Member | None] = relationship()
