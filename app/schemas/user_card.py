from pydantic import BaseModel, Field, model_validator

from app.schemas.catalog import ConditionGradeRead, PendingPhotocardRead, PhotocardRead
from app.schemas.common import OrmModel


class HaveCreate(BaseModel):
    photocard_id: int | None = None
    pending_photocard_id: int | None = None
    condition_grade_id: int
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_card_ref(self) -> "HaveCreate":
        if (self.photocard_id is None) == (self.pending_photocard_id is None):
            raise ValueError("Provide exactly one of photocard_id or pending_photocard_id")
        return self


class HaveUpdate(BaseModel):
    photocard_id: int | None = None
    pending_photocard_id: int | None = None
    condition_grade_id: int | None = None
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_card_ref(self) -> "HaveUpdate":
        if self.photocard_id is not None and self.pending_photocard_id is not None:
            raise ValueError("Provide only one of photocard_id or pending_photocard_id")
        return self


class HaveRead(OrmModel):
    id: int
    photocard_id: int | None
    pending_photocard_id: int | None
    condition_grade_id: int
    note: str | None
    photocard: PhotocardRead | None
    pending_photocard: PendingPhotocardRead | None
    condition_grade: ConditionGradeRead


class WantCreate(BaseModel):
    photocard_id: int | None = None
    pending_photocard_id: int | None = None
    minimum_condition_grade_id: int | None = None
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_card_ref(self) -> "WantCreate":
        if (self.photocard_id is None) == (self.pending_photocard_id is None):
            raise ValueError("Provide exactly one of photocard_id or pending_photocard_id")
        return self


class WantUpdate(BaseModel):
    photocard_id: int | None = None
    pending_photocard_id: int | None = None
    minimum_condition_grade_id: int | None = None
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_card_ref(self) -> "WantUpdate":
        if self.photocard_id is not None and self.pending_photocard_id is not None:
            raise ValueError("Provide only one of photocard_id or pending_photocard_id")
        return self


class WantRead(OrmModel):
    id: int
    photocard_id: int | None
    pending_photocard_id: int | None
    minimum_condition_grade_id: int | None
    note: str | None
    photocard: PhotocardRead | None
    pending_photocard: PendingPhotocardRead | None
    minimum_condition_grade: ConditionGradeRead | None
