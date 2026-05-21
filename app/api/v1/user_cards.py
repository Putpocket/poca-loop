from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.errors import commit_or_409, conflict
from app.db.session import get_db
from app.models.catalog import PendingPhotocard, Photocard
from app.models.user_card import ConditionGrade, UserHave, UserWant
from app.models.users import User
from app.schemas.catalog import PendingPhotocardRead
from app.schemas.user_card import HaveCreate, HaveRead, HaveUpdate, WantCreate, WantRead, WantUpdate

router = APIRouter(prefix="/me/cards", tags=["user-cards"])
pending_router = APIRouter(prefix="/me/pending-photocards", tags=["pending-photocards"])
DbDep = Annotated[Session, Depends(get_db)]
UserDep = Annotated[User, Depends(get_current_user)]


def ensure_exists(db: Session, model: type, item_id: int) -> None:
    if db.get(model, item_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced item not found")


def ensure_pending_owned(db: Session, current_user: User, item_id: int) -> None:
    if (
        db.scalar(
            select(PendingPhotocard).where(
                PendingPhotocard.id == item_id,
                PendingPhotocard.created_by_user_id == current_user.id,
            )
        )
        is None
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced item not found")


def card_identity(payload, current_item=None) -> tuple[int | None, int | None]:
    if getattr(payload, "photocard_id", None) is not None:
        return payload.photocard_id, None
    if getattr(payload, "pending_photocard_id", None) is not None:
        return None, payload.pending_photocard_id
    if current_item is not None:
        return current_item.photocard_id, current_item.pending_photocard_id
    return None, None


def ensure_card_ref_exists(
    db: Session,
    current_user: User,
    photocard_id: int | None,
    pending_photocard_id: int | None,
) -> None:
    if photocard_id is not None:
        ensure_exists(db, Photocard, photocard_id)
    if pending_photocard_id is not None:
        ensure_pending_owned(db, current_user, pending_photocard_id)


def have_options():
    return (
        selectinload(UserHave.photocard).selectinload(Photocard.release),
        selectinload(UserHave.pending_photocard),
        selectinload(UserHave.condition_grade),
    )


def want_options():
    return (
        selectinload(UserWant.photocard).selectinload(Photocard.release),
        selectinload(UserWant.pending_photocard),
        selectinload(UserWant.minimum_condition_grade),
    )


def get_user_have_or_404(db: Session, current_user: User, item_id: int) -> UserHave:
    item = db.scalar(
        select(UserHave)
        .options(*have_options())
        .where(UserHave.id == item_id, UserHave.user_id == current_user.id)
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


def get_user_want_or_404(db: Session, current_user: User, item_id: int) -> UserWant:
    item = db.scalar(
        select(UserWant)
        .options(*want_options())
        .where(UserWant.id == item_id, UserWant.user_id == current_user.id)
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.post("/haves", response_model=HaveRead, status_code=status.HTTP_201_CREATED)
def create_have(payload: HaveCreate, db: DbDep, current_user: UserDep) -> UserHave:
    photocard_id, pending_photocard_id = card_identity(payload)
    ensure_card_ref_exists(db, current_user, photocard_id, pending_photocard_id)
    ensure_exists(db, ConditionGrade, payload.condition_grade_id)
    if db.scalar(
        select(UserHave).where(
            UserHave.user_id == current_user.id,
            UserHave.photocard_id == photocard_id,
            UserHave.pending_photocard_id == pending_photocard_id,
            UserHave.condition_grade_id == payload.condition_grade_id,
        )
    ):
        raise conflict("Have card already registered")
    have = UserHave(user_id=current_user.id, **payload.model_dump())
    db.add(have)
    commit_or_409(db, "Have card already registered", have)
    return db.scalar(
        select(UserHave)
        .options(*have_options())
        .where(UserHave.id == have.id)
    )


@router.get("/haves", response_model=list[HaveRead])
def list_haves(db: DbDep, current_user: UserDep) -> list[UserHave]:
    return list(
        db.scalars(
            select(UserHave)
            .options(*have_options())
            .where(UserHave.user_id == current_user.id)
            .order_by(UserHave.id)
        ).all()
    )


@router.patch("/haves/{item_id}", response_model=HaveRead)
def update_have(item_id: int, payload: HaveUpdate, db: DbDep, current_user: UserDep) -> UserHave:
    have = get_user_have_or_404(db, current_user, item_id)
    photocard_id, pending_photocard_id = card_identity(payload, have)
    condition_grade_id = (
        payload.condition_grade_id if payload.condition_grade_id is not None else have.condition_grade_id
    )
    ensure_card_ref_exists(db, current_user, photocard_id, pending_photocard_id)
    ensure_exists(db, ConditionGrade, condition_grade_id)
    if db.scalar(
        select(UserHave).where(
            UserHave.id != item_id,
            UserHave.user_id == current_user.id,
            UserHave.photocard_id == photocard_id,
            UserHave.pending_photocard_id == pending_photocard_id,
            UserHave.condition_grade_id == condition_grade_id,
        )
    ):
        raise conflict("Have card already registered")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(have, field, value)
    if "photocard_id" in payload.model_fields_set:
        have.pending_photocard_id = None
    if "pending_photocard_id" in payload.model_fields_set:
        have.photocard_id = None
    commit_or_409(db, "Have card already registered", have)
    return get_user_have_or_404(db, current_user, item_id)


@router.delete("/haves/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_have(item_id: int, db: DbDep, current_user: UserDep) -> None:
    have = get_user_have_or_404(db, current_user, item_id)
    # TODO: Switch to soft delete if matching history or audit trails are introduced.
    db.delete(have)
    db.commit()


@router.post("/wants", response_model=WantRead, status_code=status.HTTP_201_CREATED)
def create_want(payload: WantCreate, db: DbDep, current_user: UserDep) -> UserWant:
    photocard_id, pending_photocard_id = card_identity(payload)
    ensure_card_ref_exists(db, current_user, photocard_id, pending_photocard_id)
    if payload.minimum_condition_grade_id is not None:
        ensure_exists(db, ConditionGrade, payload.minimum_condition_grade_id)
    if db.scalar(
        select(UserWant).where(
            UserWant.user_id == current_user.id,
            UserWant.photocard_id == photocard_id,
            UserWant.pending_photocard_id == pending_photocard_id,
        )
    ):
        raise conflict("Want card already registered")
    want = UserWant(user_id=current_user.id, **payload.model_dump())
    db.add(want)
    commit_or_409(db, "Want card already registered", want)
    return db.scalar(
        select(UserWant)
        .options(*want_options())
        .where(UserWant.id == want.id)
    )


@router.get("/wants", response_model=list[WantRead])
def list_wants(db: DbDep, current_user: UserDep) -> list[UserWant]:
    return list(
        db.scalars(
            select(UserWant)
            .options(*want_options())
            .where(UserWant.user_id == current_user.id)
            .order_by(UserWant.id)
        ).all()
    )


@router.patch("/wants/{item_id}", response_model=WantRead)
def update_want(item_id: int, payload: WantUpdate, db: DbDep, current_user: UserDep) -> UserWant:
    want = get_user_want_or_404(db, current_user, item_id)
    photocard_id, pending_photocard_id = card_identity(payload, want)
    ensure_card_ref_exists(db, current_user, photocard_id, pending_photocard_id)
    if payload.minimum_condition_grade_id is not None:
        ensure_exists(db, ConditionGrade, payload.minimum_condition_grade_id)
    if db.scalar(
        select(UserWant).where(
            UserWant.id != item_id,
            UserWant.user_id == current_user.id,
            UserWant.photocard_id == photocard_id,
            UserWant.pending_photocard_id == pending_photocard_id,
        )
    ):
        raise conflict("Want card already registered")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(want, field, value)
    if "photocard_id" in payload.model_fields_set:
        want.pending_photocard_id = None
    if "pending_photocard_id" in payload.model_fields_set:
        want.photocard_id = None
    commit_or_409(db, "Want card already registered", want)
    return get_user_want_or_404(db, current_user, item_id)


@router.delete("/wants/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_want(item_id: int, db: DbDep, current_user: UserDep) -> None:
    want = get_user_want_or_404(db, current_user, item_id)
    # TODO: Switch to soft delete if matching history or audit trails are introduced.
    db.delete(want)
    db.commit()


@pending_router.get("", response_model=list[PendingPhotocardRead])
def list_my_pending_photocards(db: DbDep, current_user: UserDep) -> list[PendingPhotocard]:
    return list(
        db.scalars(
            select(PendingPhotocard)
            .where(PendingPhotocard.created_by_user_id == current_user.id)
            .order_by(PendingPhotocard.id)
        ).all()
    )
