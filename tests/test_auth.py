def test_signup_login_and_me(client):
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "fan@example.com", "username": "fan_1", "password": "safe-password"},
    )
    assert signup.status_code == 201
    assert signup.json()["username"] == "fan_1"
    assert "email" not in signup.json()
    assert "hashed_password" not in signup.json()
    assert "role" not in signup.json()
    assert "is_active" not in signup.json()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "fan@example.com", "password": "safe-password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "fan_1"


def test_health_check_success(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_catalog_write_requires_auth_or_admin(client):
    unauthenticated = client.post("/api/v1/catalog/groups", json={"name": "IVE", "slug": "ive"})
    assert unauthenticated.status_code == 401

    client.post(
        "/api/v1/auth/signup",
        json={"email": "fan2@example.com", "username": "fan_2", "password": "safe-password"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "fan2@example.com", "password": "safe-password"},
    )
    forbidden = client.post(
        "/api/v1/catalog/groups",
        json={"name": "IVE", "slug": "ive"},
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert forbidden.status_code == 403
