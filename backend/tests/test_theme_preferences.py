"""Tests for theme preferences functionality."""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserPreferencesBase, UserPreferencesUpdate


def test_valid_theme_values():
    """Test that all new theme values are accepted."""
    valid_themes = [
        "light",
        "dark",
        "high-contrast",
        "system",
        "classic",
        "professional",
    ]

    for theme in valid_themes:
        # Should not raise ValidationError
        prefs = UserPreferencesUpdate(theme=theme)
        assert prefs.theme == theme


def test_invalid_theme_value():
    """Test that invalid theme values are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        UserPreferencesUpdate(theme="invalid-theme")

    assert "theme" in str(exc_info.value)


def test_default_theme_is_light():
    """Test that the default theme is 'light'."""
    prefs = UserPreferencesBase()
    assert prefs.theme == "light"


def test_theme_update_optional():
    """Test that theme field is optional in updates."""
    # Should not raise error when theme is not provided
    prefs = UserPreferencesUpdate(default_view="list")
    assert prefs.theme is None
    assert prefs.default_view == "list"


def test_backward_compatibility_classic_theme():
    """Test that 'classic' theme is still supported for backward compatibility."""
    prefs = UserPreferencesUpdate(theme="classic")
    assert prefs.theme == "classic"


def test_system_theme_value():
    """Test that 'system' theme value is accepted."""
    prefs = UserPreferencesUpdate(theme="system")
    assert prefs.theme == "system"
