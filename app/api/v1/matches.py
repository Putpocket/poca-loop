from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.users import User
from app.schemas.matching import DirectMatchRead, ThreeWayMatchRead
from app.services.matching import get_direct_matches, get_three_way_matches

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/direct", response_model=list[DirectMatchRead])
def direct_matches(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[DirectMatchRead]:
    return get_direct_matches(db, current_user, limit=limit)


@router.get("/three-way", response_model=list[ThreeWayMatchRead])
def three_way_matches(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ThreeWayMatchRead]:
    return get_three_way_matches(db, current_user, limit=limit)
