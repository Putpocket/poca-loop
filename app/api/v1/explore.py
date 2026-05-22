from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.catalog import Photocard, Release
from app.models.user_card import UserHave, UserWant
from app.models.users import User
from app.schemas.explore import ExploreCardRead

router = APIRouter(prefix="/explore", tags=["explore"])
DbDep = Annotated[Session, Depends(get_db)]
UserDep = Annotated[User, Depends(get_current_user)]


def have_options():
    return (
        selectinload(UserHave.user),
        selectinload(UserHave.photocard).selectinload(Photocard.group),
        selectinload(UserHave.photocard).selectinload(Photocard.member),
        selectinload(UserHave.photocard).selectinload(Photocard.release),
        selectinload(UserHave.condition_grade),
    )


def want_options():
    return (
        selectinload(UserWant.user),
        selectinload(UserWant.photocard).selectinload(Photocard.group),
        selectinload(UserWant.photocard).selectinload(Photocard.member),
        selectinload(UserWant.photocard).selectinload(Photocard.release),
        selectinload(UserWant.minimum_condition_grade),
    )


def apply_photocard_filters(
    query,
    group_id: int | None,
    member_id: int | None,
    release_id: int | None,
    photocard_id: int | None,
    source_type: str | None,
):
    if group_id is not None:
        query = query.where(Photocard.group_id == group_id)
    if member_id is not None:
        query = query.where(Photocard.member_id == member_id)
    if release_id is not None:
        query = query.where(Photocard.release_id == release_id)
    if photocard_id is not None:
        query = query.where(Photocard.id == photocard_id)
    if source_type is not None:
        query = query.where(Release.source_type == source_type)
    return query


def serialize_have(item: UserHave) -> ExploreCardRead:
    return ExploreCardRead(
        entry_type="have",
        username=item.user.username,
        group=item.photocard.group,
        member=item.photocard.member,
        release_source=item.photocard.release,
        photocard=item.photocard,
        condition_grade=item.condition_grade,
        minimum_condition_grade=None,
        created_at=item.created_at,
    )


def serialize_want(item: UserWant) -> ExploreCardRead:
    return ExploreCardRead(
        entry_type="want",
        username=item.user.username,
        group=item.photocard.group,
        member=item.photocard.member,
        release_source=item.photocard.release,
        photocard=item.photocard,
        condition_grade=None,
        minimum_condition_grade=item.minimum_condition_grade,
        created_at=item.created_at,
    )


@router.get("/cards", response_model=list[ExploreCardRead])
def explore_cards(
    db: DbDep,
    _current_user: UserDep,
    entry_type: Literal["have", "want"] | None = None,
    group_id: int | None = None,
    member_id: int | None = None,
    release_id: int | None = None,
    photocard_id: int | None = None,
    source_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ExploreCardRead]:
    results: list[ExploreCardRead] = []

    if entry_type in (None, "have"):
        have_query = (
            select(UserHave)
            .join(UserHave.photocard)
            .outerjoin(Photocard.release)
            .options(*have_options())
            .where(UserHave.photocard_id.is_not(None), UserHave.pending_photocard_id.is_(None))
            .order_by(UserHave.created_at.desc(), UserHave.id.desc())
            .limit(limit)
        )
        have_query = apply_photocard_filters(
            have_query, group_id, member_id, release_id, photocard_id, source_type
        )
        results.extend(serialize_have(item) for item in db.scalars(have_query).all())

    if entry_type in (None, "want"):
        want_query = (
            select(UserWant)
            .join(UserWant.photocard)
            .outerjoin(Photocard.release)
            .options(*want_options())
            .where(UserWant.photocard_id.is_not(None), UserWant.pending_photocard_id.is_(None))
            .order_by(UserWant.created_at.desc(), UserWant.id.desc())
            .limit(limit)
        )
        want_query = apply_photocard_filters(
            want_query, group_id, member_id, release_id, photocard_id, source_type
        )
        results.extend(serialize_want(item) for item in db.scalars(want_query).all())

    results.sort(key=lambda item: item.created_at, reverse=True)
    return results[:limit]
