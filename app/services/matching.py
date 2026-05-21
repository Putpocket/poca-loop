from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Photocard
from app.models.user_card import ConditionGrade, UserHave, UserWant
from app.models.users import User
from app.schemas.matching import (
    ConditionCheck,
    DirectMatchRead,
    MatchCardSide,
    ThreeWayMatchRead,
    ThreeWayTradeEdge,
)

GRADE_RANK = {
    "S": 5,
    "A": 4,
    "B": 3,
    "C": 2,
    "D": 1,
}


def grade_meets_minimum(actual: ConditionGrade, minimum: ConditionGrade | None) -> bool:
    if minimum is None:
        return actual.code != "D"
    return GRADE_RANK.get(actual.code, 0) >= GRADE_RANK.get(minimum.code, 0)


def load_active_haves_and_wants(db: Session) -> tuple[list[UserHave], list[UserWant]]:
    # TODO: Exclude soft-deleted or inactive photocards once the catalog has soft-delete fields.
    haves = list(
        db.scalars(
            select(UserHave)
            .options(
                selectinload(UserHave.user),
                selectinload(UserHave.photocard).selectinload(Photocard.release),
                selectinload(UserHave.condition_grade),
            )
            .join(User)
            .where(User.is_active.is_(True))
        ).all()
    )
    wants = list(
        db.scalars(
            select(UserWant)
            .options(
                selectinload(UserWant.user),
                selectinload(UserWant.photocard).selectinload(Photocard.release),
                selectinload(UserWant.minimum_condition_grade),
            )
            .join(User)
            .where(User.is_active.is_(True))
        ).all()
    )
    return haves, wants


def canonical_three_way_key(edges: list[tuple[int, int, int]]) -> tuple[tuple[int, int, int], ...]:
    rotations = [tuple(edges[i:] + edges[:i]) for i in range(len(edges))]
    return min(rotations)


def get_direct_matches(db: Session, current_user: User, limit: int = 50) -> list[DirectMatchRead]:
    haves, wants = load_active_haves_and_wants(db)

    haves_by_card: dict[int, list[UserHave]] = {}
    wants_by_card: dict[int, list[UserWant]] = {}
    for have in haves:
        haves_by_card.setdefault(have.photocard_id, []).append(have)
    for want in wants:
        wants_by_card.setdefault(want.photocard_id, []).append(want)

    generated_at = datetime.now(UTC)
    seen: set[tuple[int, int, int, int]] = set()
    matches: list[DirectMatchRead] = []

    for user_a_have in haves:
        if user_a_have.user_id != current_user.id:
            continue

        for user_b_want in wants_by_card.get(user_a_have.photocard_id, []):
            if user_b_want.user_id == user_a_have.user_id:
                continue
            if not grade_meets_minimum(user_a_have.condition_grade, user_b_want.minimum_condition_grade):
                continue

            for user_a_want in wants:
                if user_a_want.user_id != user_a_have.user_id:
                    continue

                for user_b_have in haves_by_card.get(user_a_want.photocard_id, []):
                    if user_b_have.user_id != user_b_want.user_id:
                        continue
                    if not grade_meets_minimum(
                        user_b_have.condition_grade, user_a_want.minimum_condition_grade
                    ):
                        continue

                    user_pair = tuple(sorted((user_a_have.user_id, user_b_have.user_id)))
                    card_pair = tuple(sorted((user_a_have.photocard_id, user_b_have.photocard_id)))
                    dedupe_key = (*user_pair, *card_pair)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)

                    matches.append(
                        DirectMatchRead(
                            match_type="direct",
                            user_a=user_a_have.user,
                            user_b=user_b_have.user,
                            user_a_gives=MatchCardSide(
                                photocard=user_a_have.photocard,
                                condition_grade=user_a_have.condition_grade,
                            ),
                            user_a_receives=MatchCardSide(
                                photocard=user_b_have.photocard,
                                condition_grade=user_b_have.condition_grade,
                            ),
                            user_b_gives=MatchCardSide(
                                photocard=user_b_have.photocard,
                                condition_grade=user_b_have.condition_grade,
                            ),
                            user_b_receives=MatchCardSide(
                                photocard=user_a_have.photocard,
                                condition_grade=user_a_have.condition_grade,
                            ),
                            condition_check=ConditionCheck(
                                user_a_give_meets_user_b_minimum=True,
                                user_b_give_meets_user_a_minimum=True,
                                user_a_give_grade=user_a_have.condition_grade.code,
                                user_b_minimum_grade=(
                                    user_b_want.minimum_condition_grade.code
                                    if user_b_want.minimum_condition_grade
                                    else None
                                ),
                                user_b_give_grade=user_b_have.condition_grade.code,
                                user_a_minimum_grade=(
                                    user_a_want.minimum_condition_grade.code
                                    if user_a_want.minimum_condition_grade
                                    else None
                                ),
                            ),
                            generated_at=generated_at,
                        )
                    )
                    if len(matches) >= limit:
                        return matches

    return matches


