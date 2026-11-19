import json
import os
from pathlib import Path
import socket
from typing import Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _resolve_default_db_url() -> str:
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return _normalize_db_url(env_url)
    # If postgresql port 5432 is not accepting connections, use local SQLite database for zero-config dev
    try:
        with socket.create_connection(("localhost", 5432), timeout=0.5):
            return "postgresql+asyncpg://coglearn:coglearn_dev_password@localhost:5432/coglearn"
    except OSError:
        db_path = Path(__file__).resolve().parent.parent.parent / "coglearn.db"
        return f"sqlite+aiosqlite:///{db_path.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core environment
    ENVIRONMENT: str = Field(default="development")
    APP_NAME: str = Field(default="COGLEARN API")
    MIN_COHORT_SIZE: int = Field(default=5)

    # Database
    DATABASE_URL: str = Field(default_factory=_resolve_default_db_url)

    # Redis & Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")

    # Security & JWT (RS256)
    SECRET_KEY: str = Field(
        default="development_secret_key_change_in_production_32bytesmin"
    )
    JWT_ALGORITHM: str = Field(default="RS256")
    JWT_PRIVATE_KEY: str = Field(default="")
    JWT_PUBLIC_KEY: str = Field(default="")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # Platform Admin credentials
    PLATFORM_ADMIN_EMAIL: str = Field(default="admin@coglearn.internal")
    PLATFORM_ADMIN_PASSWORD: str = Field(default="AdminSecurePassword123!")

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:8000"]
    )

    # Storage settings
    STORAGE_BACKEND: str = Field(default="local")
    STORAGE_LOCAL_PATH: str = Field(default="/app/uploads")

    # SMTP / Email settings
    SMTP_HOST: str | None = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str | None = Field(default=None)
    SMTP_PASSWORD: str | None = Field(default=None)
    SMTP_FROM_EMAIL: str = Field(default="notifications@coglearn.internal")
    SMTP_FROM_NAME: str = Field(default="COGLEARN Platform")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Any) -> str:
        if isinstance(v, str):
            return _normalize_db_url(v)
        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return v

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def backend_cors_origins(self) -> list[str]:
        return self.BACKEND_CORS_ORIGINS

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND

    @property
    def jwt_private_key(self) -> str:
        return self.JWT_PRIVATE_KEY.replace("\\n", "\n")

    @property
    def jwt_public_key(self) -> str:
        return self.JWT_PUBLIC_KEY.replace("\\n", "\n")


settings = Settings()
