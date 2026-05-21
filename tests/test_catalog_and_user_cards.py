from sqlalchemy import select

from app.db.seed import seed_default_data
from app.models.user_card import ConditionGrade
from tests.test_direct_matches import login_named_user


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


def create_extra_card(client, admin_headers, name="Bunny Night"):
    group = client.get("/api/v1/catalog/groups").json()[0]
    member = client.get("/api/v1/catalog/members").json()[0]
    release = client.get("/api/v1/catalog/releases").json()[0]
    return client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": group["id"],
            "member_id": member["id"],
            "release_id": release["id"],
            "name": name,
        },
        headers=admin_headers,
    ).json()


def create_extra_grade(client, admin_headers, code="EX"):
    return client.post(
        "/api/v1/catalog/condition-grades",
        json={"code": code, "label": f"{code} Grade", "sort_order": 20},
        headers=admin_headers,
    ).json()


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


def test_user_can_update_own_have(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    new_card = create_extra_card(client, admin_headers)
    new_grade = create_extra_grade(client, admin_headers)
    user_headers = login_user(client)
    have = client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"], "note": "old"},
        headers=user_headers,
    ).json()

    response = client.patch(
        f"/api/v1/me/cards/haves/{have['id']}",
        json={
            "photocard_id": new_card["id"],
            "condition_grade_id": new_grade["id"],
            "note": "updated",
        },
        headers=user_headers,
    )

    assert response.status_code == 200
    assert response.json()["photocard_id"] == new_card["id"]
    assert response.json()["condition_grade"]["code"] == "EX"
    assert response.json()["note"] == "updated"


def test_user_can_delete_own_have(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_user(client)
    have = client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    ).json()

    response = client.delete(f"/api/v1/me/cards/haves/{have['id']}", headers=user_headers)
    remaining = client.get("/api/v1/me/cards/haves", headers=user_headers)

    assert response.status_code == 204
    assert remaining.json() == []


def test_user_cannot_update_or_delete_other_users_have(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    owner_headers = login_named_user(client, "owner-have@example.com", "owner_have")
    other_headers = login_named_user(client, "other-have@example.com", "other_have")
    have = client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=owner_headers,
    ).json()

    update = client.patch(
        f"/api/v1/me/cards/haves/{have['id']}",
        json={"note": "not mine"},
        headers=other_headers,
    )
    delete = client.delete(f"/api/v1/me/cards/haves/{have['id']}", headers=other_headers)

    assert update.status_code == 404
    assert delete.status_code == 404


def test_user_can_update_own_want(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    new_card = create_extra_card(client, admin_headers)
    new_grade = create_extra_grade(client, admin_headers)
    user_headers = login_user(client)
    want = client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"], "note": "old"},
        headers=user_headers,
    ).json()

    response = client.patch(
        f"/api/v1/me/cards/wants/{want['id']}",
        json={
            "photocard_id": new_card["id"],
            "minimum_condition_grade_id": new_grade["id"],
            "note": "updated",
        },
        headers=user_headers,
    )

    assert response.status_code == 200
    assert response.json()["photocard_id"] == new_card["id"]
    assert response.json()["minimum_condition_grade"]["code"] == "EX"
    assert response.json()["note"] == "updated"


def test_user_can_delete_own_want(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_user(client)
    want = client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    ).json()

    response = client.delete(f"/api/v1/me/cards/wants/{want['id']}", headers=user_headers)
    remaining = client.get("/api/v1/me/cards/wants", headers=user_headers)

    assert response.status_code == 204
    assert remaining.json() == []


def test_user_cannot_update_or_delete_other_users_want(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    owner_headers = login_named_user(client, "owner-want@example.com", "owner_want")
    other_headers = login_named_user(client, "other-want@example.com", "other_want")
    want = client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=owner_headers,
    ).json()

    update = client.patch(
        f"/api/v1/me/cards/wants/{want['id']}",
        json={"note": "not mine"},
        headers=other_headers,
    )
    delete = client.delete(f"/api/v1/me/cards/wants/{want['id']}", headers=other_headers)

    assert update.status_code == 404
    assert delete.status_code == 404


def test_duplicate_user_card_update_returns_409(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    other_card = create_extra_card(client, admin_headers)
    other_grade = create_extra_grade(client, admin_headers)
    user_headers = login_user(client)

    have_a = client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    ).json()
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": other_card["id"], "condition_grade_id": other_grade["id"]},
        headers=user_headers,
    )
    duplicate_have = client.patch(
        f"/api/v1/me/cards/haves/{have_a['id']}",
        json={"photocard_id": other_card["id"], "condition_grade_id": other_grade["id"]},
        headers=user_headers,
    )

    want_a = client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    ).json()
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": other_card["id"], "minimum_condition_grade_id": other_grade["id"]},
        headers=user_headers,
    )
    duplicate_want = client.patch(
        f"/api/v1/me/cards/wants/{want_a['id']}",
        json={"photocard_id": other_card["id"]},
        headers=user_headers,
    )

    assert duplicate_have.status_code == 409
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


