from html import escape

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Photocard
from app.models.user_card import UserHave, UserWant
from app.models.users import User

MAX_HAVES = 50
MAX_WANTS = 50
ROW_HEIGHT = 26
SECTION_GAP = 42
WIDTH = 980
MARGIN = 32


def safe_text(value: object | None) -> str:
    escaped = escape("" if value is None else str(value), quote=True)
    return escaped.replace("onload=", "onload&#61;").replace("onclick=", "onclick&#61;")


def photocard_label(card: Photocard) -> str:
    group = card.group.name if card.group else "Unknown group"
    member = card.member.name if card.member else "Unknown member"
    release = card.release.title if card.release else "No release"
    version = f" ({card.version})" if card.version else ""
    return f"{group} / {member} / {release} / {card.name}{version}"


def truncate_text(value: str, max_length: int = 130) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."


def load_user_cards(db: Session, user: User) -> tuple[list[UserHave], list[UserWant]]:
    haves = list(
        db.scalars(
            select(UserHave)
            .options(
                selectinload(UserHave.photocard).selectinload(Photocard.group),
                selectinload(UserHave.photocard).selectinload(Photocard.member),
                selectinload(UserHave.photocard).selectinload(Photocard.release),
                selectinload(UserHave.condition_grade),
            )
            .where(UserHave.user_id == user.id)
            .order_by(UserHave.id)
        ).all()
    )
    wants = list(
        db.scalars(
            select(UserWant)
            .options(
                selectinload(UserWant.photocard).selectinload(Photocard.group),
                selectinload(UserWant.photocard).selectinload(Photocard.member),
                selectinload(UserWant.photocard).selectinload(Photocard.release),
                selectinload(UserWant.minimum_condition_grade),
            )
            .where(UserWant.user_id == user.id)
            .order_by(UserWant.id)
        ).all()
    )
    return haves, wants


def render_row(y: int, label: str, meta: str) -> str:
    return (
        f'<rect x="{MARGIN}" y="{y - 15}" width="14" height="14" rx="2" '
        'fill="#ffffff" stroke="#475569" stroke-width="1.5"/>'
        f'<text x="{MARGIN + 24}" y="{y}" class="item">{safe_text(truncate_text(label))}</text>'
        f'<text x="{WIDTH - 210}" y="{y}" class="meta">{safe_text(meta)}</text>'
    )


def render_svg_checklist(db: Session, user: User) -> str:
    haves, wants = load_user_cards(db, user)
    shown_haves = haves[:MAX_HAVES]
    shown_wants = wants[:MAX_WANTS]
    have_more = len(haves) > MAX_HAVES
    want_more = len(wants) > MAX_WANTS

    have_rows = len(shown_haves) + (1 if have_more else 0)
    want_rows = len(shown_wants) + (1 if want_more else 0)
    height = 160 + (have_rows + want_rows) * ROW_HEIGHT + SECTION_GAP

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" aria-label="poca-loop checklist">',
        "<style>"
        "text{font-family:Arial,sans-serif;fill:#0f172a}"
        ".title{font-size:28px;font-weight:700}"
        ".subtitle{font-size:15px;fill:#475569}"
        ".section{font-size:17px;font-weight:700}"
        ".item{font-size:14px}"
        ".meta{font-size:13px;fill:#334155}"
        ".muted{font-size:14px;fill:#64748b}"
        "</style>",
        f'<rect x="0" y="0" width="{WIDTH}" height="{height}" fill="#f8fafc"/>',
        f'<rect x="18" y="18" width="{WIDTH - 36}" height="{height - 36}" rx="8" '
        'fill="#ffffff" stroke="#cbd5e1"/>',
        f'<text x="{MARGIN}" y="58" class="title">poca-loop</text>',
        f'<text x="{MARGIN}" y="86" class="subtitle">Checklist for @{safe_text(user.username)}</text>',
    ]

    y = 126
    parts.append(f'<text x="{MARGIN}" y="{y}" class="section">HAVE</text>')
    y += 28
    if shown_haves:
        for have in shown_haves:
            label = photocard_label(have.photocard)
            meta = f"grade {have.condition_grade.code}"
            if have.note:
                meta += f" / {have.note}"
            parts.append(render_row(y, label, meta))
            y += ROW_HEIGHT
    else:
        parts.append(f'<text x="{MARGIN}" y="{y}" class="muted">No have cards yet</text>')
        y += ROW_HEIGHT
    if have_more:
        parts.append(f'<text x="{MARGIN}" y="{y}" class="muted">and more...</text>')
        y += ROW_HEIGHT

    y += SECTION_GAP - 12
    parts.append(f'<text x="{MARGIN}" y="{y}" class="section">WANT</text>')
    y += 28
    if shown_wants:
        for want in shown_wants:
            label = photocard_label(want.photocard)
            minimum = want.minimum_condition_grade.code if want.minimum_condition_grade else "not specified"
            parts.append(render_row(y, label, f"min grade {minimum}"))
            y += ROW_HEIGHT
    else:
        parts.append(f'<text x="{MARGIN}" y="{y}" class="muted">No want cards yet</text>')
        y += ROW_HEIGHT
    if want_more:
        parts.append(f'<text x="{MARGIN}" y="{y}" class="muted">and more...</text>')

    parts.append("</svg>")
    return "".join(parts)
