from tests.test_direct_matches import login_named_user


def create_svg_catalog(
    client,
    admin_headers,
    group_name="IVE",
    member_name="Wonyoung",
    card_name="Lucky",
    grade_code="A",
):
    group = client.post(
        "/api/v1/catalog/groups",
        json={"name": group_name, "slug": f"svg-{abs(hash(group_name)) % 100000}"},
        headers=admin_headers,
    ).json()
    member = client.post(
        "/api/v1/catalog/members",
        json={"group_id": group["id"], "name": member_name},
        headers=admin_headers,
    ).json()
    release = client.post(
        "/api/v1/catalog/releases",
        json={"group_id": group["id"], "title": "After Like", "release_type": "album"},
        headers=admin_headers,
    ).json()
    card = client.post(
        "/api/v1/catalog/photocards",
        json={
            "group_id": group["id"],
            "member_id": member["id"],
            "release_id": release["id"],
            "name": card_name,
        },
        headers=admin_headers,
    ).json()
    grade = client.post(
        "/api/v1/catalog/condition-grades",
        json={"code": grade_code, "label": grade_code, "sort_order": 10},
        headers=admin_headers,
    ).json()
    return card, grade


def test_template_svg_requires_login(client):
    response = client.get("/templates/me.svg")
    assert response.status_code == 401


def test_logged_in_user_can_get_svg_with_own_have_and_want(client, admin_headers):
    card, grade = create_svg_catalog(client, admin_headers)
    user = login_named_user(client, "svg@example.com", "svg_user")

    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"], "note": "corner ding"},
        headers=user,
    )
    client.post(
        "/api/v1/me/cards/wants",
        json={"photocard_id": card["id"], "minimum_condition_grade_id": grade["id"]},
        headers=user,
    )

    response = client.get("/templates/me.svg", headers=user)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert "private" in response.headers["cache-control"]
    svg = response.text
    assert "poca-loop" in svg
    assert "svg_user" in svg
    assert "HAVE" in svg
    assert "WANT" in svg
    assert "IVE / Wonyoung / After Like / Lucky" in svg
    assert "grade A / corner ding" in svg
    assert "min grade A" in svg


def test_template_svg_does_not_include_other_users_cards(client, admin_headers):
    card, grade = create_svg_catalog(client, admin_headers)
    user_a = login_named_user(client, "svg-a@example.com", "svg_a")
    user_b = login_named_user(client, "svg-b@example.com", "svg_b")

    client.post(
        "/api/v1/me/cards/haves",
        json={"photocard_id": card["id"], "condition_grade_id": grade["id"], "note": "private-other"},
        headers=user_b,
    )

    response = client.get("/templates/me.svg", headers=user_a)

    assert response.status_code == 200
    assert "private-other" not in response.text


def test_template_svg_does_not_expose_sensitive_user_fields(client, admin_headers):
    user = login_named_user(client, "sensitive@example.com", "safe_svg")

    response = client.get("/templates/me.svg", headers=user)

    assert response.status_code == 200
    svg = response.text
    assert "sensitive@example.com" not in svg
    assert "hashed_password" not in svg
    assert "is_admin" not in svg
    assert "role" not in svg
    assert "is_active" not in svg


def test_template_svg_height_contains_empty_have_and_want_sections(client, admin_headers):
    user = login_named_user(client, "empty-svg@example.com", "empty_svg")

    response = client.get("/templates/me.svg", headers=user)

    assert response.status_code == 200
    svg = response.text
    assert 'height="310"' in svg
    assert 'viewBox="0 0 980 310"' in svg
    assert 'height="274"' in svg
    assert "No have cards yet" in svg
    assert "No want cards yet" in svg


def test_template_svg_escapes_special_characters_and_avoids_active_content(client, admin_headers):
    card, grade = create_svg_catalog(
        client,
        admin_headers,
        group_name="IVE <script>",
        member_name='Won"young',
        card_name="<script>alert(1)</script>",
    )
    user = login_named_user(client, "escape@example.com", "escape_user")
    client.post(
        "/api/v1/me/cards/haves",
        json={
            "photocard_id": card["id"],
            "condition_grade_id": grade["id"],
            "note": '<foreignObject onload="bad()">',
        },
        headers=user,
    )

    response = client.get("/templates/me.svg", headers=user)

    assert response.status_code == 200
    svg = response.text
    assert "&lt;script&gt;" in svg
    assert "&quot;" in svg
    assert "&lt;foreignObject onload&#61;&quot;bad()&quot;&gt;" in svg
    assert "<script" not in svg
    assert "<foreignObject" not in svg
    assert "onload=" not in svg
    assert "onclick=" not in svg


def test_template_svg_shows_and_more_when_items_exceed_limit(client, admin_headers):
    user = login_named_user(client, "many@example.com", "many_svg")
    grade = None
    for index in range(51):
        card, grade = create_svg_catalog(
            client,
            admin_headers,
            group_name=f"Group {index}",
            member_name="Member",
            card_name=f"Card {index}",
            grade_code=f"A{index}",
        )
        client.post(
            "/api/v1/me/cards/haves",
            json={"photocard_id": card["id"], "condition_grade_id": grade["id"]},
            headers=user,
        )

    response = client.get("/templates/me.svg", headers=user)

    assert response.status_code == 200
    assert "and more..." in response.text


def test_template_svg_uses_natural_pending_photocard_label(client, admin_headers):
    _, grade = create_svg_catalog(client, admin_headers)
    user = login_named_user(client, "svg-pending@example.com", "svg_pending")
    pending = client.post(
        "/api/v1/catalog/pending-photocards",
        json={
            "group_name": "NMIXX",
            "member_name": "Haewon",
            "source_type": "popup",
            "source_title": "Fe3O4: BREAK POP-UP STORE",
            "card_description": "random benefit card",
        },
        headers=user,
    ).json()
    client.post(
        "/api/v1/me/cards/haves",
        json={"pending_photocard_id": pending["id"], "condition_grade_id": grade["id"]},
        headers=user,
    )

    response = client.get("/templates/me.svg", headers=user)

    assert response.status_code == 200
    assert "NMIXX / Haewon / Fe3O4: BREAK POP-UP STORE / random benefit card [임시 등록]" in response.text
    assert "[pending]" not in response.text
