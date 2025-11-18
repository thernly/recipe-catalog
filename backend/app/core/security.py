"""
Security utilities for password hashing and JWT tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import bleach
from app.core.config import settings

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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
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


# CSRF Protection
# Note: This API primarily uses JWT tokens in headers (not cookies),
# so CSRF is less of a concern. However, these utilities are provided
# for defense-in-depth and future-proofing.

# In-memory store for CSRF tokens (simple approach for stateless API)
# In production with multiple instances, consider using Redis or database
_csrf_tokens: set[str] = set()


def generate_csrf_token() -> str:
    """
    Generate a secure CSRF token.

    Returns:
        A URL-safe random token string
    """
    token = secrets.token_urlsafe(32)
    _csrf_tokens.add(token)
    return token


def validate_csrf_token(token: str) -> bool:
    """
    Validate a CSRF token.

    Args:
        token: The CSRF token to validate

    Returns:
        True if token is valid, False otherwise
    """
    return token in _csrf_tokens


def revoke_csrf_token(token: str) -> None:
    """
    Revoke a CSRF token after use.

    Args:
        token: The CSRF token to revoke
    """
    _csrf_tokens.discard(token)


# Refresh Token Utilities
def generate_refresh_token() -> str:
    """
    Generate a secure random refresh token.

    Returns:
        A URL-safe random token string
    """
    return secrets.token_urlsafe(64)


def get_refresh_token_expiry() -> datetime:
    """
    Calculate expiry datetime for refresh tokens.

    Returns:
        Datetime object for configured days from now
    """
    return datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
