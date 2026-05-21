from sqlalchemy import select

from app.db.seed import seed_default_data
from app.models.user_card import ConditionGrade


def login_user(client) -> dict[str, str]:
    client.post(
        "/api/v1/auth/signup",
        json={"email": "user@example.com", "username": "collector", "password": "safe-password"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "safe-password"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_catalog(client, admin_headers):
    group = client.post(
        "/api/v1/catalog/groups",
        json={"name": "NewJeans", "slug": "newjeans"},
        headers=admin_headers,
    ).json()
    member = client.post(
        "/api/v1/catalog/members",
        json={"group_id": group["id"], "name": "Minji"},
        headers=admin_headers,
    ).json()
    release = client.post(
        "/api/v1/catalog/releases",
        json={"group_id": group["id"], "title": "Get Up", "release_type": "album"},
        headers=admin_headers,
    ).json()
    card = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": group["id"],
            "member_id": member["id"],
            "release_id": release["id"],
            "name": "Bunny Beach",
            "external_url": "https://example.com/cards/bunny-beach",
        },
        headers=admin_headers,
    ).json()
    grade = client.post(
        "/api/v1/catalog/condition-grades",
        json={"code": "NM", "label": "Near Mint", "sort_order": 10},
        headers=admin_headers,
    ).json()
    return card, grade


def test_catalog_crud_and_user_have_want(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_user(client)

    have = client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"], "note": "sleeved"},
        headers=user_headers,
    )
    assert have.status_code == 201
    assert have.json()["condition_grade"]["code"] == "NM"

    want = client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    )
    assert want.status_code == 201
    assert want.json()["photocard"]["name"] == "Bunny Beach"
    assert want.json()["photocard"]["release"]["source_type"] == "album"

    haves = client.get("/api/v1/me/cards/haves", headers=user_headers)
    wants = client.get("/api/v1/me/cards/wants", headers=user_headers)
    assert len(haves.json()) == 1
    assert len(wants.json()) == 1


def test_release_source_metadata_supports_complex_origins(client, admin_headers):
    group = client.post(
        "/api/v1/catalog/groups",
        json={"name": "NMIXX", "slug": "nmixx"},
        headers=admin_headers,
    ).json()

    payload = {
        "group_id": group["id"],
        "title": "Fe3O4: BREAK POP-UP STORE",
        "source_type": "popup",
        "retailer_or_event": "JYP SHOP",
        "venue": "The Hyundai Seoul",
        "country": "KR",
        "round": "1차",
        "detail": "5만원 이상 구매 특전",
        "notes": "랜덤 포토카드 세트",
    }
    created = client.post("/api/v1/catalog/releases", json=payload, headers=admin_headers)
    assert created.status_code == 201
    data = created.json()
    assert data["source_type"] == "popup"
    assert data["release_type"] == "popup"
    assert data["retailer_or_event"] == "JYP SHOP"
    assert data["venue"] == "The Hyundai Seoul"
    assert data["detail"] == "5만원 이상 구매 특전"

    duplicate = client.post("/api/v1/catalog/releases", json=payload, headers=admin_headers)
    assert duplicate.status_code == 409

    second_round = client.post(
        "/api/v1/catalog/releases",
        json={**payload, "round": "2차"},
        headers=admin_headers,
    )
    assert second_round.status_code == 201


def test_release_type_legacy_payload_sets_source_type(client, admin_headers):
    group = client.post(
        "/api/v1/catalog/groups",
        json={"name": "IVE", "slug": "ive"},
        headers=admin_headers,
    ).json()
    response = client.post(
        "/api/v1/catalog/releases",
        json={"group_id": group["id"], "title": "I AM", "release_type": "album"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["source_type"] == "album"


def test_admin_can_create_group_and_duplicate_group_returns_409(client, admin_headers):
    created = client.post(
        "/api/v1/catalog/groups",
        json={"name": "LE SSERAFIM", "slug": "le-sserafim"},
        headers=admin_headers,
    )
    assert created.status_code == 201

    duplicate = client.post(
        "/api/v1/catalog/groups",
        json={"name": "LE SSERAFIM", "slug": "le-sserafim-2"},
        headers=admin_headers,
    )
    assert duplicate.status_code == 409


def test_seed_creates_default_condition_grades_idempotently(client, db):
    seed_default_data(db)
    seed_default_data(db)

    grades = db.scalars(select(ConditionGrade).order_by(ConditionGrade.sort_order)).all()
    assert [grade.code for grade in grades] == ["S", "A", "B", "C", "D"]


def test_duplicate_have_and_want_return_409(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_user(client)

    have_payload = {"photocard_id": card["id"], "condition_grade_id": grade["id"]}
    first_have = client.post("/api/v1/me/cards/haves", json=have_payload, headers=user_headers)
    duplicate_have = client.post("/api/v1/me/cards/haves", json=have_payload, headers=user_headers)
    assert first_have.status_code == 201
    assert duplicate_have.status_code == 409

    want_payload = {"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]}
    first_want = client.post("/api/v1/me/cards/wants", json=want_payload, headers=user_headers)
    duplicate_want = client.post("/api/v1/me/cards/wants", json=want_payload, headers=user_headers)
    assert first_want.status_code == 201
    assert duplicate_want.status_code == 409


def test_external_url_must_be_valid(client, admin_headers):
    group = client.post(
        "/api/v1/catalog/groups",
        json={"name": "Aespa", "slug": "aespa"},
        headers=admin_headers,
    ).json()
    member = client.post(
        "/api/v1/catalog/members",
        json={"group_id": group["id"], "name": "Karina"},
        headers=admin_headers,
    ).json()
    response = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": group["id"],
            "member_id": member["id"],
            "name": "Drama",
            "external_url": "not-a-url",
        },
        headers=admin_headers,
    )
    assert response.status_code == 422
