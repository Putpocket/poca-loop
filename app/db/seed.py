from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.catalog import Group, Member, Photocard, Release
from app.models.user_card import ConditionGrade
from app.models.users import User


DEFAULT_GRADES = [
    ("S", "Sealed / Mint", "Unopened or effectively mint condition", 10),
    ("A", "Excellent", "Very light handling wear only", 20),
    ("B", "Good", "Visible minor wear, no major damage", 30),
    ("C", "Fair", "Noticeable wear or small defects", 40),
    ("D", "Damaged", "Heavy wear, bends, stains, or major defects", 50),
]


def get_or_create(db: Session, model: type, defaults: dict | None = None, **filters):
    item = db.scalar(select(model).filter_by(**filters))
    if item is not None:
        return item
    item = model(**filters, **(defaults or {}))
    db.add(item)
    db.flush()
    return item


def seed_default_data(db: Session) -> None:
    admin = db.scalar(select(User).where(User.email == settings.seed_admin_email))
    if admin is None:
        admin = User(
            email=settings.seed_admin_email,
            username=settings.seed_admin_username,
            hashed_password=hash_password(settings.seed_admin_password),
            role="admin",
        )
        db.add(admin)
    else:
        admin.role = "admin"

    for code, label, description, sort_order in DEFAULT_GRADES:
        grade = db.scalar(select(ConditionGrade).where(ConditionGrade.code == code))
        if grade is None:
            db.add(
                ConditionGrade(
                    code=code,
                    label=label,
                    description=description,
                    sort_order=sort_order,
                )
            )

    group = get_or_create(db, Group, name="NewJeans", defaults={"slug": "newjeans"})
    member = get_or_create(db, Member, group_id=group.id, name="Minji")
    release = get_or_create(
        db,
        Release,
        group_id=group.id,
        title="Get Up",
        defaults={"release_type": "album"},
    )
    existing_card = db.scalar(
        select(Photocard).where(
            Photocard.group_id == group.id,
            Photocard.member_id == member.id,
            Photocard.release_id == release.id,
            Photocard.name == "Bunny Beach",
            Photocard.version == "Sample",
        )
    )
    if existing_card is None:
        db.add(
            Photocard(
                group_id=group.id,
                member_id=member.id,
                release_id=release.id,
                name="Bunny Beach",
                version="Sample",
                external_url="https://example.com/poca-loop/sample-card",
                notes="Sample metadata only; no copyrighted image is stored.",
            )
        )

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed_default_data(db)


if __name__ == "__main__":
    main()
