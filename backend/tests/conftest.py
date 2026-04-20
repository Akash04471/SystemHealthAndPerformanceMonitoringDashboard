import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "admin123")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_ROLE", "admin")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "5")

    from backend.app.core.config import get_settings

    get_settings.cache_clear()

    import backend.app.main as main_module
    from backend.app.api.routes import auth as auth_routes

    importlib.reload(main_module)
    auth_routes._login_rate_limiter = auth_routes.LoginRateLimiter()

    with TestClient(main_module.app) as test_client:
        yield test_client

    get_settings.cache_clear()


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
