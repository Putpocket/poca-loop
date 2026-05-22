import pytest
from sqlalchemy import select

import app.api.v1.admin as admin_api
from app.models.catalog import PendingPhotocard, Photocard
from app.models.user_card import UserHave, UserWant
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
    merged_response = client.get(
        "/api/v1/admin/pending-photocards?catalog_status=merged",
        headers=admin_headers,
    )
    unsupported_response = client.get(
        "/api/v1/admin/pending-photocards?catalog_status=archived",
        headers=admin_headers,
    )

    assert pending_response.status_code == 200
    assert len(pending_response.json()) == 1
    assert rejected_response.status_code == 200
    assert rejected_response.json() == []
    assert approved_response.status_code == 200
    assert approved_response.json() == []
    assert merged_response.status_code == 200
    assert merged_response.json() == []
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
    assert wants[0]["photocard"]["name"] == "Transferred Card"


def test_approve_keeps_transfer_atomic_when_reference_transfer_fails(
    db, client, admin_headers, monkeypatch
):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-rollback@example.com", "approve_rollback")
    pending = create_pending(client, user_headers, "rollback me")
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

    def fail_transfer(db, pending_id, photocard_id):
        raise RuntimeError("simulated transfer failure")

    monkeypatch.setattr(admin_api, "transfer_pending_card_references", fail_transfer)

    with pytest.raises(RuntimeError):
        client.post(
            f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
            json=approval_payload(card, name="Should Roll Back"),
            headers=admin_headers,
        )

    db.expire_all()
    pending_row = db.get(PendingPhotocard, pending["id"])
    created = db.scalar(select(Photocard).where(Photocard.name == "Should Roll Back"))
    have = db.scalar(select(UserHave).where(UserHave.pending_photocard_id == pending["id"]))
    want = db.scalar(select(UserWant).where(UserWant.pending_photocard_id == pending["id"]))

    assert pending_row.catalog_status == "pending"
    assert pending_row.approved_photocard_id is None
    assert created is None
    assert have is not None
    assert have.photocard_id is None
    assert want is not None
    assert want.photocard_id is None


def test_approve_rejects_member_or_release_from_another_group(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    other_group = client.post(
        "/api/v1/catalog/groups",
        json={"name": "Other Group", "slug": "other-group"},
        headers=admin_headers,
    ).json()
    other_member = client.post(
        "/api/v1/catalog/members",
        json={"group_id": other_group["id"], "name": "Other Member"},
        headers=admin_headers,
    ).json()
    other_release = client.post(
        "/api/v1/catalog/releases",
        json={"group_id": other_group["id"], "title": "Other Release", "release_type": "album"},
        headers=admin_headers,
    ).json()
    user_headers = login_named_user(client, "approve-wrong-refs@example.com", "approve_wrong_refs")
    pending = create_pending(client, user_headers, "wrong refs")

    wrong_member = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json={**approval_payload(card), "member_id": other_member["id"]},
        headers=admin_headers,
    )
    wrong_release = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json={**approval_payload(card), "release_id": other_release["id"]},
        headers=admin_headers,
    )

    assert wrong_member.status_code == 400
    assert wrong_release.status_code == 400


def test_approve_returns_409_when_photocard_identity_already_exists(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-duplicate@example.com", "approve_duplicate")
    pending = create_pending(client, user_headers, "duplicate official")

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name=card["name"], version=card["version"]),
        headers=admin_headers,
    )

    assert response.status_code == 409


def test_approved_reapproval_policy_matches_readme(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-readme@example.com", "approve_readme")
    pending = create_pending(client, user_headers, "readme policy")

    first = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="README Policy Card", version="A"),
        headers=admin_headers,
    )
    second = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="Different README Policy Card", version="B"),
        headers=admin_headers,
    )

    with open("README.md", encoding="utf-8") as readme:
        readme_text = readme.read()

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["approved_photocard_id"] == first.json()["approved_photocard_id"]
    assert "이미 승인된 항목에 다시 요청하면 기존 승인 결과를 200으로 반환합니다" in readme_text


