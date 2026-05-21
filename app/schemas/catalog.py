from datetime import date, datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field, model_validator

from app.schemas.common import OrmModel

ReleaseSourceType = Literal[
    "album",
    "preorder_benefit",
    "store_benefit",
    "lucky_draw",
    "fansign",
    "broadcast",
    "popup",
    "concert",
    "fanmeeting",
    "merch",
    "season_greeting",
    "fanclub",
    "collab",
    "magazine",
    "event",
    "other",
]

SOURCE_TYPES = set(ReleaseSourceType.__args__)


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
    source_type: ReleaseSourceType | None = None
    release_type: str | None = Field(default=None, min_length=1, max_length=40)
    retailer_or_event: str | None = Field(default=None, max_length=160)
    venue: str | None = Field(default=None, max_length=160)
    country: str | None = Field(default=None, max_length=80)
    round: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)
    released_on: date | None = None

    @model_validator(mode="after")
    def sync_release_aliases(self) -> "ReleaseCreate":
        if self.source_type is None and self.release_type is None:
            self.source_type = "album"
            self.release_type = "album"
        elif self.source_type is None and self.release_type is not None:
            if self.release_type not in SOURCE_TYPES:
                raise ValueError("release_type must be one of the supported source types")
            self.source_type = self.release_type  # legacy request compatibility
        elif self.release_type is None and self.source_type is not None:
            self.release_type = self.source_type
        return self


class ReleaseUpdate(BaseModel):
    group_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    source_type: ReleaseSourceType | None = None
    release_type: str | None = Field(default=None, min_length=1, max_length=40)
    retailer_or_event: str | None = Field(default=None, max_length=160)
    venue: str | None = Field(default=None, max_length=160)
    country: str | None = Field(default=None, max_length=80)
    round: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)
    released_on: date | None = None

    @model_validator(mode="after")
    def validate_legacy_release_type(self) -> "ReleaseUpdate":
        if self.source_type is None and self.release_type is not None and self.release_type not in SOURCE_TYPES:
            raise ValueError("release_type must be one of the supported source types")
        return self


class ReleaseRead(OrmModel):
    id: int
    group_id: int
    title: str
    source_type: str
    release_type: str
    retailer_or_event: str | None
    venue: str | None
    country: str | None
    round: str | None
    detail: str | None
    start_date: date | None
    end_date: date | None
    notes: str | None
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
    release: ReleaseRead | None = None


class PendingPhotocardCreate(BaseModel):
    group_id: int | None = None
    group_name: str | None = Field(default=None, max_length=120)
    member_id: int | None = None
    member_name: str | None = Field(default=None, max_length=120)
    source_type: ReleaseSourceType
    source_title: str = Field(min_length=1, max_length=160)
    retailer_or_event: str | None = Field(default=None, max_length=160)
    venue: str | None = Field(default=None, max_length=160)
    country: str | None = Field(default=None, max_length=80)
    round: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=255)
    card_description: str = Field(min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=120)
    memo: str | None = Field(default=None, max_length=500)


class PendingPhotocardRead(OrmModel):
    id: int
    created_by_user_id: int
    group_id: int | None
    group_name: str | None
    member_id: int | None
    member_name: str | None
    source_type: str
    source_title: str
    retailer_or_event: str | None
    venue: str | None
    country: str | None
    round: str | None
    detail: str | None
    card_description: str
    version: str | None
    memo: str | None
    catalog_status: str
    created_at: datetime
    updated_at: datetime


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
