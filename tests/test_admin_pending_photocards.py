from tests.test_catalog_and_user_cards import pending_payload
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
    unsupported_response = client.get(
        "/api/v1/admin/pending-photocards?catalog_status=approved",
        headers=admin_headers,
    )

    assert pending_response.status_code == 200
    assert len(pending_response.json()) == 1
    assert unsupported_response.status_code == 422


def test_my_pending_photocards_still_shows_only_current_user_items(client):
    user_a = login_named_user(client, "my-pending-a@example.com", "my_pending_a")
    user_b = login_named_user(client, "my-pending-b@example.com", "my_pending_b")
    mine = create_pending(client, user_a, "mine")
    create_pending(client, user_b, "not mine")

    response = client.get("/api/v1/me/pending-photocards", headers=user_a)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [mine["id"]]
