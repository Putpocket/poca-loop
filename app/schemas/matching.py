from datetime import datetime

from app.schemas.catalog import ConditionGradeRead, PhotocardRead
from app.schemas.common import OrmModel


class DirectMatchUser(OrmModel):
    id: int
    username: str


class MatchCardSide(OrmModel):
    photocard: PhotocardRead
    condition_grade: ConditionGradeRead


class ConditionCheck(OrmModel):
    user_a_give_meets_user_b_minimum: bool
    user_b_give_meets_user_a_minimum: bool
    user_a_give_grade: str
    user_b_minimum_grade: str | None
    user_b_give_grade: str
    user_a_minimum_grade: str | None


class DirectMatchRead(OrmModel):
    match_type: str
    user_a: DirectMatchUser
    user_b: DirectMatchUser
    user_a_gives: MatchCardSide
    user_a_receives: MatchCardSide
    user_b_gives: MatchCardSide
    user_b_receives: MatchCardSide
    condition_check: ConditionCheck
    generated_at: datetime


class ThreeWayTradeEdge(OrmModel):
    giver: DirectMatchUser
    receiver: DirectMatchUser
    card: PhotocardRead
    condition_grade: ConditionGradeRead
    receiver_min_condition_grade: ConditionGradeRead | None
    condition_passed: bool


class ThreeWayMatchRead(OrmModel):
    match_type: str
    participants: list[DirectMatchUser]
    trade_edges: list[ThreeWayTradeEdge]
    generated_at: datetime