def test_approved_card_disappears_from_pending_badges_and_svg(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "approve-svg@example.com", "approve_svg")
    pending = create_pending(client, user_headers, "svg before approve")
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    )

    before_svg = client.get("/api/v1/templates/me.svg", headers=user_headers)
    approve = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="SVG Approved Card", version="A"),
        headers=admin_headers,
    )
    after_svg = client.get("/api/v1/templates/me.svg", headers=user_headers)
    haves = client.get("/api/v1/me/cards/haves", headers=user_headers).json()

    assert before_svg.status_code == 200
    assert "[임시 등록]" in before_svg.text
    assert approve.status_code == 200
    assert haves[0]["pending_photocard"] is None
    assert haves[0]["photocard"]["name"] == "SVG Approved Card"
    assert after_svg.status_code == 200
    assert "[임시 등록]" not in after_svg.text
    assert "SVG Approved Card (A)" in after_svg.text


def test_approved_card_participates_in_direct_matches(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_a = login_named_user(client, "approve-direct-a@example.com", "approve_direct_a")
    user_b = login_named_user(client, "approve-direct-b@example.com", "approve_direct_b")
    pending = create_pending(client, user_a, "direct approved")
    other_card = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": card["group_id"],
            "member_id": card["member_id"],
            "release_id": card["release_id"],
            "name": "Direct Other Card",
        },
        headers=admin_headers,
    ).json()
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": other_card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": other_card["id"], "condition_grade_id": grade["id"]},
        headers=user_b,
    )
    approve = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="Direct Approved Card"),
        headers=admin_headers,
    )
    approved_id = approve.json()["approved_photocard_id"]
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": approved_id, "minimum_condition_grade_id": grade["id"]},
        headers=user_b,
    )

    response = client.get("/api/v1/matches/direct", headers=user_a)

    assert response.status_code == 200
    assert len(response.json()) == 1
    match = response.json()[0]
    assert match["user_a_gives"]["photocard"]["id"] == approved_id
    assert match["user_a_gives"]["photocard"]["name"] == "Direct Approved Card"
    assert "card_description" not in match["user_a_gives"]["photocard"]


def test_approved_card_participates_in_three_way_matches(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_a = login_named_user(client, "approve-three-a@example.com", "approve_three_a")
    user_b = login_named_user(client, "approve-three-b@example.com", "approve_three_b")
    user_c = login_named_user(client, "approve-three-c@example.com", "approve_three_c")
    pending = create_pending(client, user_a, "three-way approved")
    card_b = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": card["group_id"],
            "member_id": card["member_id"],
            "release_id": card["release_id"],
            "name": "Three B Card",
        },
        headers=admin_headers,
    ).json()
    card_c = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": card["group_id"],
            "member_id": card["member_id"],
            "release_id": card["release_id"],
            "name": "Three C Card",
        },
        headers=admin_headers,
    ).json()
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card_b["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card_b["id"], "condition_grade_id": grade["id"]},
        headers=user_b,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card_c["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_b,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card_c["id"], "condition_grade_id": grade["id"]},
        headers=user_c,
    )
    approve = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="Three Approved Card"),
        headers=admin_headers,
    )
    approved_id = approve.json()["approved_photocard_id"]
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": approved_id, "minimum_condition_grade_id": grade["id"]},
        headers=user_c,
    )

    response = client.get("/api/v1/matches/three-way", headers=user_a)

    assert response.status_code == 200
    assert len(response.json()) == 1
    match = response.json()[0]
    assert {edge["card"]["id"] for edge in match["trade_edges"]} == {
        approved_id,
        card_b["id"],
        card_c["id"],
    }
    assert all("card_description" not in edge["card"] for edge in match["trade_edges"])


def test_admin_can_merge_pending_photocard_into_existing_photocard(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-owner@example.com", "merge_owner")
    pending = create_pending(client, user_headers, "merge me")
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

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"], "reason": "same official card"},
        headers=admin_headers,
    )
    haves = client.get("/api/v1/me/cards/haves", headers=user_headers).json()
    wants = client.get("/api/v1/me/cards/wants", headers=user_headers).json()

    assert response.status_code == 200
    data = response.json()
    assert data["catalog_status"] == "merged"
    assert data["merged_photocard_id"] == card["id"]
    assert data["approved_photocard_id"] is None
    assert data["review_reason"] == "same official card"
    assert data["reviewed_by_admin_id"] is not None
    assert data["reviewed_at"] is not None
    assert len(haves) == 1
    assert haves[0]["photocard_id"] == card["id"]
    assert haves[0]["pending_photocard_id"] is None
    assert haves[0]["pending_photocard"] is None
    assert haves[0]["photocard"]["name"] == card["name"]
    assert len(wants) == 1
    assert wants[0]["photocard_id"] == card["id"]
    assert wants[0]["pending_photocard_id"] is None
    assert wants[0]["pending_photocard"] is None


