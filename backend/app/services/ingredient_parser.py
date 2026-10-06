"""
Ingredient-line parsing.

The first part is the regex parser shopping lists have always used (`parse_quantity`,
`parse_ingredient_string`, `normalize_unit`, `consolidate_ingredients` and helpers),
moved here unchanged from `app/api/shopping_lists.py`.

The second part, `parse_ingredient_line` and `parse_ingredient_lines`, builds the
structured `parsedIngredients` entries stored in `recipe_data` (design doc §4.5). It
extends the same approach with notes after commas and in parentheses, ranges, unicode
fractions and group headers ("For the dressing:"), and reports lines it cannot handle.
"""

import re
from fractions import Fraction
from typing import Any


def parse_quantity(quantity_str: str) -> float:
    """
    Parse a quantity string into a float.
    Handles fractions (1/2, 3/4), mixed numbers (1 1/2), decimals, and ranges (1-2).

    Args:
        quantity_str: String representation of quantity

    Returns:
        float: Parsed quantity value
    """
    if not quantity_str or not quantity_str.strip():
        return 0.0

    quantity_str = quantity_str.strip()

    # Handle ranges (e.g., "1-2" -> use the higher value)
    if "-" in quantity_str and not quantity_str.startswith("-"):
        parts = quantity_str.split("-")
        if len(parts) == 2:
            try:
                return max(float(Fraction(parts[0].strip())), float(Fraction(parts[1].strip())))
            except (ValueError, ZeroDivisionError):
                pass

    # Handle mixed numbers (e.g., "1 1/2")
    parts = quantity_str.split()
    if len(parts) == 2:
        try:
            whole = float(Fraction(parts[0]))
            fraction = float(Fraction(parts[1]))
            return whole + fraction
        except (ValueError, ZeroDivisionError):
            pass

    # Handle simple fractions and decimals
    try:
        return float(Fraction(quantity_str))
    except (ValueError, ZeroDivisionError):
        return 0.0


def parse_ingredient_string(ingredient_str: str) -> tuple[str | None, str | None, str]:
    """
    Parse an ingredient string into quantity, unit, and name.

    Examples:
        "1 stick butter" -> ("1", "stick", "butter")
        "2 cups flour" -> ("2", "cups", "flour")
        "3 eggs" -> ("3", None, "eggs")
        "salt" -> (None, None, "salt")

    Args:
        ingredient_str: The ingredient string to parse

    Returns:
        Tuple of (quantity, unit, name)
    """
    ingredient_str = ingredient_str.strip()

    # Pattern to match quantity (including fractions) at the start
    # Matches: "1", "1.5", "1/2", "1 1/2", "1-2"
    quantity_pattern = r"^(\d+(?:\s+\d+)?(?:[\/\-\.]\d+)?)\s+"
    match = re.match(quantity_pattern, ingredient_str)

    if match:
        quantity = match.group(1).strip()
        remainder = ingredient_str[match.end() :].strip()

        # Common units
        units = [
            "cup",
            "cups",
            "tablespoon",
            "tablespoons",
            "tbsp",
            "teaspoon",
            "teaspoons",
            "tsp",
            "ounce",
            "ounces",
            "oz",
            "pound",
            "pounds",
            "lb",
            "lbs",
            "gram",
            "grams",
            "g",
            "kilogram",
            "kilograms",
            "kg",
            "milliliter",
            "milliliters",
            "ml",
            "liter",
            "liters",
            "l",
            "stick",
            "sticks",
            "clove",
            "cloves",
            "can",
            "cans",
            "package",
            "packages",
            "pkg",
            "bunch",
            "bunches",
            "head",
            "heads",
            "piece",
            "pieces",
            "slice",
            "slices",
            "pinch",
            "dash",
            "sprig",
            "sprigs",
            "whole",
            "large",
            "medium",
            "small",
        ]

        # Check if the next word is a unit
        words = remainder.split(None, 1)
        if words and words[0].lower() in units:
            unit = words[0]
            name = words[1] if len(words) > 1 else ""
            return (quantity, unit, name)
        else:
            # No unit found, rest is the name
            return (quantity, None, remainder)
    else:
        # No quantity found
        return (None, None, ingredient_str)


