from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from ...api.dependencies.auth import get_current_claims
from ...core.config import get_settings
from ...core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

router = APIRouter()


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


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    settings = get_settings()
    if payload.email != settings.bootstrap_admin_email or payload.password != settings.bootstrap_admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

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
