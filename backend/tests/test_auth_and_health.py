def test_health_live(client):
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers.get("X-Request-ID")


def test_login_success_returns_tokens(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] > 0
    assert payload["access_token"]
    assert payload["refresh_token"]


def test_login_invalid_credentials_returns_401(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_token_success(client):
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["refresh_token"]


def test_me_requires_authorization_header(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header required"


def test_me_returns_claims_with_valid_access_token(client):
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "admin@example.com"
    assert payload["role"] == "admin"
    assert payload["token_type"] == "access"


def test_login_rate_limit_returns_429_after_max_attempts(client, monkeypatch):
    monkeypatch.setenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "2")

    from backend.app.core.config import get_settings
    from backend.app.api.routes import auth as auth_routes

    get_settings.cache_clear()
    auth_routes._login_rate_limiter = auth_routes.LoginRateLimiter()

    first = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )
    second = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )
    third = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )

    assert first.status_code == 401
    assert second.status_code == 401
    assert third.status_code == 429
    assert "Too many login attempts" in third.json()["detail"]

    get_settings.cache_clear()
