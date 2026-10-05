"""
Deterministic recipe cleanup, shared by every write path (design doc §4.4).

`clean_recipe_data` runs on intake, file upload, recipe create and recipe edit:

- **Yield** is normalized in place ("6 6 servings" -> "6 servings", ["4", "4 servings"]
  -> "4 servings").
- **Times** (`prepTime`, `cookTime`, `totalTime`) are rewritten as ISO 8601 durations
  ("1 hr 30 mins" -> "PT1H30M") when they can be read; anything unreadable is left as is.
- **Ingredients:** `recipeIngredient` lines stay verbatim, and `parsedIngredients` is
  rebuilt beside them (see `app/services/ingredient_parser.py`).

No model is involved. The same function drives the backfill script.
"""

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from app.services.ingredient_parser import (
    is_header_entry,
    parse_ingredient_lines,
    unparsed_lines,
)


TIME_FIELDS = ("prepTime", "cookTime", "totalTime")

_NUM = r"\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?"
_ISO_DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$",
    re.IGNORECASE,
)
# (?![a-z]) rather than \b so compact forms like "1h30m" match
_DAYS_RE = re.compile(rf"({_NUM})\s*(?:days?|d)(?![a-z])", re.IGNORECASE)
_HOURS_RE = re.compile(rf"({_NUM})\s*(?:hours?|hrs?|h)(?![a-z])", re.IGNORECASE)
_MINUTES_RE = re.compile(rf"({_NUM})\s*(?:minutes?|mins?|m)(?![a-z])", re.IGNORECASE)
_UNICODE_HALF = {"½": " 1/2", "¼": " 1/4", "¾": " 3/4", "⅓": " 1/3", "⅔": " 2/3"}

_YIELD_LABEL_RE = re.compile(r"^(?:yields?|servings?|serves|portions?)\s*:\s*", re.IGNORECASE)
# "6 6 servings"; the lookahead keeps "1 1/2 cups" (a mixed number) intact
_REPEATED_LEADING_NUMBER_RE = re.compile(rf"^({_NUM})(?:\s+\1)+(?![\d/.])")


def _number(text: str) -> float:
    return float(sum(Fraction(part) for part in text.split()))


def parse_duration_minutes(duration: Any) -> int | None:
    """
    Parse an ISO 8601 duration or a prose time into whole minutes.

    Examples:
        "PT30M" -> 30, "PT1H30M" -> 90, "P0DT2H" -> 120, "PT90M" -> 90, "PT0M" -> 0
        "30 minutes" -> 30, "1 hour 30 minutes" -> 90, "1 1/2 hours" -> 90,
        "1.5 hrs" -> 90, "1h30m" -> 90, "20-25 mins" -> 25
        "overnight" -> None, "" -> None
    """
    if isinstance(duration, bool):
        return None
    if isinstance(duration, int | float):
        return int(round(duration)) if duration >= 0 else None
    if not isinstance(duration, str):
        return None

    text = duration.strip()
    if not text:
        return None

    iso = _ISO_DURATION_RE.match(text)
    if iso:
        parts = iso.groupdict()
        if not any(parts.values()):
            return None
        total = (
            float(parts["days"] or 0) * 1440
            + float(parts["hours"] or 0) * 60
            + float(parts["minutes"] or 0)
            + float(parts["seconds"] or 0) / 60
        )
        return int(round(total))

    for char, replacement in _UNICODE_HALF.items():
        text = text.replace(char, replacement)

    total = 0.0
    found = False
    try:
        for pattern, factor in ((_DAYS_RE, 1440), (_HOURS_RE, 60), (_MINUTES_RE, 1)):
            match = pattern.search(text)
            if match:
                total += _number(match.group(1)) * factor
                found = True
    except (ValueError, ZeroDivisionError):
        return None

    if not found:
        return None
    rounded = int(round(total))
    return rounded if rounded > 0 else None


def format_iso_duration(minutes: int) -> str:
    """Format minutes as the ISO 8601 form the recipe form reads ("PT1H30M")."""
    hours, mins = divmod(max(minutes, 0), 60)
    if hours and mins:
        return f"PT{hours}H{mins}M"
    if hours:
        return f"PT{hours}H"
    return f"PT{mins}M"


