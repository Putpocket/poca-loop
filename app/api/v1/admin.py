from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.api.deps import get_current_admin
from app.api.errors import conflict
from app.db.session import get_db
from app.models.catalog import Group, Member, PendingPhotocard, Photocard, Release
from app.models.user_card import UserHave, UserWant
from app.models.users import User
from app.schemas.catalog import PendingPhotocardRead

router = APIRouter(prefix="/admin", tags=["admin"])
DbDep = Annotated[Session, Depends(get_db)]
AdminDep = Annotated[User, Depends(get_current_admin)]


class PendingPhotocardRejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class PendingPhotocardApproveRequest(BaseModel):
    group_id: int
    member_id: int
    release_id: int | None = None
    name: str = Field(min_length=1, max_length=160)
    version: str | None = Field(default=None, max_length=120)
    external_url: AnyHttpUrl | None = None
    notes: str | None = Field(default=None, max_length=500)
    reason: str | None = Field(default=None, max_length=500)


class PendingPhotocardMergeRequest(BaseModel):
    photocard_id: int
    reason: str | None = Field(default=None, max_length=500)


@router.get("/pending-photocards", response_model=list[PendingPhotocardRead])
def pending_photocards_review_list(
    db: DbDep,
    _admin: AdminDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    catalog_status: Literal["pending", "rejected", "approved", "merged"] | None = None,
) -> list[PendingPhotocard]:
    query = select(PendingPhotocard).order_by(PendingPhotocard.created_at.desc(), PendingPhotocard.id.desc())
    if catalog_status is not None:
        query = query.where(PendingPhotocard.catalog_status == catalog_status)
    return list(db.scalars(query.limit(limit)).all())


@router.post("/pending-photocards/{item_id}/reject", response_model=PendingPhotocardRead)
def pending_photocards_reject(
    item_id: int,
    payload: PendingPhotocardRejectRequest,
    db: DbDep,
    admin: AdminDep,
) -> PendingPhotocard:
    item = db.get(PendingPhotocard, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    item.catalog_status = "rejected"
    item.reviewed_by_admin_id = admin.id
    item.reviewed_at = db.scalar(select(func.now()))
    item.review_reason = payload.reason
    db.commit()
    db.refresh(item)
    return item


def ensure_approval_catalog_refs(db: Session, payload: PendingPhotocardApproveRequest) -> None:
    group = db.get(Group, payload.group_id)
    member = db.get(Member, payload.member_id)
    release = db.get(Release, payload.release_id) if payload.release_id is not None else None
    if group is None or member is None or (payload.release_id is not None and release is None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced catalog item not found")
    if member.group_id != payload.group_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member does not belong to group")
    if release is not None and release.group_id != payload.group_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Release does not belong to group")


def transfer_pending_card_references(db: Session, pending_id: int, photocard_id: int) -> None:
    haves = list(db.scalars(select(UserHave).where(UserHave.pending_photocard_id == pending_id)).all())
    for have in haves:
        duplicate = db.scalar(
            select(UserHave).where(
                UserHave.id != have.id,
                UserHave.user_id == have.user_id,
                UserHave.photocard_id == photocard_id,
                UserHave.condition_grade_id == have.condition_grade_id,
            )
        )
        if duplicate is not None:
            db.delete(have)
        else:
            have.photocard_id = photocard_id
            have.pending_photocard_id = None

    wants = list(db.scalars(select(UserWant).where(UserWant.pending_photocard_id == pending_id)).all())
    for want in wants:
        duplicate = db.scalar(
            select(UserWant).where(
                UserWant.id != want.id,
                UserWant.user_id == want.user_id,
                UserWant.photocard_id == photocard_id,
            )
        )
        if duplicate is not None:
            db.delete(want)
        else:
            want.photocard_id = photocard_id
            want.pending_photocard_id = None


@router.post("/pending-photocards/{item_id}/approve", response_model=PendingPhotocardRead)
def pending_photocards_approve(
    item_id: int,
    payload: PendingPhotocardApproveRequest,
    db: DbDep,
    admin: AdminDep,
) -> PendingPhotocard:
    item = db.get(PendingPhotocard, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if item.catalog_status == "rejected":
        raise conflict("Rejected pending photocard cannot be approved")
    if item.catalog_status == "merged":
        raise conflict("Merged pending photocard cannot be approved")
    if item.catalog_status == "approved":
        return item

    try:
        ensure_approval_catalog_refs(db, payload)
        external_url = str(payload.external_url) if payload.external_url is not None else None
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

        photocard = Photocard(
            group_id=payload.group_id,
            member_id=payload.member_id,
            release_id=payload.release_id,
            name=payload.name,
            version=payload.version,
            external_url=external_url,
            notes=payload.notes,
        )
        db.add(photocard)
        db.flush()

        transfer_pending_card_references(db, item.id, photocard.id)
        item.catalog_status = "approved"
        item.approved_photocard_id = photocard.id
        item.reviewed_by_admin_id = admin.id
        item.reviewed_at = db.scalar(select(func.now()))
        item.review_reason = payload.reason
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise conflict("Photocard already exists") from None
    except Exception:
        db.rollback()
        raise
    db.refresh(item)
    return item


@router.post("/pending-photocards/{item_id}/merge", response_model=PendingPhotocardRead)
def pending_photocards_merge(
    item_id: int,
    payload: PendingPhotocardMergeRequest,
    db: DbDep,
    admin: AdminDep,
) -> PendingPhotocard:
    item = db.get(PendingPhotocard, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if item.catalog_status == "rejected":
        raise conflict("Rejected pending photocard cannot be merged")
    if item.catalog_status == "approved":
        raise conflict("Approved pending photocard cannot be merged")
    if item.catalog_status == "merged":
        return item

    photocard = db.get(Photocard, payload.photocard_id)
    if photocard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target photocard not found")

    try:
        transfer_pending_card_references(db, item.id, photocard.id)
        item.catalog_status = "merged"
        item.merged_photocard_id = photocard.id
        item.reviewed_by_admin_id = admin.id
        item.reviewed_at = db.scalar(select(func.now()))
        item.review_reason = payload.reason
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise conflict("Pending photocard merge created duplicate user cards") from None
    except Exception:
        db.rollback()
        raise
    db.refresh(item)
    return item
