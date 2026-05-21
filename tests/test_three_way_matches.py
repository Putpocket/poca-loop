from tests.test_direct_matches import login_named_user


def create_three_way_catalog(client, admin_headers):
    group = client.post(
        "/api/v1/catalog/groups",
        json={"name": "TWICE", "slug": "twice"},
        headers=admin_headers,
    ).json()
    member = client.post(
        "/api/v1/catalog/members",
        json={"group_id": group["id"], "name": "Nayeon"},
        headers=admin_headers,
    ).json()
    release = client.post(
        "/api/v1/catalog/releases",
        json={"group_id": group["id"], "title": "Ready To Be", "release_type": "album"},
        headers=admin_headers,
    ).json()

    cards = {}
    for name in ["A Card", "B Card", "C Card"]:
        cards[name] = client.post(
            "/api/v1/catalog/photocards",
            json={
                "group_id": group["id"],
                "member_id": member["id"],
                "release_id": release["id"],
                "name": name,
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
    return cards, grades


def create_three_way_cycle(
    client,
    admin_headers,
    a_grade="A",
    b_grade="A",
    c_grade="A",
    a_min="B",
    b_min="B",
    c_min="B",
):
    cards, grades = create_three_way_catalog(client, admin_headers)
    user_a = login_named_user(client, "three-a@example.com", "three_a")
    user_b = login_named_user(client, "three-b@example.com", "three_b")
    user_c = login_named_user(client, "three-c@example.com", "three_c")

    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": cards["A Card"]["id"], "condition_grade_id": grades[a_grade]["id"]},
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={
            "photocard_id": cards["B Card"]["id"],
            "minimum_condition_grade_id": grades[a_min]["id"],
        },
        headers=user_a,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": cards["B Card"]["id"], "condition_grade_id": grades[b_grade]["id"]},
        headers=user_b,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={
            "photocard_id": cards["C Card"]["id"],
            "minimum_condition_grade_id": grades[b_min]["id"],
        },
        headers=user_b,
    )
    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": cards["C Card"]["id"], "condition_grade_id": grades[c_grade]["id"]},
        headers=user_c,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={
            "photocard_id": cards["A Card"]["id"],
            "minimum_condition_grade_id": grades[c_min]["id"],
        },
        headers=user_c,
    )
    return user_a, user_b, user_c, cards, grades


def test_three_way_match_returns_normal_candidate(client, admin_headers):
    user_a, _, _, _, _ = create_three_way_cycle(client, admin_headers)

    response = client.get("/matches/three-way", headers=user_a)

    assert response.status_code == 200
    matches = response.json()
    assert len(matches) == 1
    assert matches[0]["match_type"] == "three_way"
    assert len(matches[0]["participants"]) == 3
    assert len(matches[0]["trade_edges"]) == 3
    assert all(edge["condition_passed"] is True for edge in matches[0]["trade_edges"])
    assert "generated_at" in matches[0]


def test_three_way_match_not_returned_for_broken_cycle(client, admin_headers):
    cards, grades = create_three_way_catalog(client, admin_headers)
    user_a = login_named_user(client, "broken-a@example.com", "broken_a")
    user_b = login_named_user(client, "broken-b@example.com", "broken_b")
    user_c = login_named_user(client, "broken-c@example.com", "broken_c")

    client.post("/api/v1/me/cards/haves", json={"photocard_id": cards["A Card"]["id"], "condition_grade_id": grades["A"]["id"]}, headers=user_a)
    client.post("/api/v1/me/cards/wants", json={"photocard_id": cards["B Card"]["id"], "minimum_condition_grade_id": grades["B"]["id"]}, headers=user_a)
    client.post("/api/v1/me/cards/haves", json={"photocard_id": cards["B Card"]["id"], "condition_grade_id": grades["A"]["id"]}, headers=user_b)
    client.post("/api/v1/me/cards/wants", json={"photocard_id": cards["C Card"]["id"], "minimum_condition_grade_id": grades["B"]["id"]}, headers=user_b)
    client.post("/api/v1/me/cards/haves", json={"photocard_id": cards["C Card"]["id"], "condition_grade_id": grades["A"]["id"]}, headers=user_c)

    response = client.get("/matches/three-way", headers=user_a)

    assert response.status_code == 200
    assert response.json() == []