def test_merge_pending_photocard_requires_login_and_admin(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-user@example.com", "merge_user")
    pending = create_pending(client, user_headers, "protected merge")

    unauthenticated = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
    )
    forbidden = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=user_headers,
    )

    assert unauthenticated.status_code == 401
    assert forbidden.status_code == 403


def test_merge_pending_photocard_returns_404_for_missing_ids(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-missing@example.com", "merge_missing")
    pending = create_pending(client, user_headers, "missing target")

    missing_pending = client.post(
        "/api/v1/admin/pending-photocards/999999/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    missing_target = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": 999999},
        headers=admin_headers,
    )

    assert missing_pending.status_code == 404
    assert missing_target.status_code == 404


def test_rejected_and_approved_pending_photocards_cannot_be_merged(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-terminal@example.com", "merge_terminal")
    rejected = create_pending(client, user_headers, "rejected merge")
    approved = create_pending(client, user_headers, "approved merge")
    client.post(
        f"/api/v1/admin/pending-photocards/{rejected['id']}/reject",
        json={"reason": "not this one"},
        headers=admin_headers,
    )
    client.post(
        f"/api/v1/admin/pending-photocards/{approved['id']}/approve",
        json=approval_payload(card, name="Already Approved For Merge Test"),
        headers=admin_headers,
    )

    rejected_merge = client.post(
        f"/api/v1/admin/pending-photocards/{rejected['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    approved_merge = client.post(
        f"/api/v1/admin/pending-photocards/{approved['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )

    assert rejected_merge.status_code == 409
    assert approved_merge.status_code == 409


def test_merged_pending_photocard_cannot_be_approved(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-then-approve@example.com", "merge_then_approve")
    pending = create_pending(client, user_headers, "merge then approve")
    client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/approve",
        json=approval_payload(card, name="Should Not Approve Merged"),
        headers=admin_headers,
    )

    assert response.status_code == 409


def test_merged_remerge_policy_matches_readme(client, admin_headers):
    card, _ = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-readme@example.com", "merge_readme")
    pending = create_pending(client, user_headers, "readme merge policy")

    first = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"], "reason": "first merge"},
        headers=admin_headers,
    )
    second = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"], "reason": "ignored merge"},
        headers=admin_headers,
    )

    with open("README.md", encoding="utf-8") as readme:
        readme_text = readme.read()

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["catalog_status"] == "merged"
    assert second.json()["merged_photocard_id"] == first.json()["merged_photocard_id"]
    assert second.json()["review_reason"] == "first merge"
    assert "이미 병합된 항목에 다시 요청하면 기존 병합 결과를 200으로 반환합니다" in readme_text


