"""
Application configuration using Pydantic Settings.
Loads values from .env file with sensible defaults.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Finance Dashboard API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database — use /tmp on Vercel (read-only filesystem except /tmp)
    DATABASE_URL: str = (
        "sqlite+aiosqlite:////tmp/finance_dashboard.db"
        if os.environ.get("VERCEL")
        else "sqlite+aiosqlite:///./finance_dashboard.db"
    )

    # JWT
    SECRET_KEY: str = "finance-dashboard-dev-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Default Admin
    DEFAULT_ADMIN_EMAIL: str = "admin@financedash.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    AUTH_RATE_LIMIT_PER_MINUTE: int = 20

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
