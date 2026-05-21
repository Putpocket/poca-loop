from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.catalog import PendingPhotocard
from app.models.users import User
from app.schemas.catalog import PendingPhotocardRead

router = APIRouter(prefix="/admin", tags=["admin"])
DbDep = Annotated[Session, Depends(get_db)]
AdminDep = Annotated[User, Depends(get_current_admin)]


@router.get("/pending-photocards", response_model=list[PendingPhotocardRead])
def pending_photocards_review_list(
    db: DbDep,
    _admin: AdminDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    catalog_status: Literal["pending"] | None = None,
) -> list[PendingPhotocard]:
    query = select(PendingPhotocard).order_by(PendingPhotocard.created_at.desc(), PendingPhotocard.id.desc())
    if catalog_status is not None:
        query = query.where(PendingPhotocard.catalog_status == catalog_status)
    return list(db.scalars(query.limit(limit)).all())
