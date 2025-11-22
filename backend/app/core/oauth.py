"""OAuth/OIDC provider configuration and utilities."""

import secrets
from typing import Any

from authlib.integrations.starlette_client import OAuth

from app.core.config import settings


# Initialize OAuth registry with httpx client
oauth = OAuth()

# Configure Google OIDC provider
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile",
            "prompt": "select_account",
        },
    )

# Configure Microsoft OIDC provider
if settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET:
    oauth.register(
        name="microsoft",
        client_id=settings.MICROSOFT_CLIENT_ID,
        client_secret=settings.MICROSOFT_CLIENT_SECRET,
        server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile",
        },
    )

# Configure GitHub OAuth provider (feature-flagged)
if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        api_base_url="https://api.github.com/",
        client_kwargs={
            "scope": "user:email",
        },
    )


def get_available_providers() -> list[dict[str, str]]:
    """Get list of configured OAuth providers."""
    providers = []

    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        providers.append({"name": "google", "display_name": "Google", "icon": "google"})

    if settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET:
        providers.append({"name": "microsoft", "display_name": "Microsoft", "icon": "microsoft"})

    if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
        providers.append({"name": "github", "display_name": "GitHub", "icon": "github"})

    return providers


def generate_state_token() -> str:
    """Generate a secure random state token for CSRF protection."""
    return secrets.token_urlsafe(32)


def extract_user_info(provider_name: str, userinfo: dict[str, Any]) -> dict[str, str | bool | None]:
    """
    Extract standardized user information from provider-specific userinfo.

    Returns:
        dict with keys: subject, email, email_verified, display_name
    """
    if provider_name == "google":
        return {
            "subject": userinfo.get("sub"),
            "email": userinfo.get("email"),
            "email_verified": userinfo.get("email_verified", False),
            "display_name": userinfo.get("name"),
        }

    elif provider_name == "microsoft":
        return {
            "subject": userinfo.get("sub") or userinfo.get("oid"),
            "email": userinfo.get("email") or userinfo.get("preferred_username"),
            "email_verified": True,  # Microsoft emails are always verified
            "display_name": userinfo.get("name"),
        }

    elif provider_name == "github":
        # GitHub requires additional API call for email
        return {
            "subject": str(userinfo.get("id")),
            "email": userinfo.get("email"),
            "email_verified": userinfo.get("verified", False),
            "display_name": userinfo.get("name") or userinfo.get("login"),
        }

    else:
        raise ValueError(f"Unknown provider: {provider_name}")
