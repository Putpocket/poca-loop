from app.api.v1.admin import transfer_pending_card_references
from tests.test_catalog_and_user_cards import pending_payload, seed_catalog
from tests.test_direct_matches import login_named_user


def create_pending(client, headers, description: str):
    return client.post(
        "/api/v1/catalog/pending-photocards",
        json=pending_payload(card_description=description),
        headers=headers,
    ).json()


def approval_payload(card, name="Approved Card", version="Approved", reason="approved by admin"):
    return {
        "group_id": card["group_id"],
        "member_id": card["member_id"],
        "release_id": card["release_id"],
        "name": name,
        "version": version,
        "notes": "Approved from pending photocard text metadata.",
        "reason": reason,
    }


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
    approved_response = client.get(
        "/api/v1/admin/pending-photocards?catalog_status=approved",
        headers=admin_headers,
    )
    unsupported_response = client.get(
        "/api/v1/admin/pending-photocards?catalog_status=merged",
        headers=admin_headers,
    )

    assert pending_response.status_code == 200
    assert len(pending_response.json()) == 1
    assert rejected_response.status_code == 200
    assert rejected_response.json() == []
    assert approved_response.status_code == 200
    assert approved_response.json() == []
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


def test_admin_can_approve_pending_photocard(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-owner@example.com", "approve_owner")
    pending = create_pending(client, user_headers, "approve me")

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card),
        headers=admin_headers,
    )
    photocards = client.get("/api/v1/catalog/photocards").json()

    assert response.status_code == 200
    data = response.json()
    assert data["catalog_status"] == "approved"
    assert data["approved_photocard_id"] is not None
    assert data["reviewed_by_admin_id"] is not None
    assert data["reviewed_at"] is not None
    assert data["review_reason"] == "approved by admin"
    created = next(item for item in photocards if item["id"] == data["approved_photocard_id"])
    assert created["name"] == "Approved Card"
    assert created["version"] == "Approved"


def test_approve_pending_photocard_requires_login_and_admin(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-user@example.com", "approve_user")
    pending = create_pending(client, user_headers, "protected approve")

    unauthenticated = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card),
    )
    forbidden = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card),
        headers=user_headers,
    )

    assert unauthenticated.status_code == 401
    assert forbidden.status_code == 403


def test_approve_pending_photocard_returns_404_for_missing_id(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)

    response = client.post(
        "/api/v1/admin/pending-photocards/999999/approve",
        json=approval_payload(card),
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_rejected_pending_photocard_cannot_be_approved(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-rejected@example.com", "approve_rejected")
    pending = create_pending(client, user_headers, "rejected first")
    client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/reject",
        json={"reason": "not approved"},
        headers=admin_headers,
    )

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card),
        headers=admin_headers,
    )

    assert response.status_code == 409


def test_approve_pending_photocard_is_idempotent(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-again@example.com", "approve_again")
    pending = create_pending(client, user_headers, "approve again")

    first = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="Idempotent Card", version="A"),
        headers=admin_headers,
    )
    second = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="Should Not Create", version="B"),
        headers=admin_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["catalog_status"] == "approved"
    assert second.json()["approved_photocard_id"] == first.json()["approved_photocard_id"]


def test_approve_transfers_pending_have_and_want_to_new_photocard(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-transfer@example.com", "approve_transfer")
    pending = create_pending(client, user_headers, "transfer me")
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

    approve = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="Transferred Card"),
        headers=admin_headers,
    )
    approved_id = approve.json()["approved_photocard_id"]
    haves = client.get("/api/v1/me/cards/haves", headers=user_headers).json()
    wants = client.get("/api/v1/me/cards/wants", headers=user_headers).json()

    assert approve.status_code == 200
    assert len(haves) == 1
    assert len(wants) == 1
    assert haves[0]["photocard_id"] == approved_id
    assert haves[0]["pending_photocard_id"] is None
    assert haves[0]["pending_photocard"] is None
    assert haves[0]["photocard"]["name"] == "Transferred Card"
    assert wants[0]["photocard_id"] == approved_id
    assert wants[0]["pending_photocard_id"] is None
    assert wants[0]["pending_photocard"] is None


def test_transfer_deletes_duplicate_pending_want(db, client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-want-dup@example.com", "approve_want_dup")
    pending = create_pending(client, user_headers, "duplicate want")
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"pending_photocard_id": pending["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_headers,
    )

    transfer_pending_card_references(db, pending["id"], card["id"])
    db.commit()
    wants = client.get("/api/v1/me/cards/wants", headers=user_headers).json()

    assert len(wants) == 1
    assert wants[0]["photocard_id"] == card["id"]
    assert wants[0]["pending_photocard_id"] is None


def test_transfer_deletes_duplicate_pending_have_with_same_grade(db, client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-have-dup@example.com", "approve_have_dup")
    pending = create_pending(client, user_headers, "duplicate have")
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    )

    transfer_pending_card_references(db, pending["id"], card["id"])
    db.commit()
    haves = client.get("/api/v1/me/cards/haves", headers=user_headers).json()

    assert len(haves) == 1
    assert haves[0]["photocard_id"] == card["id"]
    assert haves[0]["pending_photocard_id"] is None
