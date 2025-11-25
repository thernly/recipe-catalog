"""
Security utilities for password hashing and JWT tokens.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bleach
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jwt.exceptions import PyJWTError

from app.core.config import settings
from app.core.constants import REFRESH_TOKEN_LENGTH


# Argon2 password hasher
# Argon2 is the modern standard (won Password Hashing Competition 2015)
# - No password length limitations (unlike bcrypt's 72-byte limit)
# - Memory-hard algorithm resistant to GPU/ASIC attacks
# - Configurable time/memory/parallelism parameters
#
# Default parameters (as of argon2-cffi 23.x):
# - time_cost=2 (iterations)
# - memory_cost=65536 (64 MiB)
# - parallelism=1 (threads)
# - hash_len=32 (bytes)
# - salt_len=16 (bytes)
ph = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its Argon2 hash.

    Returns True if password matches, False otherwise.
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2id.

    Returns an Argon2 hash string in PHC format.
    """
    return ph.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except PyJWTError:
        return None


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Strips all HTML tags and returns plain text only.
    This is a simple approach suitable for user-generated content
    that should not contain any markup.

    Args:
        text: Text that may contain HTML

    Returns:
        Sanitized plain text with HTML tags removed
    """
    if not text:
        return text
    # Strip all HTML tags - allow plain text only
    return bleach.clean(text, tags=[], strip=True)


# Refresh Token Utilities
def generate_refresh_token() -> str:
    """
    Generate a secure random refresh token.

    Returns:
        A URL-safe random token string
    """
    return secrets.token_urlsafe(REFRESH_TOKEN_LENGTH)


def get_refresh_token_expiry() -> datetime:
    """
    Calculate expiry datetime for refresh tokens.

    Returns:
        Datetime object for configured days from now
    """
    return datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


def is_safe_redirect_url(url: str) -> bool:
    """
    Validate that a redirect URL is safe and belongs to allowed origins.

    This prevents open redirect vulnerabilities by ensuring redirects only go to
    trusted domains configured in ALLOWED_ORIGINS or FRONTEND_URL.

    Args:
        url: The URL to validate

    Returns:
        True if URL is safe to redirect to, False otherwise

    Examples:
        >>> is_safe_redirect_url("http://localhost:5173/dashboard")
        True
        >>> is_safe_redirect_url("https://evil.com/phishing")
        False
    """
    from urllib.parse import urlparse

    if not url:
        return False

    # Parse the URL
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    # Relative URLs (no scheme/netloc) are safe - they can't redirect to external sites
    if not parsed.scheme and not parsed.netloc:
        return True

    # Build list of allowed origins
    allowed_origins = []

    # Add configured allowed origins
    if isinstance(settings.ALLOWED_ORIGINS, list):
        allowed_origins.extend(settings.ALLOWED_ORIGINS)
    elif isinstance(settings.ALLOWED_ORIGINS, str):
        allowed_origins.append(settings.ALLOWED_ORIGINS)

    # Add frontend URL
    if settings.FRONTEND_URL:
        allowed_origins.append(settings.FRONTEND_URL)

    # Check if URL matches any allowed origin
    url_origin = f"{parsed.scheme}://{parsed.netloc}"
    return url_origin in allowed_origins


# CSRF Protection (Double-Submit Cookie Pattern)
def generate_csrf_token() -> str:
    """
    Generate a secure random CSRF token.

    Returns:
        A URL-safe random token string (32 bytes = 43 characters base64)
    """
    return secrets.token_urlsafe(32)


def verify_csrf_token(cookie_token: str | None, header_token: str | None) -> bool:
    """
    Verify CSRF token using double-submit cookie pattern.

    This provides defense-in-depth CSRF protection in addition to SameSite cookies.
    The token in the cookie must match the token in the request header.

    Args:
        cookie_token: CSRF token from cookie
        header_token: CSRF token from X-CSRF-Token header

    Returns:
        True if tokens match and are valid, False otherwise
    """
    if not cookie_token or not header_token:
        return False

    # Constant-time comparison to prevent timing attacks
    return secrets.compare_digest(cookie_token, header_token)
