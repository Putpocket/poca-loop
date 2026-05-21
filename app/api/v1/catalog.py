from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.errors import commit_or_409, conflict
from app.db.session import get_db
from app.models.catalog import Group, Member, Photocard, Release
from app.models.user_card import ConditionGrade
from app.models.users import User
from app.schemas.catalog import (
    ConditionGradeCreate,
    ConditionGradeRead,
    ConditionGradeUpdate,
    GroupCreate,
    GroupRead,
    GroupUpdate,
    MemberCreate,
    MemberRead,
    MemberUpdate,
    PhotocardCreate,
    PhotocardRead,
    PhotocardUpdate,
    ReleaseCreate,
    ReleaseRead,
    ReleaseUpdate,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])
ModelT = TypeVar("ModelT")


def list_items(db: Session, model: type[ModelT]) -> list[ModelT]:
    return list(db.scalars(select(model).order_by(model.id)).all())


def get_item_or_404(db: Session, model: type[ModelT], item_id: int) -> ModelT:
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


def update_item(db: Session, item: object, payload: BaseModel) -> object:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None and field == "external_url":
            value = str(value)
        setattr(item, field, value)
    commit_or_409(db, "Catalog item already exists", item)
    return item


def create_item(db: Session, model: type[ModelT], payload: BaseModel) -> ModelT:
    data = payload.model_dump()
    if "external_url" in data and data["external_url"] is not None:
        data["external_url"] = str(data["external_url"])
    item = model(**data)
    db.add(item)
    commit_or_409(db, "Catalog item already exists", item)
    return item


def delete_item(db: Session, item: object) -> None:
    db.delete(item)
    db.commit()


AdminDep = Annotated[User, Depends(get_current_admin)]
DbDep = Annotated[Session, Depends(get_db)]


@router.get("/groups", response_model=list[GroupRead])
def groups_list(db: DbDep) -> list[Group]:
    return list_items(db, Group)