def normalize_unit(unit: str | None) -> str | None:
    """
    Normalize unit names for better consolidation.

    Args:
        unit: The unit string to normalize

    Returns:
        Normalized unit string or None
    """
    if not unit:
        return None

    unit_lower = unit.lower().strip()

    # Map variations to standard forms
    unit_map = {
        "tbsp": "tablespoon",
        "tablespoons": "tablespoon",
        "tsp": "teaspoon",
        "teaspoons": "teaspoon",
        "cups": "cup",
        "oz": "ounce",
        "ounces": "ounce",
        "lb": "pound",
        "lbs": "pound",
        "pounds": "pound",
        "g": "gram",
        "grams": "gram",
        "kg": "kilogram",
        "kilograms": "kilogram",
        "ml": "milliliter",
        "milliliters": "milliliter",
        "l": "liter",
        "liters": "liter",
        "sticks": "stick",
        "cloves": "clove",
        "cans": "can",
        "packages": "package",
        "pkg": "package",
        "bunches": "bunch",
        "heads": "head",
        "pieces": "piece",
        "slices": "slice",
        "sprigs": "sprig",
    }

    return unit_map.get(unit_lower, unit_lower)


def get_base_ingredient_name(name: str) -> str:
    """
    Extract the base ingredient name by removing preparation methods.

    This removes:
    - Text in parentheses: "garlic (minced)" -> "garlic"
    - Text after commas: "garlic, minced" -> "garlic"
    - Common preparation words at the end

    Args:
        name: The full ingredient name

    Returns:
        The base ingredient name without preparation methods
    """
    import re

    # Remove text in parentheses
    base_name = re.sub(r"\s*\([^)]*\)\s*", " ", name)

    # Remove text after comma
    base_name = base_name.split(",")[0]

    # Strip common preparation keywords at the end
    # These are preparation methods you do at home, so they shouldn't affect shopping
    prep_keywords = [
        "minced",
        "chopped",
        "diced",
        "sliced",
        "grated",
        "shredded",
        "crushed",
        "pressed",
        "peeled",
        "julienned",
        "cubed",
        "halved",
        "quartered",
        "beaten",
        "melted",
        "finely",
        "coarsely",
        "roughly",
        "thinly",
        "thickly",
        "cloves",
        "clove",  # for "garlic cloves" -> "garlic"
    ]

    # Try to remove preparation keywords from the end
    words = base_name.strip().split()
    while words and words[-1].lower() in prep_keywords:
        words.pop()

    if words:
        base_name = " ".join(words)

    return base_name.strip()


def singularize_ingredient(name: str) -> str:
    """
    Convert plural ingredient names to singular for better consolidation.

    Examples:
        "onions" -> "onion"
        "tomatoes" -> "tomato"
        "carrots" -> "carrot"

    Args:
        name: The ingredient name to singularize

    Returns:
        The singularized ingredient name
    """
    name_lower = name.lower()

    # Handle common irregular plurals
    irregular_plurals = {
        "tomatoes": "tomato",
        "potatoes": "potato",
    }

    if name_lower in irregular_plurals:
        return irregular_plurals[name_lower]

    # Handle regular plurals ending in 's'
    # Only singularize if it's likely a plural (ends in s but not ss, us, is)
    if name_lower.endswith("s") and not name_lower.endswith(("ss", "us", "is")):
        # Handle words ending in 'ies' -> 'y'
        if name_lower.endswith("ies") and len(name_lower) > 3:
            return name[:-3] + "y"
        # Handle words ending in 'es' -> 'e' or just 's'
        elif name_lower.endswith("es") and len(name_lower) > 2:
            # For words like "olives" -> "olive", but not "cheese" -> "chees"
            if name_lower[-3] not in "aeiou":
                return name[:-1]
            else:
                return name[:-2]
        # Regular plural: just remove 's'
        else:
            return name[:-1]

    return name