def get_three_way_matches(db: Session, current_user: User, limit: int = 50) -> list[ThreeWayMatchRead]:
    haves, wants = load_active_haves_and_wants(db)

    haves_by_card: dict[int, list[UserHave]] = {}
    wants_by_user: dict[int, list[UserWant]] = {}
    for have in haves:
        haves_by_card.setdefault(have.photocard_id, []).append(have)
    for want in wants:
        wants_by_user.setdefault(want.user_id, []).append(want)

    generated_at = datetime.now(UTC)
    seen: set[tuple[tuple[int, int, int], ...]] = set()
    matches: list[ThreeWayMatchRead] = []

    for user_a_want in wants:
        user_a_id = user_a_want.user_id

        for user_b_have in haves_by_card.get(user_a_want.photocard_id, []):
            user_b_id = user_b_have.user_id
            if user_b_id == user_a_id:
                continue
            if not grade_meets_minimum(user_b_have.condition_grade, user_a_want.minimum_condition_grade):
                continue

            for user_b_want in wants_by_user.get(user_b_id, []):
                for user_c_have in haves_by_card.get(user_b_want.photocard_id, []):
                    user_c_id = user_c_have.user_id
                    if len({user_a_id, user_b_id, user_c_id}) != 3:
                        continue
                    if not grade_meets_minimum(
                        user_c_have.condition_grade, user_b_want.minimum_condition_grade
                    ):
                        continue

                    for user_c_want in wants_by_user.get(user_c_id, []):
                        for user_a_have in haves_by_card.get(user_c_want.photocard_id, []):
                            if user_a_have.user_id != user_a_id:
                                continue
                            if not grade_meets_minimum(
                                user_a_have.condition_grade,
                                user_c_want.minimum_condition_grade,
                            ):
                                continue

                            if current_user.id not in {user_a_id, user_b_id, user_c_id}:
                                continue

                            edge_key = canonical_three_way_key(
                                [
                                    (user_b_id, user_a_id, user_b_have.photocard_id),
                                    (user_c_id, user_b_id, user_c_have.photocard_id),
                                    (user_a_id, user_c_id, user_a_have.photocard_id),
                                ]
                            )
                            if edge_key in seen:
                                continue
                            seen.add(edge_key)

                            matches.append(
                                ThreeWayMatchRead(
                                    match_type="three_way",
                                    participants=[
                                        user_a_want.user,
                                        user_b_have.user,
                                        user_c_have.user,
                                    ],
                                    trade_edges=[
                                        ThreeWayTradeEdge(
                                            giver=user_b_have.user,
                                            receiver=user_a_want.user,
                                            card=user_b_have.photocard,
                                            condition_grade=user_b_have.condition_grade,
                                            receiver_min_condition_grade=(
                                                user_a_want.minimum_condition_grade
                                            ),
                                            condition_passed=True,
                                        ),
                                        ThreeWayTradeEdge(
                                            giver=user_c_have.user,
                                            receiver=user_b_have.user,
                                            card=user_c_have.photocard,
                                            condition_grade=user_c_have.condition_grade,
                                            receiver_min_condition_grade=(
                                                user_b_want.minimum_condition_grade
                                            ),
                                            condition_passed=True,
                                        ),
                                        ThreeWayTradeEdge(
                                            giver=user_a_have.user,
                                            receiver=user_c_have.user,
                                            card=user_a_have.photocard,
                                            condition_grade=user_a_have.condition_grade,
                                            receiver_min_condition_grade=(
                                                user_c_want.minimum_condition_grade
                                            ),
                                            condition_passed=True,
                                        ),
                                    ],
                                    generated_at=generated_at,
                                )
                            )
                            if len(matches) >= limit:
                                return matches

    return matches
