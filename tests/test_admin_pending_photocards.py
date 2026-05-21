from tests.test_catalog_and_user_cards import pending_payload, seed_catalog
from tests.test_direct_matches import login_named_user


def create_pending(client, headers, description: str):
    return client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(card_description=description),
        headers=headers,
    ).json()


def test_admin_pending_photocards_requires_login(client):
    response = client.get("/api/v1/admin/pending-photocards")

    assert response.status_code == 401


def test_admin_pending_photocards_requires_admin(client):
    user_headers = login_named_user(client, "admin-review-user@example.com", "admin_review_user")

    response = client.get("/api/v1/admin/pending-photocards", headers=user_headers)

    assert response.status_code == 403


def test_admin_can_list_pending_photocards(client, admin_headers):
    user_headers = login_named_user(client, "pending-review@example.com", "pending_review")
    pending = create_pending(client, user_headers, "review me")

    response = client.get("/api/v1/admin/pending-photocards", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == pending["id"]
    assert data[0]["created_by_user_id"] == pending["created_by_user_id"]
    assert data[0]["group_name"] == "NMIXX"
    assert data[0]["member_name"] == "Haewon"
    assert data[0]["source_type"] == "popup"
    assert data[0]["source_title"] == "Fe3O4: BREAK POP-UP STORE"
    assert data[0]["retailer_or_event"] == "JYP SHOP"
    assert data[0]["venue"] == "The Hyundai Seoul"
    assert data[0]["country"] is None
    assert data[0]["round"] == "1차"
    assert data[0]["detail"] == "5만원 이상 구매 특전"
    assert data[0]["card_description"] == "review me"
    assert data[0]["version"] == "A"
    assert data[0]["memo"] == "No image stored"
    assert data[0]["catalog_status"] == "pending"
    assert "created_at" in data[0]
    assert "updated_at" in data[0]


def test_admin_pending_photocards_limit_defaults_and_validation(client, admin_headers):
    user_headers = login_named_user(client, "pending-limit@example.com", "pending_limit")
    for index in range(3):
        create_pending(client, user_headers, f"pending {index}")

    default_response = client.get("/api/v1/admin/pending-photocards", headers=admin_headers)
    max_response = client.get("/api/v1/admin/pending-photocards?limit=100", headers=admin_headers)
    limited_response = client.get("/api/v1/admin/pending-photocards?limit=2", headers=admin_headers)
    too_large_response = client.get("/api/v1/admin/pending-photocards?limit=101", headers=admin_headers)
    invalid_response = client.get("/api/v1/admin/pending-photocards?limit=0", headers=admin_headers)

    assert default_response.status_code == 200
    assert len(default_response.json()) <= 50
    assert max_response.status_code == 200
    assert limited_response.status_code == 200
    assert len(limited_response.json()) == 2
    assert too_large_response.status_code == 422
    assert invalid_response.status_code == 422


def test_admin_pending_photocards_status_filter_accepts_pending_only(client, admin_headers):
    user_headers = login_named_user(client, "pending-filter@example.com", "pending_filter")
    create_pending(client, user_headers, "filter me")

    pending_response = client.get(
        "/api/v1/admin/pending-photocards?catalog_status=pending",
        headers=admin_headers,
    )
    rejected_response = client.get(
        "/api/v1/admin/pending-photocards?catalog_status=rejected",
        headers=admin_headers,
    )
    unsupported_response = client.get(
        "/api/v1/admin/pending-photocards?catalog_status=approved",
        headers=admin_headers,
    )

    assert pending_response.status_code == 200
    assert len(pending_response.json()) == 1
    assert rejected_response.status_code == 200
    assert rejected_response.json() == []
    assert unsupported_response.status_code == 422


def test_my_pending_photocards_still_shows_only_current_user_items(client):
    user_a = login_named_user(client, "my-pending-a@example.com", "my_pending_a")
    user_b = login_named_user(client, "my-pending-b@example.com", "my_pending_b")
    mine = create_pending(client, user_a, "mine")
    create_pending(client, user_b, "not mine")

    response = client.get("/api/v1/me/pending-photocards", headers=user_a)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [mine["id"]]


def test_admin_can_reject_pending_photocard(client, admin_headers):
    user_headers = login_named_user(client, "reject-owner@example.com", "reject_owner")
    pending = create_pending(client, user_headers, "reject me")

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/reject",
        json={"reason": "duplicate or unsupported catalog item"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pending["id"]
    assert data["catalog_status"] == "rejected"
    assert data["review_reason"] == "duplicate or unsupported catalog item"
    assert data["reviewed_by_admin_id"] is not None
    assert data["reviewed_at"] is not None


def test_reject_pending_photocard_requires_login_and_admin(client):
    user_headers = login_named_user(client, "reject-user@example.com", "reject_user")
    pending = create_pending(client, user_headers, "protected")

    unauthenticated = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/reject",
        json={"reason": "no auth"},
    )
    forbidden = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/reject",
        json={"reason": "not admin"},
        headers=user_headers,
    )

    assert unauthenticated.status_code == 401
    assert forbidden.status_code == 403


def test_reject_pending_photocard_returns_404_for_missing_id(client, admin_headers):
    response = client.post(
        "/api/v1/admin/pending-photocards/999999/reject",
        json={"reason": "missing"},
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_reject_pending_photocard_is_idempotent(client, admin_headers):
    user_headers = login_named_user(client, "reject-again@example.com", "reject_again")
    pending = create_pending(client, user_headers, "reject again")

    first = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/reject",
        json={"reason": "first"},
        headers=admin_headers,
    )
    second = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/reject",
        json={"reason": "second"},
        headers=admin_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["catalog_status"] == "rejected"
    assert second.json()["review_reason"] == "second"


def test_reject_does_not_delete_have_or_want(client, admin_headers):
    _, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "reject-keeps-cards@example.com", "reject_keeps_cards")
    pending = create_pending(client, user_headers, "keep references")
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

    reject = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/reject",
        json={"reason": "not cataloged"},
        headers=admin_headers,
    )
    haves = client.get("/api/v1/me/cards/haves", headers=user_headers)
    wants = client.get("/api/v1/me/cards/wants", headers=user_headers)

    assert reject.status_code == 200
    assert haves.status_code == 200
    assert wants.status_code == 200
    assert len(haves.json()) == 1
    assert len(wants.json()) == 1
    assert haves.json()[0]["pending_photocard"]["catalog_status"] == "rejected"
    assert haves.json()[0]["pending_photocard"]["review_reason"] == "not cataloged"
    assert wants.json()[0]["pending_photocard"]["catalog_status"] == "rejected"