def consolidate_ingredients(
    ingredients_data: list[dict[str, str | None]],
) -> list[dict[str, str | None]]:
    """
    Consolidate ingredients by name and unit, summing quantities.

    Ingredients are grouped by their base name (without preparation methods)
    and unit. For example, "garlic (minced)", "garlic (chopped)", and "garlic cloves"
    will all be combined into a single shopping list item.

    Args:
        ingredients_data: List of dicts with 'quantity', 'unit', 'name' keys

    Returns:
        List of consolidated ingredient dicts
    """
    # Group by (base_ingredient_name, normalized_unit)
    consolidated: dict[tuple[str, str | None], dict[str, Any]] = {}

    for ing in ingredients_data:
        name = ing.get("name", "").strip()  # type: ignore[union-attr]  # latent: an explicit None name raises
        if not name:
            continue

        # Filter out section headers (e.g., "Pie Crust:", "filling:", "For the crust:")
        # These are items with no quantity that end with a colon
        quantity_str = ing.get("quantity")
        if not quantity_str and name.endswith(":"):
            continue

        # Get base ingredient name (without preparation methods) for grouping
        base_name = get_base_ingredient_name(name)
        # Singularize and lowercase for consistent grouping
        base_name = singularize_ingredient(base_name).lower()

        unit = normalize_unit(ing.get("unit"))

        # Parse quantity
        quantity_value = parse_quantity(quantity_str) if quantity_str else 0.0

        key = (base_name, unit)

        if key in consolidated:
            # Add to existing quantity
            consolidated[key]["quantity_value"] += quantity_value
            # Prefer the simpler name (shorter is usually simpler)
            # Singularize and use lowercase for consistency
            current_name = consolidated[key]["name"]
            new_name = singularize_ingredient(get_base_ingredient_name(name)).lower()
            if len(new_name) < len(current_name):
                consolidated[key]["name"] = new_name
        else:
            # New ingredient - use base name for display (without preparation methods)
            # Singularize and use lowercase for case-insensitive consolidation
            consolidated[key] = {
                "name": singularize_ingredient(get_base_ingredient_name(name)).lower(),
                "unit": unit,
                "quantity_value": quantity_value,
            }

    # Convert back to list with formatted quantities
    result = []
    for (_name_key, _unit_key), data in consolidated.items():
        qty_value = data["quantity_value"]

        # Format quantity nicely
        if qty_value == 0:
            qty_str = None
        elif qty_value == int(qty_value):
            qty_str = str(int(qty_value))
        else:
            # Try to convert to fraction if it's close to a common fraction
            frac = Fraction(qty_value).limit_denominator(16)
            if abs(float(frac) - qty_value) < 0.01:
                if frac.numerator > frac.denominator:
                    whole = frac.numerator // frac.denominator
                    remainder = frac.numerator % frac.denominator
                    if remainder > 0:
                        qty_str = f"{whole} {remainder}/{frac.denominator}"
                    else:
                        qty_str = str(whole)
                else:
                    qty_str = f"{frac.numerator}/{frac.denominator}"
            else:
                qty_str = f"{qty_value:.2f}".rstrip("0").rstrip(".")

        result.append(
            {
                "name": data["name"],
                "unit": data["unit"],
                "quantity": qty_str,
            }
        )

    return result


# ============================================
# Structured parsing for recipe_data["parsedIngredients"] (design doc §4.5)
# ============================================

PARSED_BY_REGEX = "regex"
PARSED_BY_MODEL = "model"

_UNICODE_FRACTIONS = {
    "½": "1/2",
    "⅓": "1/3",
    "⅔": "2/3",
    "¼": "1/4",
    "¾": "3/4",
    "⅕": "1/5",
    "⅖": "2/5",
    "⅗": "3/5",
    "⅘": "4/5",
    "⅙": "1/6",
    "⅚": "5/6",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
}

# Bullets and checkbox glyphs that scraped ingredient lists often start with
_LEADING_BULLETS_RE = re.compile(r"^[•‣⁃□▢○●☐☑·*\-]+\s*")

_NUMBER = r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
_QUANTITY_RE = re.compile(
    rf"^(?P<q1>{_NUMBER})(?:\s*(?:-|to|or)\s*(?P<q2>{_NUMBER}))?(?=\s|$|[a-zA-Z(])",
    re.IGNORECASE,
)

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}
# "a"/"an" count as 1 only before a unit ("a pinch of salt"), never on their own
# ("a little oil")
_ARTICLES = {"a", "an"}

# Package size right after the quantity: "1 (14-ounce) can" is handled by the
# parenthesis rule, "1 15-ounce can" by this one
_SIZE_RE = re.compile(
    rf"^(?P<size>(?:{_NUMBER})\s*-?\s*(?:ounces?|oz|grams?|g|ml|pounds?|lbs?|inch(?:es)?|cm)\.?)\s+",
    re.IGNORECASE,
)