def test_three_way_match_not_returned_when_condition_grade_is_too_low(client, admin_headers):
    user_a, _, _, _, _ = create_three_way_cycle(client, admin_headers, b_grade="D", a_min="C")

    response = client.get("/matches/three-way", headers=user_a)

    assert response.status_code == 200
    assert response.json() == []


def test_three_way_d_grade_requires_explicit_d_minimum(client, admin_headers):
    user_a, _, _, _, _ = create_three_way_cycle(
        client,
        admin_headers,
        a_grade="D",
        b_grade="D",
        c_grade="D",
        a_min="D",
        b_min="D",
        c_min="D",
    )

    response = client.get("/matches/three-way", headers=user_a)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_three_way_match_deduplicates_rotations(client, admin_headers):
    user_a, user_b, user_c, _, _ = create_three_way_cycle(client, admin_headers)

    a_response = client.get("/matches/three-way", headers=user_a)
    b_response = client.get("/matches/three-way", headers=user_b)
    c_response = client.get("/matches/three-way", headers=user_c)

    assert len(a_response.json()) == 1
    a_edges = [
        (edge["giver"]["username"], edge["receiver"]["username"], edge["card"]["name"])
        for edge in a_response.json()[0]["trade_edges"]
    ]
    for response in [b_response, c_response]:
        edges = [
            (edge["giver"]["username"], edge["receiver"]["username"], edge["card"]["name"])
            for edge in response.json()[0]["trade_edges"]
        ]
        assert edges == a_edges


def test_three_way_match_never_matches_self(client, admin_headers):
    cards, grades = create_three_way_catalog(client, admin_headers)
    user_a = login_named_user(client, "self-three@example.com", "self_three")

    for card_name in ["A Card", "B Card", "C Card"]:
        client.post(
            "/api/v1/me/cards/haves",
            json={"photocard_id": cards[card_name]["id"], "condition_grade_id": grades["A"]["id"]},
            headers=user_a,
        )
    client.post("/api/v1/me/cards/wants", json={"photocard_id": cards["B Card"]["id"], "minimum_condition_grade_id": grades["B"]["id"]}, headers=user_a)
    client.post("/api/v1/me/cards/wants", json={"photocard_id": cards["C Card"]["id"], "minimum_condition_grade_id": grades["B"]["id"]}, headers=user_a)

    response = client.get("/matches/three-way", headers=user_a)

    assert response.status_code == 200
    assert response.json() == []


def test_three_way_match_requires_login(client):
    response = client.get("/matches/three-way")
    assert response.status_code == 401


def test_logged_in_user_sees_only_own_three_way_matches(client, admin_headers):
    user_a, _, _, _, _ = create_three_way_cycle(client, admin_headers)
    outsider = login_named_user(client, "three-outsider@example.com", "three_outsider")

    own_response = client.get("/matches/three-way", headers=user_a)
    outsider_response = client.get("/matches/three-way", headers=outsider)

    assert len(own_response.json()) == 1
    assert outsider_response.status_code == 200
    assert outsider_response.json() == []


def test_three_way_match_response_does_not_expose_sensitive_user_fields(client, admin_headers):
    user_a, _, _, _, _ = create_three_way_cycle(client, admin_headers)

    response = client.get("/matches/three-way", headers=user_a)

    assert response.status_code == 200
    match = response.json()[0]
    for user_payload in match["participants"]:
        assert set(user_payload) == {"id", "username"}
    for edge in match["trade_edges"]:
        for user_key in ("giver", "receiver"):
            assert set(edge[user_key]) == {"id", "username"}
            assert "email" not in edge[user_key]
            assert "hashed_password" not in edge[user_key]
            assert "is_admin" not in edge[user_key]
            assert "role" not in edge[user_key]
            assert "is_active" not in edge[user_key]


def test_three_way_match_limit_defaults_and_validation(client, admin_headers):
    user_a, _, _, _, _ = create_three_way_cycle(client, admin_headers)

    default_response = client.get("/matches/three-way", headers=user_a)
    max_response = client.get("/matches/three-way?limit=100", headers=user_a)
    too_large_response = client.get("/matches/three-way?limit=101", headers=user_a)
    invalid_response = client.get("/matches/three-way?limit=0", headers=user_a)

    assert default_response.status_code == 200
    assert len(default_response.json()) <= 50
    assert max_response.status_code == 200
    assert too_large_response.status_code == 422
    assert invalid_response.status_code == 422
