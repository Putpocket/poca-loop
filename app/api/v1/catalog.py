from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.api.errors import commit_or_409, conflict
from app.db.session import get_db
from app.models.catalog import Group, Member, PendingPhotocard, Photocard, Release
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
    PendingPhotocardCreate,
    PendingPhotocardRead,
    ReleaseCreate,
    ReleaseRead,
    ReleaseUpdate,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])
ModelT = TypeVar("ModelT")
RELEASE_IDENTITY_FIELDS = (
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
)


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


def nullable_eq(column: object, value: object | None) -> ColumnElement[bool]:
    if value is None:
        return column.is_(None)  # type: ignore[attr-defined]
    return column == value  # type: ignore[no-any-return]


def release_identity_query(values: dict[str, object | None], exclude_id: int | None = None):
    checks = [nullable_eq(getattr(Release, field), values[field]) for field in RELEASE_IDENTITY_FIELDS]
    query = select(Release).where(*checks)
    if exclude_id is not None:
        query = query.where(Release.id != exclude_id)
    return query


def release_payload_data(payload: BaseModel, *, exclude_unset: bool = False) -> dict[str, object | None]:
    data = payload.model_dump(exclude_unset=exclude_unset)
    if data.get("source_type") is None and data.get("release_type") is not None:
        data["source_type"] = data["release_type"]
    if data.get("release_type") is None and data.get("source_type") is not None:
        data["release_type"] = data["source_type"]
    return data


def delete_item(db: Session, item: object) -> None:
    db.delete(item)
    db.commit()


AdminDep = Annotated[User, Depends(get_current_admin)]
UserDep = Annotated[User, Depends(get_current_user)]
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
    data = release_payload_data(payload)
    identity = {field: data[field] for field in RELEASE_IDENTITY_FIELDS}
    if db.scalar(release_identity_query(identity)):
        raise conflict("Release already exists in this group")
    item = Release(**data)
    db.add(item)
    commit_or_409(db, "Release already exists in this group", item)
    return item


@router.patch("/releases/{item_id}", response_model=ReleaseRead)
def releases_update(item_id: int, payload: ReleaseUpdate, db: DbDep, _admin: AdminDep) -> Release:
    item = get_item_or_404(db, Release, item_id)
    data = release_payload_data(payload, exclude_unset=True)
    if "source_type" not in payload.model_fields_set and "release_type" in payload.model_fields_set:
        data["source_type"] = data["release_type"]
    if "release_type" not in payload.model_fields_set and "source_type" in payload.model_fields_set:
        data["release_type"] = data["source_type"]
    current = {field: getattr(item, field) for field in RELEASE_IDENTITY_FIELDS}
    changed_fields = payload.model_fields_set | set(data)
    for field in RELEASE_IDENTITY_FIELDS:
        if field in changed_fields or field in ({"source_type", "release_type"} & changed_fields):
            current[field] = data.get(field)
    if db.scalar(release_identity_query(current, exclude_id=item_id)):
        raise conflict("Release already exists in this group")
    for field, value in data.items():
        setattr(item, field, value)
    commit_or_409(db, "Release already exists in this group", item)
    return item


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


@router.post(
    "/pending-photocards",
    response_model=PendingPhotocardRead,
    status_code=status.HTTP_201_CREATED,
)
def pending_photocards_create(
    payload: PendingPhotocardCreate, db: DbDep, current_user: UserDep
) -> PendingPhotocard:
    if payload.group_id is not None:
        get_item_or_404(db, Group, payload.group_id)
    if payload.member_id is not None:
        member = get_item_or_404(db, Member, payload.member_id)
        if payload.group_id is not None and member.group_id != payload.group_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member is not in group")
    item = PendingPhotocard(
        created_by_user_id=current_user.id,
        catalog_status="pending",
        **payload.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


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
