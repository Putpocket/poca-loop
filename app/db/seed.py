from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.catalog import Group, Member, Photocard, Release
from app.models.user_card import ConditionGrade
from app.models.users import User


NMIXX_MEMBERS = [
    ("릴리", "Lily"),
    ("해원", "Haewon"),
    ("설윤", "Sullyoon"),
    ("배이", "Bae"),
    ("지우", "Jiwoo"),
    ("규진", "Kyujin"),
]

NMIXX_RELEASE_SOURCES = [
    {
        "title": "AD MARE",
        "released_on": "2022-02-22",
        "sources": [
            ("album", None, "Album Photocard", "정규 앨범 랜덤 포토카드"),
            (
                "preorder_benefit",
                "Blind Package",
                "Blind Package Photocard",
                "블라인드 패키지 특전 포토카드",
            ),
            ("store_benefit", "Retailer Benefit", "Retail Benefit Photocard", "판매처 특전 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
        ],
    },
    {
        "title": "ENTWURF",
        "released_on": "2022-09-19",
        "sources": [
            ("album", None, "Album Photocard", "정규 앨범 랜덤 포토카드"),
            ("preorder_benefit", "Pre-order Benefit", "POB Photocard", "예약판매 특전 포토카드"),
            ("store_benefit", "Retailer Benefit", "Retail Benefit Photocard", "판매처 특전 포토카드"),
            ("lucky_draw", "Lucky Draw", "Lucky Draw Photocard", "럭키드로우 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
        ],
    },
    {
        "title": "Funky Glitter Christmas",
        "released_on": "2022-11-23",
        "sources": [
            ("event", "Intermixxion Single Event", "Event Photocard", "디지털 싱글 이벤트 포토카드"),
            ("store_benefit", "Makestar / Retail Event", "Retail Benefit Photocard", "판매처 이벤트 특전 포토카드"),
            ("fansign", "Video Call Event", "Video Call Photocard", "영상통화 이벤트 포토카드"),
        ],
    },
    {
        "title": "NSWER 1st Generation",
        "released_on": "2023-02-20",
        "sources": [
            ("fanclub", "Official Fanclub Kit", "Fanclub Kit Photocard", "공식 팬클럽 키트 포토카드"),
            ("fanclub", "Membership Benefit", "Membership Benefit Photocard", "팬클럽 가입/멤버십 특전 포토카드"),
        ],
    },
    {
        "title": "expergo",
        "released_on": "2023-03-20",
        "sources": [
            ("album", None, "Album Photocard", "정규 앨범 랜덤 포토카드"),
            ("album", "Digipack", "Digipack Photocard", "디지팩 버전 포토카드"),
            ("preorder_benefit", "Pre-order Benefit", "POB Photocard", "예약판매 특전 포토카드"),
            ("store_benefit", "Retailer Benefit", "Retail Benefit Photocard", "판매처 특전 포토카드"),
            ("lucky_draw", "Lucky Draw", "Lucky Draw Photocard", "럭키드로우 포토카드"),
            ("popup", "Soundwave Pop-up Store", "Pop-up Store Photocard", "팝업스토어 이벤트 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
            ("broadcast", "Music Broadcast", "Broadcast Photocard", "음악방송 참여 특전 포토카드"),
        ],
    },
    {
        "title": "A Midsummer NMIXX's Dream",
        "released_on": "2023-07-11",
        "sources": [
            ("album", None, "Album Photocard", "정규 앨범 랜덤 포토카드"),
            ("album", "Polaroid Card", "Polaroid Card", "앨범 동봉 폴라로이드 카드"),
            ("album", "Digipack", "Digipack Photocard", "디지팩 버전 포토카드"),
            ("preorder_benefit", "Pre-order Benefit", "POB Photocard", "예약판매 특전 포토카드"),
            ("store_benefit", "Retailer Benefit", "Retail Benefit Photocard", "판매처 특전 포토카드"),
            ("lucky_draw", "Lucky Draw", "Lucky Draw Photocard", "럭키드로우 포토카드"),
            ("popup", "Pop-up Store", "Pop-up Store Photocard", "팝업스토어 이벤트 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
            ("broadcast", "Music Broadcast", "Broadcast Photocard", "음악방송 참여 특전 포토카드"),
        ],
    },
    {
        "title": "NICE TO MIXX YOU",
        "released_on": "2023-10-04",
        "sources": [
            ("concert", "Showcase Tour MD", "Tour MD Photocard", "쇼케이스 투어 MD 포토카드"),
            ("concert", "VIP / Venue Benefit", "Venue Benefit Photocard", "공연장/VIP 특전 포토카드"),
            ("merch", "Tin Case Photocard Set", "Tin Case Photocard Set", "틴케이스 포토카드 세트"),
        ],
    },
    {
        "title": "NMIXX CHANGE UP: MIXX UNIVERSITY",
        "released_on": "2023-10-07",
        "sources": [
            ("fanmeeting", "Fan Concert MD", "Fan Concert MD Photocard", "팬콘서트 MD 포토카드"),
            ("fanmeeting", "Venue Benefit", "Venue Benefit Photocard", "공연장 특전 포토카드"),
            ("merch", "Tin Case Photocard Set", "Tin Case Photocard Set", "틴케이스 포토카드 세트"),
            ("merch", "Trading Card", "Trading Card", "트레이딩 카드"),
        ],
    },
    {
        "title": "2024 Season's Greetings",
        "released_on": "2023-12-01",
        "sources": [
            ("season_greeting", "Season's Greetings", "Season's Greetings Photocard", "시즌그리팅 포토카드"),
            ("season_greeting", "Pre-order Benefit", "Season's Greetings POB", "시즌그리팅 예약 특전 포토카드"),
        ],
    },
    {
        "title": "Soñar (Breaker)",
        "released_on": "2023-12-04",
        "sources": [
            ("event", "Pre-release Single Event", "Event Photocard", "선공개 싱글 이벤트 포토카드"),
            ("store_benefit", "Retailer Event", "Retail Benefit Photocard", "판매처 이벤트 특전 포토카드"),
        ],
    },
    {
        "title": "Fe3O4: BREAK",
        "released_on": "2024-01-15",
        "sources": [
            ("album", "Square One / Mixx Blood", "Album Photocard", "정규 앨범 랜덤 포토카드"),
            ("album", "Nemo", "Nemo Photocard", "네모 앨범 포토카드"),
            (
                "preorder_benefit",
                "JYP SHOP / BDM / Soundwave / Withmuu",
                "POB Photocard",
                "예약판매 특전 포토카드",
            ),
            (
                "lucky_draw",
                "JYP SHOP / Everline / Soundwave / Withmuu",
                "Lucky Draw Photocard",
                "럭키드로우 포토카드",
            ),
            ("popup", "Counting Stars / Pop-up Store", "Pop-up Benefit Photocard", "팝업/이벤트 특전 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
            ("broadcast", "Music Broadcast", "Broadcast Photocard", "음악방송 참여 특전 포토카드"),
            ("store_benefit", "Target / Retail Exclusive", "Retail Exclusive Photocard", "해외/리테일러 독점 특전 포토카드"),
        ],
    },
    {
        "title": "NSWER 2nd Generation",
        "released_on": "2024-02-01",
        "sources": [
            ("fanclub", "Official Fanclub Kit", "Fanclub Kit Photocard", "공식 팬클럽 키트 포토카드"),
            ("fanclub", "Membership Benefit", "Membership Benefit Photocard", "팬클럽 가입/멤버십 특전 포토카드"),
        ],
    },
    {
        "title": "NMIXX Official Light Stick",
        "released_on": "2024-05-01",
        "sources": [
            ("merch", "Light Stick Purchase Benefit", "Light Stick Benefit Photocard", "공식 응원봉 구매 특전 포토카드"),
            ("store_benefit", "Retailer Light Stick Benefit", "Retail Benefit Photocard", "응원봉 판매처 특전 포토카드"),
        ],
    },
    {
        "title": "NMIXX CHANGE UP: MIXX LAB",
        "released_on": "2024-05-04",
        "sources": [
            ("fanmeeting", "Fan Concert MD", "Fan Concert MD Photocard", "팬콘서트 MD 포토카드"),
            ("fanmeeting", "Venue Benefit", "Venue Benefit Photocard", "공연장 특전 포토카드"),
            ("merch", "Trading Card", "Trading Card", "트레이딩 카드"),
            ("merch", "Tin Case Photocard Set", "Tin Case Photocard Set", "틴케이스 포토카드 세트"),
        ],
    },
    {
        "title": "Fe3O4: STICK OUT",
        "released_on": "2024-08-19",
        "sources": [
            ("album", "Nephelomancy / Pyromancy", "Album Photocard", "정규 앨범 랜덤 포토카드"),
            ("album", "Nemo", "Nemo Photocard", "네모 앨범 포토카드"),
            (
                "preorder_benefit",
                "JYP SHOP / Ktown4u / MyMusicTaste / Apple Music / BDM",
                "POB Photocard",
                "예약판매 특전 포토카드",
            ),
            (
                "lucky_draw",
                "Apple Music / Soundwave / Everline",
                "Lucky Draw Photocard",
                "럭키드로우 포토카드",
            ),
            ("popup", "Fe3O4: STICK OUT Pop-up Store", "Pop-up Store Photocard", "팝업스토어 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
            ("broadcast", "Music Broadcast", "Broadcast Photocard", "음악방송 참여 특전 포토카드"),
            ("merch", "Pop-up Tin Case Photocard Set", "Tin Case Photocard Set", "팝업 MD 틴케이스 포토카드 세트"),
        ],
    },
    {
        "title": "2025 Season's Greetings",
        "released_on": "2024-12-01",
        "sources": [
            ("season_greeting", "Season's Greetings", "Season's Greetings Photocard", "시즌그리팅 포토카드"),
            ("season_greeting", "Pre-order Benefit", "Season's Greetings POB", "시즌그리팅 예약 특전 포토카드"),
        ],
    },
    {
        "title": "Fe3O4: FORWARD",
        "released_on": "2025-03-17",
        "sources": [
            ("album", None, "Album Photocard", "정규 앨범 랜덤 포토카드"),
            ("album", "Platform / POCA", "Platform Photocard", "플랫폼/포카앨범 포토카드"),
            ("preorder_benefit", "Pre-order Benefit", "POB Photocard", "예약판매 특전 포토카드"),
            ("store_benefit", "Retailer Benefit", "Retail Benefit Photocard", "판매처 특전 포토카드"),
            ("lucky_draw", "Lucky Draw", "Lucky Draw Photocard", "럭키드로우 포토카드"),
            ("popup", "Fe3O4: FORWARD Pop-up Store", "Pop-up Store Photocard", "팝업스토어 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
            ("broadcast", "Music Broadcast", "Broadcast Photocard", "음악방송 참여 특전 포토카드"),
        ],
    },
    {
        "title": "NSWER 3rd Generation",
        "released_on": "2025-04-01",
        "sources": [
            ("fanclub", "Official Fanclub Kit", "Fanclub Kit Photocard", "공식 팬클럽 키트 포토카드"),
            ("fanclub", "Membership Benefit", "Membership Benefit Photocard", "팬클럽 가입/멤버십 특전 포토카드"),
        ],
    },
    {
        "title": "MIXXPEDIA",
        "released_on": "2025-07-01",
        "sources": [
            ("merch", "Photobook / MD", "Photobook Photocard", "포토북/MD 포토카드"),
            ("store_benefit", "Retailer Benefit", "Retail Benefit Photocard", "판매처 특전 포토카드"),
        ],
    },
    {
        "title": "Blue Valentine",
        "released_on": "2025-10-13",
        "sources": [
            ("album", "Blue / Valentine / Chaos", "Album Photocard", "정규 앨범 랜덤 포토카드"),
            ("album", "Unit", "Unit Photocard", "유닛 포토카드"),
            (
                "preorder_benefit",
                "Apple Music / Ktown4u / Everline / Fans Shop / Music Korea / Musicplant / Makestar",
                "POB Photocard",
                "예약판매 특전 포토카드",
            ),
            ("store_benefit", "Retailer Benefit", "Retail Benefit Photocard", "판매처 특전 포토카드"),
            ("lucky_draw", "Lucky Draw", "Lucky Draw Photocard", "럭키드로우 포토카드"),
            ("popup", "inside the heart Pop-up MD", "Pop-up MD Photocard", "팝업스토어 MD 포토카드"),
            ("popup", "IFC Mall Pop-up Store", "Pop-up Store Photocard", "팝업스토어 특전 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
            ("magazine", "Magazine / Press Benefit", "Magazine Photocard", "잡지/화보 특전 포토카드"),
        ],
    },
    {
        "title": "EPISODE 1: ZERO FRONTIER",
        "released_on": "2025-11-28",
        "sources": [
            ("concert", "World Tour VIP / Venue Benefit", "Tour Benefit Photocard", "월드투어 VIP/공연장 특전 포토카드"),
            ("popup", "World Tour Pop-up Store", "Pop-up Store Photocard", "월드투어 팝업스토어 포토카드"),
            ("popup", "Pop-up Purchase Benefit", "Purchase Benefit Photocard", "팝업 구매 금액대별 특전 포토카드"),
            ("merch", "Trading Card", "Trading Card", "트레이딩 카드"),
            ("merch", "Photocard Pack", "Photocard Pack", "포토카드 팩"),
            ("merch", "Photocard Holder Benefit", "Holder Benefit Photocard", "포토카드 홀더/MD 특전 포토카드"),
        ],
    },
    {
        "title": "Heavy Serenade",
        "released_on": "2026-05-11",
        "sources": [
            ("album", "Heavy / Serenade", "Album Photocard", "정규 앨범 랜덤 포토카드"),
            ("album", "Unit", "Unit Photocard", "유닛 포토카드"),
            ("album", "POCAALBUM", "POCAALBUM Photocard Set", "포카앨범 포토카드 세트"),
            ("album", "Melody Box", "Melody Box Photocard Set", "멜로디 박스 포토카드 세트"),
            ("preorder_benefit", "Pre-order Benefit", "POB Photocard", "예약판매 특전 포토카드"),
            ("lucky_draw", "Lucky Draw", "Lucky Draw Photocard", "럭키드로우 포토카드"),
            ("store_benefit", "Target / Barnes & Noble / Retail Exclusive", "Retail Exclusive Photocard", "해외/리테일러 독점 특전 포토카드"),
            ("fansign", "Fansign / Video Call", "Fansign Photocard", "팬사인회/영상통화 특전 포토카드"),
            ("broadcast", "Music Broadcast", "Broadcast Photocard", "음악방송 참여 특전 포토카드"),
            ("popup", "Heavy Serenade Pop-up Store", "Pop-up Store Photocard", "팝업스토어 포토카드"),
            ("merch", "Official MD / Trading Card", "Official MD Photocard", "공식 MD/트레이딩 카드"),
        ],
    },
]

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


def sync_nmixx_members(db: Session, group: Group) -> dict[str, Member]:
    members: dict[str, Member] = {}
    for korean_name, english_name in NMIXX_MEMBERS:
        member = db.scalar(
            select(Member).where(
                Member.group_id == group.id,
                (Member.name == korean_name) | (Member.name == english_name) | (Member.stage_name == english_name),
            )
        )
        if member is None:
            member = Member(group_id=group.id, name=korean_name, stage_name=english_name)
            db.add(member)
            db.flush()
        else:
            member.name = korean_name
            member.stage_name = english_name
        members[korean_name] = member
    return members


def get_or_create_release(db: Session, group: Group, source: dict, source_type: str, detail: str | None) -> Release:
    detail_filter = Release.detail == detail if detail is not None else Release.detail.is_(None)
    release = db.scalar(
        select(Release).where(
            Release.group_id == group.id,
            Release.title == source["title"],
            Release.source_type == source_type,
            Release.retailer_or_event.is_(None),
            Release.venue.is_(None),
            Release.country == "KR",
            Release.round.is_(None),
            detail_filter,
            Release.start_date.is_(None),
            Release.end_date.is_(None),
        )
    )
    if release is None:
        release = Release(
            group_id=group.id,
            title=source["title"],
            source_type=source_type,
            release_type=source_type,
            country="KR",
            detail=detail,
            released_on=date.fromisoformat(source["released_on"]),
            notes="Seeded NMIXX text metadata only; no copyrighted image is stored.",
        )
        db.add(release)
        db.flush()
    else:
        release.source_type = source_type
        release.release_type = source_type
        release.country = release.country or "KR"
        release.detail = detail
        release.released_on = release.released_on or date.fromisoformat(source["released_on"])
        release.notes = release.notes or "Seeded NMIXX text metadata only; no copyrighted image is stored."
    return release


def sync_nmixx_catalog(db: Session) -> None:
    group = get_or_create(db, Group, name="NMIXX", defaults={"slug": "nmixx"})
    group.slug = "nmixx"
    members = sync_nmixx_members(db, group)
    release_dates = {source["title"]: date.fromisoformat(source["released_on"]) for source in NMIXX_RELEASE_SOURCES}

    for source in NMIXX_RELEASE_SOURCES:
        for source_type, detail, card_name, card_notes in source["sources"]:
            release = get_or_create_release(db, group, source, source_type, detail)
            for korean_name, member in members.items():
                card = db.scalar(
                    select(Photocard).where(
                        Photocard.group_id == group.id,
                        Photocard.member_id == member.id,
                        Photocard.release_id == release.id,
                        Photocard.name == card_name,
                        Photocard.version == korean_name,
                    )
                )
                if card is None:
                    db.add(
                        Photocard(
                            group_id=group.id,
                            member_id=member.id,
                            release_id=release.id,
                            name=card_name,
                            version=korean_name,
                            notes=card_notes,
                        )
                    )
                else:
                    card.notes = card_notes

    for release in db.scalars(select(Release).where(Release.group_id == group.id)).all():
        if release.title in release_dates and release.released_on is None:
            release.released_on = release_dates[release.title]


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

    sync_nmixx_catalog(db)

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed_default_data(db)


if __name__ == "__main__":
    main()
