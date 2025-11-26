"""Test configuration validation."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.constants import MIN_SECRET_KEY_LENGTH


def test_secret_key_minimum_length_valid():
    """Test that SECRET_KEY with sufficient length is accepted."""
    valid_key = "a" * MIN_SECRET_KEY_LENGTH
    settings = Settings(SECRET_KEY=valid_key)
    assert valid_key == settings.SECRET_KEY


def test_secret_key_too_short():
    """Test that SECRET_KEY shorter than minimum is rejected."""
    short_key = "a" * (MIN_SECRET_KEY_LENGTH - 1)
    with pytest.raises(ValidationError) as exc_info:
        Settings(SECRET_KEY=short_key)

    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert "SECRET_KEY" in str(errors[0])
    assert "at least" in str(errors[0]["msg"]).lower()


def test_secret_key_exactly_minimum_length():
    """Test that SECRET_KEY with exactly minimum length is accepted."""
    key = "a" * MIN_SECRET_KEY_LENGTH
    settings = Settings(SECRET_KEY=key)
    assert key == settings.SECRET_KEY


def test_secret_key_long_key():
    """Test that long SECRET_KEY is accepted."""
    long_key = "a" * (MIN_SECRET_KEY_LENGTH * 2)
    settings = Settings(SECRET_KEY=long_key)
    assert long_key == settings.SECRET_KEY
