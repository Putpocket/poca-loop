from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConditionGrade(Base):
    __tablename__ = "condition_grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class UserHave(Base):
    __tablename__ = "user_haves"
    __table_args__ = (
        UniqueConstraint("user_id", "photocard_id", "condition_grade_id", name="uq_have_user_card_grade"),
        UniqueConstraint(
            "user_id",
            "pending_photocard_id",
            "condition_grade_id",
            name="uq_have_user_pending_card_grade",
        ),
        CheckConstraint(
            "(photocard_id IS NOT NULL AND pending_photocard_id IS NULL) OR "
            "(photocard_id IS NULL AND pending_photocard_id IS NOT NULL)",
            name="ck_have_exactly_one_card_ref",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    photocard_id: Mapped[int | None] = mapped_column(ForeignKey("photocards.id", ondelete="CASCADE"))
    pending_photocard_id: Mapped[int | None] = mapped_column(
        ForeignKey("pending_photocards.id", ondelete="CASCADE")
    )
    condition_grade_id: Mapped[int] = mapped_column(ForeignKey("condition_grades.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="haves")
    photocard: Mapped["Photocard | None"] = relationship()
    pending_photocard: Mapped["PendingPhotocard | None"] = relationship()
    condition_grade: Mapped[ConditionGrade] = relationship()


class UserWant(Base):
    __tablename__ = "user_wants"
    __table_args__ = (
        UniqueConstraint("user_id", "photocard_id", name="uq_want_user_card"),
        UniqueConstraint("user_id", "pending_photocard_id", name="uq_want_user_pending_card"),
        CheckConstraint(
            "(photocard_id IS NOT NULL AND pending_photocard_id IS NULL) OR "
            "(photocard_id IS NULL AND pending_photocard_id IS NOT NULL)",
            name="ck_want_exactly_one_card_ref",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    photocard_id: Mapped[int | None] = mapped_column(ForeignKey("photocards.id", ondelete="CASCADE"))
    pending_photocard_id: Mapped[int | None] = mapped_column(
        ForeignKey("pending_photocards.id", ondelete="CASCADE")
    )
    minimum_condition_grade_id: Mapped[int | None] = mapped_column(ForeignKey("condition_grades.id"))
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="wants")
    photocard: Mapped["Photocard | None"] = relationship()
    pending_photocard: Mapped["PendingPhotocard | None"] = relationship()
    minimum_condition_grade: Mapped[ConditionGrade | None] = relationship()
