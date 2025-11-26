"""
Application configuration settings.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import MIN_SECRET_KEY_LENGTH


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Recipe Catalog API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    _TESTING: bool = False  # Internal flag - only enabled in non-production environments

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./recipes.db"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived for security with refresh tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # Long-lived for better UX

    # CORS
    ALLOWED_ORIGINS: str | list[str] = ["http://localhost:5173"]
    ALLOWED_METHODS: str | list[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    ALLOWED_HEADERS: str | list[str] = [
        "Authorization",
        "Content-Type",
        "Accept",
    ]

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@recipecatalog.app"
    FROM_NAME: str = "Recipe Catalog"

    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:5173"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str | list[str] = ["image/jpeg", "image/png", "image/webp"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # OAuth / Identity Providers
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback"

    # AI / OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    AI_RATE_LIMIT_PER_HOUR: int = 50

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, env_parse_none_str="null"
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("ALLOWED_METHODS", mode="before")
    @classmethod
    def parse_methods(cls, v) -> list[str]:
        if isinstance(v, str):
            return [method.strip() for method in v.split(",") if method.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("ALLOWED_IMAGE_TYPES", mode="before")
    @classmethod
    def parse_image_types(cls, v) -> list[str]:
        if isinstance(v, str):
            return [image_type.strip() for image_type in v.split(",") if image_type.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("ALLOWED_HEADERS", mode="before")
    @classmethod
    def parse_headers(cls, v) -> list[str]:
        if isinstance(v, str):
            return [header.strip() for header in v.split(",") if header.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate SECRET_KEY length."""
        if len(v) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters long (got {len(v)}). "
                "Generate a secure key with: openssl rand -hex 32"
            )
        return v

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v, info):
        """Validate CORS origins - prevent wildcard in production."""
        if info.data.get("ENVIRONMENT") == "production" and "*" in v:
            raise ValueError(
                "ALLOWED_ORIGINS cannot contain '*' in production. "
                "Specify explicit origins for security."
            )
        return v

    @property
    def TESTING(self) -> bool:  # noqa: N802
        """
        Testing flag that's only enabled in non-production environments.

        This prevents accidentally disabling security features (like rate limiting)
        in production even if the TESTING environment variable is set.
        """
        return self._TESTING and self.ENVIRONMENT != "production"

    @TESTING.setter
    def TESTING(self, value: bool) -> None:  # noqa: N802
        """Allow tests to set TESTING flag."""
        self._TESTING = value


# Create global settings instance
settings = Settings()
