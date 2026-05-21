from pathlib import Path


def test_gitignore_covers_local_and_generated_files():
    gitignore = Path(".gitignore").read_text()
    required_patterns = [
        ".env",
        ".env.*",
        "!.env.example",
        ".venv/",
        "__pycache__/",
        "*.pyc",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        "htmlcov/",
        "dist/",
        "build/",
    ]

    for pattern in required_patterns:
        assert pattern in gitignore


def test_no_local_env_or_database_files_in_project_root():
    forbidden_names = {".env"}
    forbidden_suffixes = {".db", ".sqlite", ".sqlite3"}

    for path in Path(".").glob("*"):
        assert path.name not in forbidden_names
        assert path.suffix not in forbidden_suffixes


def test_auth_responses_do_not_expose_internal_user_fields(client):
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "public@example.com", "username": "public_user", "password": "safe-password"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "public@example.com", "password": "safe-password"},
    )
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert signup.status_code == 201
    assert me.status_code == 200
    for payload in [signup.json(), me.json()]:
        assert set(payload) == {"id", "username"}
        assert "email" not in payload
        assert "hashed_password" not in payload
        assert "is_admin" not in payload
        assert "role" not in payload
        assert "is_active" not in payload
