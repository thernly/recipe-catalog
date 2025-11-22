"""Shared utilities for SQLAlchemy models."""

from datetime import UTC, datetime


def utc_now():
    """
    Return current UTC datetime.

    Used as default for datetime columns to avoid deprecation warnings
    from datetime.utcnow().
    """
    return datetime.now(UTC)
