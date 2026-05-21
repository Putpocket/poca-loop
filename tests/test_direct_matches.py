def login_named_user(client, email: str, username: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "username": username, "password": "safe-password"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "safe-password"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_direct_match_catalog(client, admin_headers):
    group = client.post(
        "/api/v1/catalog/groups",
        json={"name": "IVE", "slug": "ive"},
        headers=admin_headers,
    ).json()
    member = client.post(
        "/api/v1/catalog/members",
        json={"group_id": group["id"], "name": "Wonyoung"},
        headers=admin_headers,
    ).json()
    release = client.post(
        "/api/v1/catalog/releases",
        json={"group_id": group["id"], "title": "I AM", "release_type": "album"},
        headers=admin_headers,
    ).json()
    card_x = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": group["id"],
            "member_id": member["id"],
            "release_id": release["id"],
            "name": "Card X",
            "version": "A",
        },
        headers=admin_headers,
    ).json()
    card_y = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": group["id"],
            "member_id": member["id"],
            "release_id": release["id"],
            "name": "Card Y",
            "version": "B",
        },
        headers=admin_headers,
    ).json()

    grades = {}
    for index, code in enumerate(["S", "A", "B", "C", "D"], start=1):
        grades[code] = client.post(
            "/api/v1/catalog/condition-grades",
            json={"code": code, "label": code, "sort_order": index * 10},
            headers=admin_headers,
        ).json()
    return card_x, card_y, grades


def create_direct_match_pair(client, admin_headers, a_x_grade="A", b_y_grade="A", b_min_x="B", a_min_y="B"):
    card_x, card_y, grades = create_direct_match_catalog(client, admin_headers)
    user_a = login_named_user(client, "a@example.com", "collector_a")
    user_b = login_named_user(client, "b@example.com", "collector_b")

    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card_x["id"], "condition_grade_id": grades[a_x_grade]["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card_y["id"], "minimum_condition_grade_id": grades[a_min_y]["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card_y["id"], "condition_grade_id": grades[b_y_grade]["id"]},
        headers=user_b,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card_x["id"], "minimum_condition_grade_id": grades[b_min_x]["id"]},
        headers=user_b,
    )
    return user_a, user_b, card_x, card_y, grades


def test_direct_match_returns_normal_candidate(client, admin_headers):
    user_a, _, card_x, card_y, _ = create_direct_match_pair(client, admin_headers)

    response = client.get("/api/v1/matches/direct", headers=user_a)

    assert response.status_code == 200
    matches = response.json()
    assert len(matches) == 1
    match = matches[0]
    assert match["match_type"] == "direct"
    assert match["user_a_gives"]["photocard"]["id"] == card_x["id"]
    assert match["user_a_receives"]["photocard"]["id"] == card_y["id"]
    assert match["condition_check"]["user_a_give_meets_user_b_minimum"] is True
    assert match["condition_check"]["user_b_give_meets_user_a_minimum"] is True
    assert "generated_at" in match


def test_direct_match_not_returned_when_condition_grade_is_too_low(client, admin_headers):
    user_a, _, _, _, _ = create_direct_match_pair(
        client,
        admin_headers,
        a_x_grade="D",
        b_y_grade="A",
        b_min_x="C",
        a_min_y="B",
    )

    response = client.get("/api/v1/matches/direct", headers=user_a)

    assert response.status_code == 200
    assert response.json() == []


def test_direct_match_d_grade_requires_explicit_d_minimum(client, admin_headers):
    user_a, _, _, _, _ = create_direct_match_pair(
        client,
        admin_headers,
        a_x_grade="D",
        b_y_grade="D",
        b_min_x="D",
        a_min_y="D",
    )

    response = client.get("/matches/direct", headers=user_a)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_direct_match_never_matches_self(client, admin_headers):
    card_x, card_y, grades = create_direct_match_catalog(client, admin_headers)
    user_a = login_named_user(client, "self@example.com", "self_collector")

    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card_x["id"], "condition_grade_id": grades["A"]["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card_y["id"], "minimum_condition_grade_id": grades["B"]["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card_y["id"], "condition_grade_id": grades["A"]["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card_x["id"], "minimum_condition_grade_id": grades["B"]["id"]},
        headers=user_a,
    )

    response = client.get("/api/v1/matches/direct", headers=user_a)

    assert response.status_code == 200
    assert response.json() == []


def test_direct_match_deduplicates_a_b_and_b_a(client, admin_headers):
    user_a, _, _, _, grades = create_direct_match_pair(client, admin_headers)

    card_z = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": 1,
            "member_id": 1,
            "release_id": 1,
            "name": "Unrelated Card",
            "version": "Z",
        },
        headers=admin_headers,
    )
    assert card_z.status_code == 201

    duplicate = client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": 1, "condition_grade_id": grades["S"]["id"]},
        headers=user_a,
    )
    assert duplicate.status_code == 201

    response = client.get("/api/v1/matches/direct", headers=user_a)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_direct_match_requires_login(client):
    response = client.get("/matches/direct")
    assert response.status_code == 401


def test_logged_in_user_can_query_own_direct_matches(client, admin_headers):
    user_a, _, _, _, _ = create_direct_match_pair(client, admin_headers)

    response = client.get("/matches/direct", headers=user_a)

    assert response.status_code == 200
    assert response.json()[0]["user_a"]["username"] == "collector_a"


def test_direct_match_only_returns_matches_involving_current_user(client, admin_headers):
    create_direct_match_pair(client, admin_headers)
    outsider = login_named_user(client, "outsider@example.com", "outsider")

    response = client.get("/matches/direct", headers=outsider)

    assert response.status_code == 200
    assert response.json() == []


def test_direct_match_response_does_not_expose_sensitive_user_fields(client, admin_headers):
    user_a, _, _, _, _ = create_direct_match_pair(client, admin_headers)

    response = client.get("/matches/direct", headers=user_a)

    assert response.status_code == 200
    match = response.json()[0]
    for user_key in ("user_a", "user_b"):
        assert set(match[user_key]) == {"id", "username"}
        assert "email" not in match[user_key]
        assert "hashed_password" not in match[user_key]
        assert "is_admin" not in match[user_key]
        assert "role" not in match[user_key]
        assert "is_active" not in match[user_key]


def test_direct_match_limit_defaults_and_validation(client, admin_headers):
    user_a, _, _, _, _ = create_direct_match_pair(client, admin_headers)

    default_response = client.get("/matches/direct", headers=user_a)
    max_response = client.get("/matches/direct?limit=100", headers=user_a)
    too_large_response = client.get("/matches/direct?limit=101", headers=user_a)
    invalid_response = client.get("/matches/direct?limit=0", headers=user_a)

    assert default_response.status_code == 200
    assert len(default_response.json()) <= 50
    assert max_response.status_code == 200
    assert too_large_response.status_code == 422
    assert invalid_response.status_code == 422
