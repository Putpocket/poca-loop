from datetime import date

from pydantic import AnyHttpUrl, BaseModel, Field

from app.schemas.common import OrmModel


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")


class GroupRead(OrmModel):
    id: int
    name: str
    slug: str


class MemberCreate(BaseModel):
    group_id: int
    name: str = Field(min_length=1, max_length=120)
    stage_name: str | None = Field(default=None, max_length=120)


class MemberUpdate(BaseModel):
    group_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    stage_name: str | None = Field(default=None, max_length=120)


class MemberRead(OrmModel):
    id: int
    group_id: int
    name: str
    stage_name: str | None


class ReleaseCreate(BaseModel):
    group_id: int
    title: str = Field(min_length=1, max_length=160)
    release_type: str = Field(min_length=1, max_length=40)
    released_on: date | None = None


class ReleaseUpdate(BaseModel):
    group_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    release_type: str | None = Field(default=None, min_length=1, max_length=40)
    released_on: date | None = None


class ReleaseRead(OrmModel):
    id: int
    group_id: int
    title: str
    release_type: str
    released_on: date | None


class PhotocardCreate(BaseModel):
    group_id: int
    member_id: int
    release_id: int | None = None
    name: str = Field(min_length=1, max_length=160)
    version: str | None = Field(default=None, max_length=120)
    external_url: AnyHttpUrl | None = None
    notes: str | None = Field(default=None, max_length=500)


class PhotocardUpdate(BaseModel):
    group_id: int | None = None
    member_id: int | None = None
    release_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=160)
    version: str | None = Field(default=None, max_length=120)
    external_url: AnyHttpUrl | None = None
    notes: str | None = Field(default=None, max_length=500)


class PhotocardRead(OrmModel):
    id: int
    group_id: int
    member_id: int
    release_id: int | None
    name: str
    version: str | None
    external_url: str | None
    notes: str | None


class ConditionGradeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=20, pattern=r"^[A-Z0-9_]+$")
    label: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(ge=0)


class ConditionGradeUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20, pattern=r"^[A-Z0-9_]+$")
    label: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    sort_order: int | None = Field(default=None, ge=0)


class ConditionGradeRead(OrmModel):
    id: int
    code: str
    label: str
    description: str | None
    sort_order: int
