"""
Security utilities for password hashing and JWT tokens.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

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
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
