from pydantic import BaseModel, Field

from app.schemas.catalog import ConditionGradeRead, PhotocardRead
from app.schemas.common import OrmModel


class HaveCreate(BaseModel):
    photocard_id: int
    condition_grade_id: int
    note: str | None = Field(default=None, max_length=500)


class HaveUpdate(BaseModel):
    photocard_id: int | None = None
    condition_grade_id: int | None = None
    note: str | None = Field(default=None, max_length=500)


class HaveRead(OrmModel):
    id: int
    photocard_id: int
    condition_grade_id: int
    note: str | None
    photocard: PhotocardRead
    condition_grade: ConditionGradeRead


class WantCreate(BaseModel):
    photocard_id: int
    minimum_condition_grade_id: int | None = None
    note: str | None = Field(default=None, max_length=500)


class WantUpdate(BaseModel):
    photocard_id: int | None = None
    minimum_condition_grade_id: int | None = None
    note: str | None = Field(default=None, max_length=500)


class WantRead(OrmModel):
    id: int
    photocard_id: int
    minimum_condition_grade_id: int | None
    note: str | None
    photocard: PhotocardRead
    minimum_condition_grade: ConditionGradeRead | None
