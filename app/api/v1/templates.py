from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.users import User
from app.services.template_svg import render_svg_checklist

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/me.svg")
def my_svg_template(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    svg = render_svg_checklist(db, current_user)
    return Response(
        content=svg,
        media_type="image/svg+xml; charset=utf-8",
        headers={"Cache-Control": "private, no-store"},
    )
