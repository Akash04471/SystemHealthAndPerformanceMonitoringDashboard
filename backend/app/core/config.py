from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = "/api/v1"
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    db_host: str = Field(default="127.0.0.1", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_user: str = Field(default="", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_name: str = Field(default="system_monitoring", alias="DB_NAME")

    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="REDIS_URL")

    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    jwt_refresh_secret: str = Field(default="", alias="JWT_REFRESH_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    bootstrap_admin_email: str = Field(default="admin@example.com", alias="BOOTSTRAP_ADMIN_EMAIL")
    bootstrap_admin_password: str = Field(default="admin123", alias="BOOTSTRAP_ADMIN_PASSWORD")
    bootstrap_admin_role: str = Field(default="admin", alias="BOOTSTRAP_ADMIN_ROLE")

    zscore_threshold: float = Field(default=1.5, alias="ZSCORE_THRESHOLD")
    zscore_window_size: int = Field(default=30, alias="ZSCORE_WINDOW_SIZE")
    zscore_min_points: int = Field(default=10, alias="ZSCORE_MIN_POINTS")
    alert_cooldown_minutes: int = Field(default=15, alias="ALERT_COOLDOWN_MINUTES")
    cors_origins: str = Field(default="http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://localhost:5173,http://localhost:5174,http://localhost:5175", alias="CORS_ORIGINS")
    strict_cors_in_non_dev: bool = Field(default=True, alias="STRICT_CORS_IN_NON_DEV")

    login_rate_limit_window_seconds: int = Field(default=60, alias="LOGIN_RATE_LIMIT_WINDOW_SECONDS")
    login_rate_limit_max_attempts: int = Field(default=5, alias="LOGIN_RATE_LIMIT_MAX_ATTEMPTS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
