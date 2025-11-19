"""
Application configuration settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Recipe Catalog API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    TESTING: bool = False  # Set to True to disable rate limiting for tests

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./recipes.db"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = (
        15  # Short-lived for security with refresh tokens
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # Long-lived for better UX

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
    ALLOWED_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    ALLOWED_HEADERS: list[str] = [
        "Authorization",
        "Content-Type",
        "Accept",
        "X-CSRF-Token",
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
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

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
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_METHODS", mode="before")
    @classmethod
    def parse_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @field_validator("ALLOWED_IMAGE_TYPES", mode="before")
    @classmethod
    def parse_image_types(cls, v):
        if isinstance(v, str):
            return [image_type.strip() for image_type in v.split(",")]
        return v

    @field_validator("ALLOWED_HEADERS", mode="before")
    @classmethod
    def parse_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v, info):
        """Validate SECRET_KEY strength in production."""
        # Known weak/default keys to reject
        weak_keys = {
            "secret",
            "changeme",
            "default",
            "test",
            "password",
            "secret_key",
            "your-secret-key",
            "dev-secret-key",
        }

        # Check minimum length
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters long (got {len(v)}). "
                "Generate a secure key with: openssl rand -hex 32"
            )

        # Get environment from info context if available
        environment = info.data.get("ENVIRONMENT", "production")

        # In production, reject weak keys
        if environment == "production" and v.lower() in weak_keys:
            raise ValueError(
                f"SECRET_KEY appears to be a weak/default value. "
                "Generate a secure key with: openssl rand -hex 32"
            )

        return v


# Create global settings instance
settings = Settings()
