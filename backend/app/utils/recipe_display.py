"""Normalize schema.org content for text and PDF display."""

from typing import Any


def display_ingredients(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [value] if value else []


def display_steps(value: Any) -> list[str]:
    if isinstance(value, list):
        return [text for step in value for text in display_steps(step)]
    if isinstance(value, dict):
        if "itemListElement" in value:
            heading = [str(value["name"])] if value.get("name") else []
            return heading + display_steps(value["itemListElement"])
        return [str(value.get("text") or value.get("name") or "")]
    return [str(value)] if value else []
