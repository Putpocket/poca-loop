from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.catalog import PendingPhotocard
from app.models.users import User
from app.schemas.catalog import PendingPhotocardRead

router = APIRouter(prefix="/admin", tags=["admin"])
DbDep = Annotated[Session, Depends(get_db)]
AdminDep = Annotated[User, Depends(get_current_admin)]


class PendingPhotocardRejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


@router.get("/pending-photocards", response_model=list[PendingPhotocardRead])
def pending_photocards_review_list(
    db: DbDep,
    _admin: AdminDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    catalog_status: Literal["pending", "rejected"] | None = None,
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
