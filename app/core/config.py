import json
import logging
from pathlib import Path
from typing import List, Union, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("uvicorn")

# Dynamically locate root project directory (where .env lives)
# app/core/config.py -> app/core/ -> app/ -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "AuraWardrobe Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database Configuration
    DATABASE_URL: Optional[str] = None
    ASYNC_DATABASE_URL: Optional[str] = None

    # External Service API Keys
    GEMINI_API_KEY: str = ""
    WEATHER_API_KEY: str = ""

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Security & JWT Token Config
    SECRET_KEY: str = "23ed5f07340b7de7df2dacb3e7128f6d6974058bc2968e1e80f76a0b60e27213"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v

    @model_validator(mode="after")
    def validate_and_assemble_settings(self) -> "Settings":
        """Assemble Async DB URL and verify crucial API keys."""

        # 1. Database URL Auto-assembly
        if not self.ASYNC_DATABASE_URL and self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self.ASYNC_DATABASE_URL = url
        elif not self.DATABASE_URL and self.ASYNC_DATABASE_URL:
            self.DATABASE_URL = self.ASYNC_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

        # 2. Check for missing Weather API key
        if not self.WEATHER_API_KEY.strip():
            logger.warning(
                "⚠️ WEATHER_API_KEY is empty! Weather Service will return fallback data (25°C)."
            )

        return self

    model_config = SettingsConfigDict(
        env_file=(str(ENV_FILE_PATH), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,  # Accepts WEATHER_API_KEY or weather_api_key
        extra="ignore",
    )


settings = Settings()