# Unit spelling -> canonical name for spellings `normalize_unit` does not already map.
# Spellings not listed here go through `normalize_unit`, so its map stays the single
# source for the units shopping lists use.
_EXTRA_UNIT_ALIASES = {
    "c": "cup",
    "tbs": "tablespoon",
    "tbl": "tablespoon",
    "tbsps": "tablespoon",
    "tsps": "teaspoon",
    "fl oz": "fluid ounce",
    "fluid ounce": "fluid ounce",
    "fluid ounces": "fluid ounce",
    "kgs": "kilogram",
    "mg": "milligram",
    "milligrams": "milligram",
    "millilitre": "milliliter",
    "millilitres": "milliliter",
    "mls": "milliliter",
    "litre": "liter",
    "litres": "liter",
    "quarts": "quart",
    "qt": "quart",
    "qts": "quart",
    "pints": "pint",
    "pt": "pint",
    "pts": "pint",
    "gallons": "gallon",
    "gal": "gallon",
    "jars": "jar",
    "packets": "packet",
    "pkgs": "package",
    "bags": "bag",
    "boxes": "box",
    "bottles": "bottle",
    "pinches": "pinch",
    "dashes": "dash",
    "handfuls": "handful",
    "sheets": "sheet",
    "stalks": "stalk",
    "drops": "drop",
    "envelopes": "envelope",
    "containers": "container",
    "cartons": "carton",
    "scoops": "scoop",
}

_UNIT_SPELLINGS = sorted(
    {
        # Volume
        "cup", "cups", "c",
        "tablespoon", "tablespoons", "tbsp", "tbsps", "tbs", "tbl",
        "teaspoon", "teaspoons", "tsp", "tsps",
        "fluid ounce", "fluid ounces", "fl oz",
        "milliliter", "milliliters", "millilitre", "millilitres", "ml", "mls",
        "liter", "liters", "litre", "litres", "l",
        "quart", "quarts", "qt", "qts",
        "pint", "pints", "pt", "pts",
        "gallon", "gallons", "gal",
        # Weight
        "ounce", "ounces", "oz",
        "pound", "pounds", "lb", "lbs",
        "gram", "grams", "g",
        "kilogram", "kilograms", "kg", "kgs",
        "milligram", "milligrams", "mg",
        # Count and package
        "stick", "sticks", "clove", "cloves", "can", "cans", "jar", "jars",
        "package", "packages", "pkg", "pkgs", "packet", "packets", "bag", "bags",
        "box", "boxes", "bottle", "bottles", "bunch", "bunches", "head", "heads",
        "piece", "pieces", "slice", "slices", "pinch", "pinches", "dash", "dashes",
        "sprig", "sprigs", "handful", "handfuls", "sheet", "sheets", "stalk", "stalks",
        "drop", "drops", "envelope", "envelopes", "container", "containers",
        "carton", "cartons", "scoop", "scoops",
    },
    key=len,
    reverse=True,
)  # fmt: skip
_UNIT_RE = re.compile(
    r"^(?P<unit>"
    + "|".join(re.escape(u).replace(r"\ ", r"\.?\s+") for u in _UNIT_SPELLINGS)
    + r")\.?(?=\s|$|[,()/])",
    re.IGNORECASE,
)

_TRAILING_NOTE_RE = re.compile(
    r"\s+(?P<note>to taste|optional|"
    r"for (?:garnish|garnishing|serving|decoration|dusting|greasing|frying|brushing))$",
    re.IGNORECASE,
)

_MAX_ITEM_LENGTH = 60
_MAX_ITEM_WORDS = 9


