from tests.test_admin_pending_photocards import approval_payload, create_pending
from tests.test_catalog_and_user_cards import create_extra_card, seed_catalog
from tests.test_direct_matches import login_named_user


def test_explore_cards_requires_login(client):
    response = client.get("/api/v1/explore/cards")

    assert response.status_code == 401


def test_logged_in_user_can_explore_have_and_want_entries(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_a = login_named_user(client, "explore-a@example.com", "explore_a")
    user_b = login_named_user(client, "explore-b@example.com", "explore_b")

    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_b,
    )

    response = client.get("/api/v1/explore/cards", headers=user_a)

    assert response.status_code == 200
    data = response.json()
    assert {item["entry_type"] for item in data} == {"have", "want"}
    have = next(item for item in data if item["entry_type"] == "have")
    want = next(item for item in data if item["entry_type"] == "want")
    assert have["username"] == "explore_a"
    assert have["group"]["name"] == "NewJeans"
    assert have["member"]["name"] == "Minji"
    assert have["release_source"]["title"] == "Get Up"
    assert have["release_source"]["source_type"] == "album"
    assert have["photocard"]["name"] == "Bunny Beach"
    assert have["condition_grade"]["code"] == "NM"
    assert have["minimum_condition_grade"] is None
    assert want["username"] == "explore_b"
    assert want["condition_grade"] is None
    assert want["minimum_condition_grade"]["code"] == "NM"
    assert "created_at" in have


def test_explore_cards_does_not_expose_sensitive_user_fields(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user = login_named_user(client, "explore-sensitive@example.com", "explore_sensitive")
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user,
    )

    response = client.get("/api/v1/explore/cards", headers=user)

    assert response.status_code == 200
    serialized = str(response.json())
    assert "explore-sensitive@example.com" not in serialized
    assert "email" not in serialized
    assert "hashed_password" not in serialized
    assert "is_admin" not in serialized
    assert "role" not in serialized
    assert "token" not in serialized


def test_explore_cards_excludes_pending_photocard_entries(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user = login_named_user(client, "explore-pending@example.com", "explore_pending")
    pending = create_pending(client, user, "pending hidden")
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"pending_photocard_id": pending["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user,
    )

    response = client.get("/api/v1/explore/cards", headers=user)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["photocard"]["id"] == card["id"]
    serialized = str(data)
    assert "pending hidden" not in serialized
    assert "pending_photocard" not in serialized
    assert "catalog_status" not in serialized


def test_explore_cards_includes_pending_after_approval_and_merge(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user = login_named_user(client, "explore-transfer@example.com", "explore_transfer")
    approved_pending = create_pending(client, user, "approve into explore")
    merged_pending = create_pending(client, user, "merge into explore")

    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": approved_pending["id"], "condition_grade_id": grade["id"]},
        headers=user,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"pending_photocard_id": merged_pending["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user,
    )

    approved = client.post(
        f"/api/v1/admin/pending-photocards/{approved_pending['id']}/approve",
        json=approval_payload(card, name="Explore Approved", version="A"),
        headers=admin_headers,
    )
    merged = client.post(
        f"/api/v1/admin/pending-photocards/{merged_pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    response = client.get("/api/v1/explore/cards", headers=user)

    assert approved.status_code == 200
    assert merged.status_code == 200
    assert response.status_code == 200
    data = response.json()
    assert {item["entry_type"] for item in data} == {"have", "want"}
    assert {item["photocard"]["name"] for item in data} == {"Explore Approved", "Bunny Beach"}
    assert "approve into explore" not in str(data)
    assert "merge into explore" not in str(data)


def test_explore_cards_filters_and_limit_validation(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    extra_card = create_extra_card(client, admin_headers, name="Bunny Night")
    user = login_named_user(client, "explore-filter@example.com", "explore_filter")

    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": extra_card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user,
    )

    have_response = client.get("/api/v1/explore/cards?entry_type=have", headers=user)
    want_response = client.get("/api/v1/explore/cards?entry_type=want", headers=user)
    group_response = client.get(f"/api/v1/explore/cards?group_id={card['group_id']}", headers=user)
    member_response = client.get(f"/api/v1/explore/cards?member_id={card['member_id']}", headers=user)
    release_response = client.get(f"/api/v1/explore/cards?release_id={card['release_id']}", headers=user)
    card_response = client.get(f"/api/v1/explore/cards?photocard_id={extra_card['id']}", headers=user)
    source_response = client.get("/api/v1/explore/cards?source_type=album", headers=user)
    limit_response = client.get("/api/v1/explore/cards?limit=1", headers=user)
    too_large_response = client.get("/api/v1/explore/cards?limit=101", headers=user)
    invalid_type_response = client.get("/api/v1/explore/cards?entry_type=trade", headers=user)

    assert have_response.status_code == 200
    assert [item["entry_type"] for item in have_response.json()] == ["have"]
    assert want_response.status_code == 200
    assert [item["entry_type"] for item in want_response.json()] == ["want"]
    assert group_response.status_code == 200
    assert len(group_response.json()) == 2
    assert member_response.status_code == 200
    assert len(member_response.json()) == 2
    assert release_response.status_code == 200
    assert len(release_response.json()) == 2
    assert card_response.status_code == 200
    assert card_response.json()[0]["photocard"]["id"] == extra_card["id"]
    assert source_response.status_code == 200
    assert len(source_response.json()) == 2
    assert limit_response.status_code == 200
    assert len(limit_response.json()) == 1
    assert too_large_response.status_code == 422
    assert invalid_type_response.status_code == 422
