from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.errors import commit_or_409, conflict
from app.db.session import get_db
from app.models.catalog import Photocard
from app.models.user_card import ConditionGrade, UserHave, UserWant
from app.models.users import User
from app.schemas.user_card import HaveCreate, HaveRead, WantCreate, WantRead

router = APIRouter(prefix="/me/cards", tags=["user-cards"])
DbDep = Annotated[Session, Depends(get_db)]
UserDep = Annotated[User, Depends(get_current_user)]


def ensure_exists(db: Session, model: type, item_id: int) -> None:
    if db.get(model, item_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced item not found")


@router.post("/haves", response_model=HaveRead, status_code=status.HTTP_201_CREATED)
def create_have(payload: HaveCreate, db: DbDep, current_user: UserDep) -> UserHave:
    ensure_exists(db, Photocard, payload.photocard_id)
    ensure_exists(db, ConditionGrade, payload.condition_grade_id)
    if db.scalar(
        select(UserHave).where(
            UserHave.user_id == current_user.id,
            UserHave.photocard_id == payload.photocard_id,
            UserHave.condition_grade_id == payload.condition_grade_id,
        )
    ):
        raise conflict("Have card already registered")
    have = UserHave(user_id=current_user.id, **payload.model_dump())
    db.add(have)
    commit_or_409(db, "Have card already registered", have)
    return db.scalar(
        select(UserHave)
        .options(selectinload(UserHave.photocard), selectinload(UserHave.condition_grade))
        .where(UserHave.id == have.id)
    )


@router.get("/haves", response_model=list[HaveRead])
def list_haves(db: DbDep, current_user: UserDep) -> list[UserHave]:
    return list(
        db.scalars(
            select(UserHave)
            .options(selectinload(UserHave.photocard), selectinload(UserHave.condition_grade))
            .where(UserHave.user_id == current_user.id)
            .order_by(UserHave.id)
        ).all()
    )


@router.post("/wants", response_model=WantRead, status_code=status.HTTP_201_CREATED)
def create_want(payload: WantCreate, db: DbDep, current_user: UserDep) -> UserWant:
    ensure_exists(db, Photocard, payload.photocard_id)
    if payload.minimum_condition_grade_id is not None:
        ensure_exists(db, ConditionGrade, payload.minimum_condition_grade_id)
    if db.scalar(
        select(UserWant).where(
            UserWant.user_id == current_user.id,
            UserWant.photocard_id == payload.photocard_id,
        )
    ):
        raise conflict("Want card already registered")
    want = UserWant(user_id=current_user.id, **payload.model_dump())
    db.add(want)
    commit_or_409(db, "Want card already registered", want)
    return db.scalar(
        select(UserWant)
        .options(selectinload(UserWant.photocard), selectinload(UserWant.minimum_condition_grade))
        .where(UserWant.id == want.id)
    )


@router.get("/wants", response_model=list[WantRead])
def list_wants(db: DbDep, current_user: UserDep) -> list[UserWant]:
    return list(
        db.scalars(
            select(UserWant)
            .options(selectinload(UserWant.photocard), selectinload(UserWant.minimum_condition_grade))
            .where(UserWant.user_id == current_user.id)
            .order_by(UserWant.id)
        ).all()
    )
