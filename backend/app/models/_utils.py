"""Shared utilities for SQLAlchemy models."""

from datetime import UTC, datetime


def utc_now():
    """
    Return current UTC datetime.

    Used as default for datetime columns to avoid deprecation warnings
    from datetime.utcnow().
    """
    return datetime.now(UTC)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware in UTC.

    SQLite stores datetimes as naive, but we want to work with aware datetimes.
    This function handles the conversion consistently.

    Args:
        dt: A datetime object (naive or aware)

    Returns:
        A timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def is_expired(dt: datetime) -> bool:
    """
    Check if a datetime has passed (is in the past).

    Handles both timezone-aware and naive datetimes by converting to UTC.

    Args:
        dt: The datetime to check

    Returns:
        True if the datetime is in the past
    """
    dt_utc = ensure_utc(dt)
    return dt_utc < datetime.now(UTC)
