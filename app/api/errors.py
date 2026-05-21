from collections.abc import Callable
from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

T = TypeVar("T")


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def commit_or_409(db: Session, detail: str, refresh: T | None = None) -> T | None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict(detail) from None
    if refresh is not None:
        db.refresh(refresh)
    return refresh


def ensure_unique(db: Session, exists_query: Callable[[], object | None], detail: str) -> None:
    if exists_query() is not None:
        raise conflict(detail)