def normalize_time(value: Any) -> Any:
    """Return `value` as an ISO 8601 duration when it can be read, else unchanged."""
    if value is None or value == "":
        return value
    minutes = parse_duration_minutes(value)
    if minutes is None:
        return value.strip() if isinstance(value, str) else value
    return format_iso_duration(minutes)


def _normalize_yield_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = _YIELD_LABEL_RE.sub("", text)
    # "6 6 servings" -> "6 servings"
    text = _REPEATED_LEADING_NUMBER_RE.sub(r"\1", text)
    # "4 servings 4 servings" -> "4 servings"
    words = text.split(" ")
    half = len(words) // 2
    if len(words) % 2 == 0 and half and words[:half] == words[half:]:
        text = " ".join(words[:half])
    return text


def normalize_yield(value: Any) -> Any:
    """
    Normalize `recipeYield` to one readable string where possible.

    Lists (common in schema.org data, e.g. ["4", "4 servings"]) become the most
    descriptive entry; numbers become strings; text has repeated numbers and labels
    removed. Values that are not text, numbers or lists are left unchanged.
    """
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return str(int(value)) if float(value).is_integer() else str(value)
    if isinstance(value, str):
        return _normalize_yield_text(value) if value.strip() else value
    if isinstance(value, list):
        candidates = [
            _normalize_yield_text(str(v)) for v in value if isinstance(v, str | int | float)
        ]
        candidates = [c for c in candidates if c]
        if not candidates:
            return value
        descriptive = [c for c in candidates if re.search(r"[A-Za-z]", c)]
        return descriptive[0] if descriptive else candidates[0]
    return value


def derive_total_time_minutes(recipe_data: dict[str, Any]) -> int | None:
    """Total minutes from `totalTime`, else from `prepTime` + `cookTime`."""
    total = parse_duration_minutes(recipe_data.get("totalTime"))
    if total is not None:
        return total
    prep = parse_duration_minutes(recipe_data.get("prepTime"))
    cook = parse_duration_minutes(recipe_data.get("cookTime"))
    if prep is None and cook is None:
        return None
    return (prep or 0) + (cook or 0) or None


@dataclass
class CleanupResult:
    """The cleaned recipe data and what changed, for logging and the backfill report."""

    data: dict[str, Any]
    # field -> (before, after), for yield and time fields that changed
    changes: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    ingredient_lines: int = 0
    parsed_lines: int = 0
    unparsed: list[str] = field(default_factory=list)


def _ingredient_lines(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def clean_recipe_data(
    recipe_data: dict[str, Any], previous_parsed: list[Any] | None = None
) -> CleanupResult:
    """
    Clean a schema.org `recipe_data` dict. The input is not modified.

    Args:
        recipe_data: The recipe's schema.org data (camelCase keys)
        previous_parsed: The `parsedIngredients` currently stored for this recipe, if it
            already exists. Taken from the database, never from the client, so `raw`
            and `parsedBy` are always set by code.

    Returns:
        CleanupResult with the cleaned copy and a summary of the changes
    """
    data = dict(recipe_data) if isinstance(recipe_data, dict) else {}
    changes: dict[str, tuple[Any, Any]] = {}

    if "recipeYield" in data:
        cleaned_yield = normalize_yield(data["recipeYield"])
        if cleaned_yield != data["recipeYield"]:
            changes["recipeYield"] = (data["recipeYield"], cleaned_yield)
            data["recipeYield"] = cleaned_yield

    for time_field in TIME_FIELDS:
        if time_field in data:
            cleaned_time = normalize_time(data[time_field])
            if cleaned_time != data[time_field]:
                changes[time_field] = (data[time_field], cleaned_time)
                data[time_field] = cleaned_time

    lines = _ingredient_lines(data.get("recipeIngredient"))
    parsed = parse_ingredient_lines(lines, previous_parsed)
    data["parsedIngredients"] = parsed

    ingredient_entries = [
        e for e in parsed if str(e.get("raw", "")).strip() and not is_header_entry(e)
    ]
    missed = unparsed_lines(parsed)
    return CleanupResult(
        data=data,
        changes=changes,
        ingredient_lines=len(ingredient_entries),
        parsed_lines=len(ingredient_entries) - len(missed),
        unparsed=missed,
    )