def pending_payload(**overrides):
    payload = {
        "group_name": "NMIXX",
        "member_name": "Haewon",
        "source_type": "popup",
        "source_title": "Fe3O4: BREAK POP-UP STORE",
        "retailer_or_event": "JYP SHOP",
        "venue": "The Hyundai Seoul",
        "round": "1차",
        "detail": "5만원 이상 구매 특전",
        "card_description": "Haewon random photocard",
        "version": "A",
        "memo": "No image stored",
    }
    payload.update(overrides)
    return payload


def test_logged_in_user_can_create_pending_photocard(client):
    user_headers = login_named_user(client, "pending@example.com", "pending_user")

    response = client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(),
        headers=user_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["catalog_status"] == "pending"
    assert data["source_type"] == "popup"
    assert data["card_description"] == "Haewon random photocard"


def test_pending_photocard_requires_login(client):
    response = client.post("/api/v1/catalog/pending-photocards", json=pending_payload())
    assert response.status_code == 401


def test_user_can_list_own_pending_photocards(client):
    user_a = login_named_user(client, "pending-a@example.com", "pending_a")
    user_b = login_named_user(client, "pending-b@example.com", "pending_b")
    mine = client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(card_description="mine"),
        headers=user_a,
    ).json()
    client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(card_description="other"),
        headers=user_b,
    )

    response = client.get("/api/v1/me/pending-photocards", headers=user_a)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [mine["id"]]


def test_have_and_want_can_use_pending_photocard(client, admin_headers):
    _, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "pending-card@example.com", "pending_card")
    pending = client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(),
        headers=user_headers,
    ).json()

    have = client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    )
    want = client.post(
        "/api/v1/me/cards/wants",
        json={"pending_photocard_id": pending["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    )

    assert have.status_code == 201
    assert have.json()["photocard"] is None
    assert have.json()["pending_photocard"]["card_description"] == "Haewon random photocard"
    assert want.status_code == 201
    assert want.json()["photocard"] is None
    assert want.json()["pending_photocard"]["catalog_status"] == "pending"


def test_card_reference_validation_rejects_both_or_neither(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "pending-invalid@example.com", "pending_invalid")
    pending = client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(),
        headers=user_headers,
    ).json()

    both = client.post(
        "/api/v1/me/cards/haves",
        json={
            "photocard_id": card["id"],
            "pending_photocard_id": pending["id"],
            "condition_grade_id": grade["id"],
        },
        headers=user_headers,
    )
    neither = client.post(
        "/api/v1/me/cards/wants",
        json={"minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    )

    assert both.status_code == 422
    assert neither.status_code == 422


def test_cannot_register_other_users_pending_photocard(client, admin_headers):
    _, grade = seed_catalog(client, admin_headers)
    owner_headers = login_named_user(client, "pending-owner@example.com", "pending_owner")
    other_headers = login_named_user(client, "pending-other@example.com", "pending_other")
    pending = client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(card_description="owner only"),
        headers=owner_headers,
    ).json()

    have = client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=other_headers,
    )
    want = client.post(
        "/api/v1/me/cards/wants",
        json={"pending_photocard_id": pending["id"], "minimum_condition_grade_id": grade["id"]},
        headers=other_headers,
    )

    assert have.status_code == 404
    assert want.status_code == 404


def test_cannot_update_to_other_users_pending_photocard(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    owner_headers = login_named_user(client, "pending-update-owner@example.com", "pending_update_owner")
    other_headers = login_named_user(client, "pending-update-other@example.com", "pending_update_other")
    pending = client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(card_description="not yours"),
        headers=owner_headers,
    ).json()
    have = client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=other_headers,
    ).json()
    want = client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=other_headers,
    ).json()

    have_update = client.patch(
        f"/api/v1/me/cards/haves/{have['id']}",
        json={"pending_photocard_id": pending["id"]},
        headers=other_headers,
    )
    want_update = client.patch(
        f"/api/v1/me/cards/wants/{want['id']}",
        json={"pending_photocard_id": pending["id"]},
        headers=other_headers,
    )

    assert have_update.status_code == 404
    assert want_update.status_code == 404


def test_pending_photocard_in_have_want_list_response(client, admin_headers):
    _, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "pending-list@example.com", "pending_list")
    pending = client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(card_description="list check"),
        headers=user_headers,
    ).json()
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"pending_photocard_id": pending["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    )

    haves = client.get("/api/v1/me/cards/haves", headers=user_headers).json()
    wants = client.get("/api/v1/me/cards/wants", headers=user_headers).json()

    assert haves[0]["pending_photocard"]["card_description"] == "list check"
    assert wants[0]["pending_photocard"]["id"] == pending["id"]


def test_existing_official_photocard_have_want_still_work(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "official-still@example.com", "official_still")

    have = client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    )
    want = client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    )

    assert have.status_code == 201
    assert have.json()["pending_photocard"] is None
    assert have.json()["photocard"]["id"] == card["id"]
    assert want.status_code == 201
    assert want.json()["pending_photocard"] is None
