import logging
from collections import defaultdict, deque
from threading import Lock
from time import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from ...api.dependencies.auth import get_current_claims
from ...core.config import get_settings
from ...core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

router = APIRouter()
logger = logging.getLogger("backend.auth")


class LoginRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, window_seconds: int, max_attempts: int) -> tuple[bool, int]:
        now = time()

        with self._lock:
            attempts = self._attempts[key]
            cutoff = now - max(1, window_seconds)
            while attempts and attempts[0] < cutoff:
                attempts.popleft()

            if len(attempts) >= max_attempts:
                retry_after = int(max(1, window_seconds - (now - attempts[0])))
                return False, retry_after

            attempts.append(now)
            return True, 0

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)


_login_rate_limiter = LoginRateLimiter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    if forwarded_for:
        return forwarded_for
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request) -> TokenResponse:
    settings = get_settings()
    client_id = _client_identifier(request)

    allowed, retry_after = _login_rate_limiter.check(
        key=client_id,
        window_seconds=settings.login_rate_limit_window_seconds,
        max_attempts=settings.login_rate_limit_max_attempts,
    )
    if not allowed:
        logger.warning("Login rate limit exceeded for client=%s", client_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {retry_after} seconds.",
        )

    if payload.email != settings.bootstrap_admin_email or payload.password != settings.bootstrap_admin_password:
        logger.warning("Login failed for email=%s client=%s", payload.email, client_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    _login_rate_limiter.reset(client_id)
    logger.info("Login successful for email=%s client=%s", payload.email, client_id)

    return TokenResponse(
        access_token=create_access_token(payload.email, settings.bootstrap_admin_role),
        refresh_token=create_refresh_token(payload.email, settings.bootstrap_admin_role),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest) -> TokenResponse:
    if not payload.refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token is required")

    settings = get_settings()
    try:
        claims = decode_refresh_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    subject = str(claims.get("sub", ""))
    role = str(claims.get("role", settings.bootstrap_admin_role))
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token subject")

    return TokenResponse(
        access_token=create_access_token(subject, role),
        refresh_token=create_refresh_token(subject, role),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout")
def logout() -> dict:
    return {"status": "ok", "message": "Logged out"}


@router.get("/me")
def me(claims: dict = Depends(get_current_claims)) -> dict:
    return {
        "email": claims.get("sub"),
        "role": claims.get("role", "viewer"),
        "token_type": claims.get("type"),
    }