def _normalize_line(text: str, strip_bullets: bool = True) -> str:
    """Normalize unicode fractions, dashes, spacing and (optionally) leading bullets."""
    for char, fraction in _UNICODE_FRACTIONS.items():
        if char in text:
            text = re.sub(rf"(\d)\s*{char}", rf"\1 {fraction}", text)
            text = text.replace(char, fraction)
    text = text.replace("⁄", "/")  # fraction slash
    text = re.sub(r"[‐-―−]", "-", text)
    text = text.replace(" ", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return _LEADING_BULLETS_RE.sub("", text).strip() if strip_bullets else text


def _to_number(text: str) -> float:
    return float(sum(Fraction(part) for part in text.split()))


def _tidy_number(value: float) -> int | float:
    if abs(value - round(value)) < 1e-9:
        return int(round(value))
    return round(value, 3)


def _canonical_unit(spelling: str) -> str | None:
    key = re.sub(r"\.", "", spelling.lower())
    key = re.sub(r"\s+", " ", key).strip()
    return _EXTRA_UNIT_ALIASES.get(key) or normalize_unit(key)


def _split_parenthesized(text: str) -> tuple[str, list[str]] | None:
    """
    Remove each outermost "(...)" group from `text`, returning the remaining text and
    the groups' contents. Nested parentheses stay inside their group's content:
    "celeriac (peeled (about 450g))" gives ("celeriac", ["peeled (about 450g)"]).
    Returns None when the parentheses are unbalanced.
    """
    remaining: list[str] = []
    groups: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char == "(":
            if depth:
                current.append(char)
            else:
                current = []
            depth += 1
        elif char == ")":
            if depth == 0:
                return None
            depth -= 1
            if depth:
                current.append(char)
            else:
                groups.append("".join(current).strip())
        elif depth:
            current.append(char)
        else:
            remaining.append(char)
    if depth:
        return None
    return re.sub(r"\s+", " ", "".join(remaining)).strip(), [g for g in groups if g]


_INGREDIENT_PARTS = r"juice|zest|rind|peel|seeds|flesh|pulp|leaves|segments"
_PART_OF_RE = re.compile(
    rf"^(?P<part>(?:{_INGREDIENT_PARTS})(?:\s+(?:and|&)\s+(?:{_INGREDIENT_PARTS}))?)"
    r"\s+(?:of|from)\s+(?P<rest>.+)$",
    re.IGNORECASE,
)

_MEASURE_CONNECTOR_RE = re.compile(r"^\s*(/|\+|plus)\s*", re.IGNORECASE)


def _take_alternative_measures(text: str) -> tuple[str, list[str]]:
    """
    Strip extra measures right after the unit, which become notes:

    - alternatives after a slash: "2 sticks/1 cup butter", "8 oz / 225 g cheese"
      give "1 cup", "225 g";
    - additions after "plus" or "+": "1/4 cup plus 2 tablespoons oil" gives
      "plus 2 tablespoons". The first measure stays the quantity; adding them up would
      need unit conversion, which is out of scope (design doc §3).
    """
    extras: list[str] = []
    while True:
        connector = _MEASURE_CONNECTOR_RE.match(text)
        if not connector:
            break
        rest = text[connector.end() :]
        quantity = _QUANTITY_RE.match(rest)
        if not quantity:
            break
        after = rest[quantity.end() :].lstrip()
        unit = _UNIT_RE.match(after)
        if not unit:
            break
        measure = f"{quantity.group(0).strip()} {after[: unit.end()].strip()}"
        extras.append(measure if connector.group(1) == "/" else f"plus {measure}")
        text = after[unit.end() :].strip()
    return text, extras


def _make_header_entry(raw: str, group: str) -> dict[str, Any]:
    """
    A group header line ("For the apples:"). It carries no ingredient fields, so it
    cannot be mistaken for an ingredient; `group` on the lines after it names the group.
    """
    return {"raw": raw, "header": True, "group": group, "parsedBy": PARSED_BY_REGEX}


def is_header_entry(entry: dict[str, Any]) -> bool:
    return bool(entry.get("header"))


def _make_entry(
    raw: str,
    *,
    quantity: int | float | None = None,
    quantity_max: int | float | None = None,
    unit: str | None = None,
    item: str | None = None,
    note: str | None = None,
    group: str | None = None,
    parsed_by: str | None = PARSED_BY_REGEX,
) -> dict[str, Any]:
    return {
        "raw": raw,
        "quantity": quantity,
        "quantityMax": quantity_max,
        "unit": unit,
        "item": item,
        "note": note,
        "group": group,
        "parsedBy": parsed_by,
    }


def detect_group_header(line: str) -> str | None:
    """
    Return the group name if `line` is a group header ("For the dressing:"), else None.

    Headers carry no digits and are short, and either end with a colon, are wrapped in
    decoration ("--- Sauce ---", "**Sauce**"), are all capitals ("FILLING"), or start
    with "For" ("For the topping").
    """
    # Keep leading "---"/"**" here: they are header decoration, not bullets
    text = _normalize_line(line, strip_bullets=False)
    if not text or re.search(r"\d", text):
        return None

    words = text.split()
    name = re.sub(r"^[\s\-=*#_~]+|[\s\-=*#_~]+$", "", text).rstrip(":").strip()
    if not name:
        return None

    if text.endswith(":") and len(words) <= 8:
        return name
    if re.match(r"^([-=*#_~])\1+.*([-=*#_~])\2+$", text):
        return name
    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 3 and all(c.isupper() for c in letters) and len(words) <= 5:
        return name
    if re.match(r"^for\s+\w", text, re.IGNORECASE) and len(words) <= 6 and "," not in text:
        return name
    return None


def parse_ingredient_line(raw: str) -> dict[str, Any]:
    """
    Parse one ingredient line into a `parsedIngredients` entry (group left as None).

    Handles a leading quantity (integers, decimals, fractions, mixed numbers, unicode
    fractions, ranges such as "1-2", "2 to 3" and "1 or 2", number words), a package
    size ("1 (14-ounce) can", "1 15-ounce can"), a known unit, notes in parentheses,
    after the first comma, or as a trailing "to taste"/"optional", a quantity given
    after a comma ("Butter, 2 tablespoons"), and extra measures after the unit
    ("2 sticks/1 cup", "1/4 cup plus 2 tablespoons"), which go to the note.

    A line it cannot handle gets `parsedBy: None` and no parsed fields. That covers lines
    with no item left, numbers left inside the item ("seeds scraped from 1 vanilla pod"), unbalanced
    parentheses, and lines too long to be an ingredient.
    """
    unparsed = _make_entry(raw, parsed_by=None)
    text = _normalize_line(raw)
    if not text:
        return unparsed

    # "Juice of 1 lemon", "Zest and juice of 2 limes": parse what follows "of" as the
    # ingredient, and keep the part ("juice") as a note
    part_of = _PART_OF_RE.match(text)
    if part_of:
        rest = re.sub(r"^an?\s+", "1 ", part_of.group("rest"), flags=re.IGNORECASE)
        inner = parse_ingredient_line(rest)
        if inner["parsedBy"] is None or inner["quantity"] is None:
            return unparsed
        part = re.sub(r"\s+", " ", part_of.group("part")).lower()
        inner["raw"] = raw
        inner["note"] = "; ".join(n for n in (part, inner["note"]) if n)
        return inner

    quantity: float | None = None
    quantity_max: float | None = None
    unit: str | None = None
    notes: list[str] = []

    try:
        match = _QUANTITY_RE.match(text)
        if match:
            quantity = _to_number(match.group("q1"))
            if match.group("q2"):
                quantity_max = _to_number(match.group("q2"))
            text = text[match.end() :].strip()
        else:
            first, _, rest = text.partition(" ")
            word = first.lower()
            if word in _NUMBER_WORDS:
                quantity = float(_NUMBER_WORDS[word])
                text = rest.strip()
            elif word in _ARTICLES and _UNIT_RE.match(rest.strip()):
                quantity = 1.0
                text = rest.strip()
    except (ValueError, ZeroDivisionError):
        return unparsed

    if quantity is not None:
        # Package size: "(14-ounce)" or "15-ounce" between quantity and unit
        paren = re.match(r"^\(([^()]*)\)\s*", text)
        if paren:
            notes.append(paren.group(1).strip())
            text = text[paren.end() :]
        else:
            # "1 15-ounce can beans", "One 2 1/4-lb. piece beef", "1 3-pound chicken"
            size = _SIZE_RE.match(text)
            if size:
                notes.append(size.group("size").strip())
                text = text[size.end() :]

    unit_match = _UNIT_RE.match(text)
    if unit_match and (
        quantity is not None or unit_match.group("unit").lower() in {"pinch", "dash"}
    ):
        unit = _canonical_unit(unit_match.group("unit"))
        text = text[unit_match.end() :].strip()
        text, alternatives = _take_alternative_measures(text)
        notes.extend(alternatives)
        text = re.sub(r"^of\s+", "", text, flags=re.IGNORECASE)

    # Notes in parentheses, anywhere in the remainder (nested ones stay in their note)
    split = _split_parenthesized(text)
    if split is None:
        return unparsed
    text, paren_notes = split
    notes.extend(paren_notes)

    # Note after the first comma
    item, _, comma_note = text.partition(",")
    comma_note = comma_note.strip()
    item = item.strip()

    # Quantity after a comma: "Butter, 2 tablespoons"
    if quantity is None and comma_note:
        trailing = _QUANTITY_RE.match(comma_note)
        if trailing:
            after = comma_note[trailing.end() :].strip()
            trailing_unit = _UNIT_RE.match(after)
            if not after or (trailing_unit and not after[trailing_unit.end() :].strip()):
                try:
                    quantity = _to_number(trailing.group("q1"))
                    if trailing.group("q2"):
                        quantity_max = _to_number(trailing.group("q2"))
                except (ValueError, ZeroDivisionError):
                    return unparsed
                unit = _canonical_unit(trailing_unit.group("unit")) if trailing_unit else None
                comma_note = ""

    if comma_note:
        notes.append(comma_note)

    trailing_note = _TRAILING_NOTE_RE.search(item)
    if trailing_note:
        notes.append(trailing_note.group("note"))
        item = item[: trailing_note.start()]

    item = re.sub(r"^of\s+", "", item, flags=re.IGNORECASE).strip(" .;:-")

    if (
        not item
        or re.search(r"\d", item)
        or re.search(r"\bplus\b", item, re.IGNORECASE)
        or len(item) > _MAX_ITEM_LENGTH
        or len(item.split()) > _MAX_ITEM_WORDS
    ):
        return unparsed

    note = "; ".join(n for n in notes if n) or None
    return _make_entry(
        raw,
        quantity=_tidy_number(quantity) if quantity is not None else None,
        quantity_max=(
            _tidy_number(quantity_max)
            if quantity_max is not None and quantity_max != quantity
            else None
        ),
        unit=unit,
        item=item,
        note=note,
        parsed_by=PARSED_BY_REGEX,
    )


def parse_ingredient_lines(
    lines: list[Any], previous: list[Any] | None = None
) -> list[dict[str, Any]]:
    """
    Build `parsedIngredients`: one entry per `recipeIngredient` line, in order.

    A group header produces `{"raw", "header": true, "group", "parsedBy"}` with no
    ingredient fields, and sets `group` on the lines after it.

    `previous` is the recipe's stored `parsedIngredients`. A line whose raw text is
    unchanged keeps its previous entry when a model parsed it; regex entries are simply
    recomputed, which gives the same result unless the regex rules have changed since.
    So ordinary edits never need a model call. `raw` is always taken from the current
    line, never from `previous` or a client.
    """
    reusable: dict[str, list[dict[str, Any]]] = {}
    for entry in previous or []:
        if (
            isinstance(entry, dict)
            and entry.get("parsedBy") == PARSED_BY_MODEL
            and isinstance(entry.get("raw"), str)
        ):
            reusable.setdefault(entry["raw"], []).append(entry)

    group: str | None = None
    parsed: list[dict[str, Any]] = []
    for line in lines:
        if not isinstance(line, str):
            parsed.append(_make_entry(str(line), group=group, parsed_by=None))
            continue

        header = detect_group_header(line)
        if header is not None:
            group = header
            parsed.append(_make_header_entry(line, header))
            continue

        kept = reusable.get(line)
        if kept:
            previous_entry = kept.pop(0)
            parsed.append(
                _make_entry(
                    line,
                    quantity=previous_entry.get("quantity"),
                    quantity_max=previous_entry.get("quantityMax"),
                    unit=previous_entry.get("unit"),
                    item=previous_entry.get("item"),
                    note=previous_entry.get("note"),
                    group=group,
                    parsed_by=PARSED_BY_MODEL,
                )
            )
            continue

        entry = parse_ingredient_line(line)
        entry["group"] = group
        parsed.append(entry)

    return parsed


def unparsed_lines(parsed: list[dict[str, Any]]) -> list[str]:
    """The non-blank raw lines nothing could parse."""
    return [e["raw"] for e in parsed if e.get("parsedBy") is None and str(e.get("raw", "")).strip()]