def test_merge_deletes_duplicate_pending_want(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-want-dup@example.com", "merge_want_dup")
    pending = create_pending(client, user_headers, "duplicate merge want")
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

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    wants = client.get("/api/v1/me/cards/wants", headers=user_headers).json()

    assert response.status_code == 200
    assert len(wants) == 1
    assert wants[0]["photocard_id"] == card["id"]
    assert wants[0]["pending_photocard_id"] is None


def test_merge_deletes_duplicate_pending_have_with_same_grade(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-have-dup@example.com", "merge_have_dup")
    pending = create_pending(client, user_headers, "duplicate merge have")
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

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    haves = client.get("/api/v1/me/cards/haves", headers=user_headers).json()

    assert response.status_code == 200
    assert len(haves) == 1
    assert haves[0]["photocard_id"] == card["id"]
    assert haves[0]["pending_photocard_id"] is None


def test_merge_keeps_have_with_different_grade(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    other_grade = client.post(
        "/api/v1/catalog/condition-grades",
        json={"code": "VG", "label": "Very Good", "sort_order": 20},
        headers=admin_headers,
    ).json()
    user_headers = login_named_user(client, "merge-have-grade@example.com", "merge_have_grade")
    pending = create_pending(client, user_headers, "different grade merge have")
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": other_grade["id"]},
        headers=user_headers,
    )

    response = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    haves = client.get("/api/v1/me/cards/haves", headers=user_headers).json()

    assert response.status_code == 200
    assert len(haves) == 2
    assert {have["photocard_id"] for have in haves} == {card["id"]}
    assert {have["condition_grade"]["code"] for have in haves} == {"NM", "VG"}
    assert all(have["pending_photocard_id"] is None for have in haves)


def test_merge_keeps_transfer_atomic_when_reference_transfer_fails(
    db, client, admin_headers, monkeypatch
):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-rollback@example.com", "merge_rollback")
    pending = create_pending(client, user_headers, "merge rollback")
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

    def fail_transfer(db, pending_id, photocard_id):
        raise RuntimeError("simulated merge transfer failure")

    monkeypatch.setattr(admin_api, "transfer_pending_card_references", fail_transfer)

    with pytest.raises(RuntimeError):
        client.post(
            f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
            json={"photocard_id": card["id"]},
            headers=admin_headers,
        )

    db.expire_all()
    pending_row = db.get(PendingPhotocard, pending["id"])
    have = db.scalar(select(UserHave).where(UserHave.pending_photocard_id == pending["id"]))
    want = db.scalar(select(UserWant).where(UserWant.pending_photocard_id == pending["id"]))

    assert pending_row.catalog_status == "pending"
    assert pending_row.merged_photocard_id is None
    assert have is not None
    assert have.photocard_id is None
    assert want is not None
    assert want.photocard_id is None


def test_merged_card_disappears_from_pending_badges_and_svg(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_headers = login_named_user(client, "merge-svg@example.com", "merge_svg")
    pending = create_pending(client, user_headers, "svg before merge")
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_headers,
    )

    before_svg = client.get("/api/v1/templates/me.svg", headers=user_headers)
    merge = client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    after_svg = client.get("/api/v1/templates/me.svg", headers=user_headers)
    haves = client.get("/api/v1/me/cards/haves", headers=user_headers).json()

    assert before_svg.status_code == 200
    assert "[임시 등록]" in before_svg.text
    assert merge.status_code == 200
    assert haves[0]["pending_photocard"] is None
    assert haves[0]["photocard"]["name"] == card["name"]
    assert after_svg.status_code == 200
    assert "[임시 등록]" not in after_svg.text
    assert "Bunny Beach" in after_svg.text


def test_merged_card_participates_in_direct_matches(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_a = login_named_user(client, "merge-direct-a@example.com", "merge_direct_a")
    user_b = login_named_user(client, "merge-direct-b@example.com", "merge_direct_b")
    pending = create_pending(client, user_a, "direct merged")
    other_card = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": card["group_id"],
            "member_id": card["member_id"],
            "release_id": card["release_id"],
            "name": "Merge Direct Other Card",
        },
        headers=admin_headers,
    ).json()
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": other_card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": other_card["id"], "condition_grade_id": grade["id"]},
        headers=user_b,
    )
    client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_b,
    )

    response = client.get("/api/v1/matches/direct", headers=user_a)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["user_a_gives"]["photocard"]["id"] == card["id"]


def test_merged_card_participates_in_three_way_matches(client, admin_headers):
    card, grade = seed_catalog(client, admin_headers)
    user_a = login_named_user(client, "merge-three-a@example.com", "merge_three_a")
    user_b = login_named_user(client, "merge-three-b@example.com", "merge_three_b")
    user_c = login_named_user(client, "merge-three-c@example.com", "merge_three_c")
    pending = create_pending(client, user_a, "three-way merged")
    card_b = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": card["group_id"],
            "member_id": card["member_id"],
            "release_id": card["release_id"],
            "name": "Merge Three B Card",
        },
        headers=admin_headers,
    ).json()
    card_c = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": card["group_id"],
            "member_id": card["member_id"],
            "release_id": card["release_id"],
            "name": "Merge Three C Card",
        },
        headers=admin_headers,
    ).json()
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card_b["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card_b["id"], "condition_grade_id": grade["id"]},
        headers=user_b,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card_c["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_b,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card_c["id"], "condition_grade_id": grade["id"]},
        headers=user_c,
    )
    client.post(
        f"/api/v1/admin/pending-photocards/{pending['id']}/merge",
        json={"photocard_id": card["id"]},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user_c,
    )

    response = client.get("/api/v1/matches/three-way", headers=user_a)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert {edge["card"]["id"] for edge in response.json()[0]["trade_edges"]} == {
        card["id"],
        card_b["id"],
        card_c["id"],
    }


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
