"""
Application configuration settings.
"""

import os

from pydantic import field_validator, model_validator
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

    # PDF / Font configuration
    # Comma-separated list or list of preferred Unicode font filenames to look for in app assets/fonts
    PDF_UNICODE_FONTS: str | list[str] = ["NotoSans-Regular.ttf", "Roboto-Regular.ttf"]

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
    # Base URL of the auth API. The provider callback path -- "/{provider}/callback"
    # -- is appended to this, so it must NOT include the callback segment itself.
    OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8000/api/v1/auth"

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
        """Normalize ALLOWED_ORIGINS to a list.

        Accepts either a comma-separated string or a list and returns a list of
        origin strings with whitespace trimmed.
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("ALLOWED_METHODS", mode="before")
    @classmethod
    def parse_methods(cls, v) -> list[str]:
        """Normalize ALLOWED_METHODS to a list of HTTP methods.

        Accepts a comma-separated string or a list and returns a cleaned list of
        HTTP method names (e.g., "GET", "POST").
        """
        if isinstance(v, str):
            return [method.strip() for method in v.split(",") if method.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("ALLOWED_IMAGE_TYPES", mode="before")
    @classmethod
    def parse_image_types(cls, v) -> list[str]:
        """Normalize ALLOWED_IMAGE_TYPES to a list of MIME types.

        Accepts either a comma-separated string or a list and returns a list of
        MIME type strings with whitespace trimmed.
        """
        if isinstance(v, str):
            return [image_type.strip() for image_type in v.split(",") if image_type.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("ALLOWED_HEADERS", mode="before")
    @classmethod
    def parse_headers(cls, v) -> list[str]:
        """Normalize ALLOWED_HEADERS to a list of header names.

        Accepts a comma-separated string or a list and returns trimmed header
        strings suitable for use in CORS configuration.
        """
        if isinstance(v, str):
            return [header.strip() for header in v.split(",") if header.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("PDF_UNICODE_FONTS", mode="before")
    @classmethod
    def parse_unicode_fonts(cls, v) -> list[str]:
        """Normalize PDF_UNICODE_FONTS to a list of font filenames.

        Allows configuration to be provided as a comma-separated string or a list
        and returns a cleaned list of font file names to search for in
        `app/assets/fonts/`.
        """
        if isinstance(v, str):
            return [font.strip() for font in v.split(",") if font.strip()]
        return v if isinstance(v, list) else [v]

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate the SECRET_KEY length.

        Ensures SECRET_KEY meets the minimum required length and raises a
        ValueError with guidance if it does not.
        """
        if len(v) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters long (got {len(v)}). "
                "Generate a secure key with: openssl rand -hex 32"
            )
        return v

    @field_validator("OAUTH_REDIRECT_BASE_URL")
    @classmethod
    def validate_oauth_redirect_base_url(cls, v: str) -> str:
        """Reject values that already include the callback path."""
        normalized = v.rstrip("/")
        if normalized.endswith("/callback"):
            raise ValueError(
                "OAUTH_REDIRECT_BASE_URL must be the auth API base URL "
                "(e.g. http://localhost:8000/api/v1/auth). The '/{provider}/callback' "
                "path is appended automatically."
            )
        return normalized

    @model_validator(mode="after")
    def reject_legacy_oauth_redirect_uri(self) -> "Settings":
        """
        Fail loudly if the removed OAUTH_REDIRECT_URI is still set.

        Its value pointed at a route that never existed, so silently ignoring it
        would leave OAuth broken with no indication why.
        """
        if os.environ.get("OAUTH_REDIRECT_URI"):
            raise ValueError(
                "OAUTH_REDIRECT_URI has been replaced by OAUTH_REDIRECT_BASE_URL. "
                "Set OAUTH_REDIRECT_BASE_URL to the auth API base URL "
                "(e.g. https://your-domain.com/api/v1/auth) and unset OAUTH_REDIRECT_URI."
            )
        return self

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v, info):
        """Prevent unsafe CORS configuration in production.

        Rejects wildcard ('*') in ALLOWED_ORIGINS when ENVIRONMENT is 'production'
        to avoid accidentally allowing all origins in a production deployment.
        """
        if info.data.get("ENVIRONMENT") == "production" and "*" in v:
            raise ValueError(
                "ALLOWED_ORIGINS cannot contain '*' in production. Specify explicit origins for security."
            )
        return v

    @property
    def TESTING(self) -> bool:  # noqa: N802
        """Testing flag that is only considered outside of production.

        Returns True if the internal testing flag is set and the current
        ENVIRONMENT is not 'production'. This protects production from test-only
        toggles that could weaken security.
        """
        return self._TESTING and self.ENVIRONMENT != "production"

    @TESTING.setter
    def TESTING(self, value: bool) -> None:  # noqa: N802
        """Set the internal testing flag used by test suites.

        This setter allows test code to enable the testing mode for the
        application while keeping the behavior isolated from production.
        """
        self._TESTING = value


# Create global settings instance
settings = Settings()