@router.post("/groups", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def groups_create(payload: GroupCreate, db: DbDep, _admin: AdminDep) -> Group:
    if db.scalar(select(Group).where((Group.name == payload.name) | (Group.slug == payload.slug))):
        raise conflict("Group already exists")
    return create_item(db, Group, payload)


@router.patch("/groups/{item_id}", response_model=GroupRead)
def groups_update(item_id: int, payload: GroupUpdate, db: DbDep, _admin: AdminDep) -> Group:
    item = get_item_or_404(db, Group, item_id)
    checks = []
    if payload.name:
        checks.append(Group.name == payload.name)
    if payload.slug:
        checks.append(Group.slug == payload.slug)
    if checks:
        duplicate = db.scalar(select(Group).where(Group.id != item_id, checks[0] if len(checks) == 1 else checks[0] | checks[1]))
        if duplicate:
            raise conflict("Group already exists")
    return update_item(db, item, payload)


@router.delete("/groups/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def groups_delete(item_id: int, db: DbDep, _admin: AdminDep) -> None:
    delete_item(db, get_item_or_404(db, Group, item_id))


@router.get("/members", response_model=list[MemberRead])
def members_list(db: DbDep) -> list[Member]:
    return list_items(db, Member)


@router.post("/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def members_create(payload: MemberCreate, db: DbDep, _admin: AdminDep) -> Member:
    if db.scalar(select(Member).where(Member.group_id == payload.group_id, Member.name == payload.name)):
        raise conflict("Member already exists in this group")
    return create_item(db, Member, payload)


@router.patch("/members/{item_id}", response_model=MemberRead)
def members_update(item_id: int, payload: MemberUpdate, db: DbDep, _admin: AdminDep) -> Member:
    item = get_item_or_404(db, Member, item_id)
    group_id = payload.group_id if payload.group_id is not None else item.group_id
    name = payload.name if payload.name is not None else item.name
    if db.scalar(select(Member).where(Member.id != item_id, Member.group_id == group_id, Member.name == name)):
        raise conflict("Member already exists in this group")
    return update_item(db, item, payload)


@router.delete("/members/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def members_delete(item_id: int, db: DbDep, _admin: AdminDep) -> None:
    delete_item(db, get_item_or_404(db, Member, item_id))


@router.get("/releases", response_model=list[ReleaseRead])
def releases_list(db: DbDep) -> list[Release]:
    return list_items(db, Release)


@router.post("/releases", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
def releases_create(payload: ReleaseCreate, db: DbDep, _admin: AdminDep) -> Release:
    if db.scalar(
        select(Release).where(Release.group_id == payload.group_id, Release.title == payload.title)
    ):
        raise conflict("Release already exists in this group")
    return create_item(db, Release, payload)


@router.patch("/releases/{item_id}", response_model=ReleaseRead)
def releases_update(item_id: int, payload: ReleaseUpdate, db: DbDep, _admin: AdminDep) -> Release:
    item = get_item_or_404(db, Release, item_id)
    group_id = payload.group_id if payload.group_id is not None else item.group_id
    title = payload.title if payload.title is not None else item.title
    if db.scalar(
        select(Release).where(Release.id != item_id, Release.group_id == group_id, Release.title == title)
    ):
        raise conflict("Release already exists in this group")
    return update_item(db, item, payload)


@router.delete("/releases/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def releases_delete(item_id: int, db: DbDep, _admin: AdminDep) -> None:
    delete_item(db, get_item_or_404(db, Release, item_id))


@router.get("/photocards", response_model=list[PhotocardRead])
def photocards_list(db: DbDep) -> list[Photocard]:
    return list_items(db, Photocard)


@router.post("/photocards", response_model=PhotocardRead, status_code=status.HTTP_201_CREATED)
def photocards_create(payload: PhotocardCreate, db: DbDep, _admin: AdminDep) -> Photocard:
    if db.scalar(
        select(Photocard).where(
            Photocard.group_id == payload.group_id,
            Photocard.member_id == payload.member_id,
            Photocard.release_id == payload.release_id,
            Photocard.name == payload.name,
            Photocard.version == payload.version,
        )
    ):
        raise conflict("Photocard already exists")
    return create_item(db, Photocard, payload)


@router.patch("/photocards/{item_id}", response_model=PhotocardRead)
def photocards_update(
    item_id: int, payload: PhotocardUpdate, db: DbDep, _admin: AdminDep
) -> Photocard:
    item = get_item_or_404(db, Photocard, item_id)
    group_id = payload.group_id if payload.group_id is not None else item.group_id
    member_id = payload.member_id if payload.member_id is not None else item.member_id
    release_id = payload.release_id if payload.release_id is not None else item.release_id
    name = payload.name if payload.name is not None else item.name
    version = payload.version if payload.version is not None else item.version
    if db.scalar(
        select(Photocard).where(
            Photocard.id != item_id,
            Photocard.group_id == group_id,
            Photocard.member_id == member_id,
            Photocard.release_id == release_id,
            Photocard.name == name,
            Photocard.version == version,
        )
    ):
        raise conflict("Photocard already exists")
    return update_item(db, item, payload)


@router.delete("/photocards/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def photocards_delete(item_id: int, db: DbDep, _admin: AdminDep) -> None:
    delete_item(db, get_item_or_404(db, Photocard, item_id))


@router.get("/condition-grades", response_model=list[ConditionGradeRead])
def condition_grades_list(db: DbDep) -> list[ConditionGrade]:
    return list(db.scalars(select(ConditionGrade).order_by(ConditionGrade.sort_order)).all())


@router.post(
    "/condition-grades", response_model=ConditionGradeRead, status_code=status.HTTP_201_CREATED
)
def condition_grades_create(
    payload: ConditionGradeCreate, db: DbDep, _admin: AdminDep
) -> ConditionGrade:
    if db.scalar(select(ConditionGrade).where(ConditionGrade.code == payload.code)):
        raise conflict("Condition grade already exists")
    return create_item(db, ConditionGrade, payload)


@router.patch("/condition-grades/{item_id}", response_model=ConditionGradeRead)
def condition_grades_update(
    item_id: int, payload: ConditionGradeUpdate, db: DbDep, _admin: AdminDep
) -> ConditionGrade:
    return update_item(db, get_item_or_404(db, ConditionGrade, item_id), payload)


@router.delete("/condition-grades/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def condition_grades_delete(item_id: int, db: DbDep, _admin: AdminDep) -> None:
    delete_item(db, get_item_or_404(db, ConditionGrade, item_id))
