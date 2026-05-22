from datetime import datetime
from typing import Literal

from app.schemas.catalog import ConditionGradeRead
from app.schemas.common import OrmModel


class ExploreGroupRead(OrmModel):
    id: int
    name: str
    slug: str


class ExploreMemberRead(OrmModel):
    id: int
    name: str
    stage_name: str | None


class ExploreReleaseSourceRead(OrmModel):
    id: int
    title: str
    source_type: str
    retailer_or_event: str | None
    venue: str | None
    country: str | None
    round: str | None
    detail: str | None


class ExplorePhotocardRead(OrmModel):
    id: int
    name: str
    version: str | None


class ExploreCardRead(OrmModel):
    entry_type: Literal["have", "want"]
    username: str
    group: ExploreGroupRead
    member: ExploreMemberRead
    release_source: ExploreReleaseSourceRead | None
    photocard: ExplorePhotocardRead
    condition_grade: ConditionGradeRead | None = None
    minimum_condition_grade: ConditionGradeRead | None = None
    created_at: datetime
