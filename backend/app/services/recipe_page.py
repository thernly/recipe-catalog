"""
Find the recipe a web page publishes about itself.

Most recipe sites embed a schema.org Recipe as JSON-LD
(`<script type="application/ld+json">`). `extract_recipe` returns it in the plain
shape the importer takes, or None when the page has none.

ponytail: JSON-LD only. Pages that use Microdata/RDFa, or no markup at all, are
reported as "no recipe found"; the Recipe Siphon extension covers those.
"""

import json
from html.parser import HTMLParser
from typing import Any

from app.utils.recipe_display import display_steps
from app.utils.recipe_format import plain_text


# Copied as they are; the importer and clean_recipe_data validate and normalize them
_PASS_THROUGH = (
    "name",
    "description",
    "author",
    "datePublished",
    "recipeYield",
    "prepTime",
    "cookTime",
    "totalTime",
    "recipeCategory",
    "recipeCuisine",
    "keywords",
    "nutrition",
    "aggregateRating",
)
_MAX_DEPTH = 6  # how far into @graph / mainEntity nesting to look


class _JsonLdBlocks(HTMLParser):
    """Collects the text of every JSON-LD script element."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self._inside = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            kind = (dict(attrs).get("type") or "").strip().lower()
            self._inside = kind == "application/ld+json"
            if self._inside:
                self.blocks.append("")

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._inside = False

    def handle_data(self, data: str) -> None:
        if self._inside:
            self.blocks[-1] += data


def _find_recipe(node: Any, depth: int = 0) -> dict[str, Any] | None:
    if depth > _MAX_DEPTH:
        return None
    if isinstance(node, list):
        for child in node:
            if found := _find_recipe(child, depth + 1):
                return found
    elif isinstance(node, dict):
        types = node.get("@type")
        if "Recipe" in (types if isinstance(types, list) else [types]):
            return node
        return _find_recipe(node.get("@graph"), depth + 1) or _find_recipe(
            node.get("mainEntity"), depth + 1
        )
    return None


def _first_image(value: Any) -> list[str]:
    """Sites list several crops of one photo; each would be fetched and stored, so keep one."""
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        value = value.get("url")
    return [value] if isinstance(value, str) and value else []


def _lines(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    cleaned = (plain_text(v) for v in values if isinstance(v, str))
    return [line for line in cleaned if line]


def extract_recipe(page_html: str) -> dict[str, Any] | None:
    """Return the page's schema.org Recipe, simplified for the importer, or None."""
    parser = _JsonLdBlocks()
    parser.feed(page_html)

    recipe = None
    for block in parser.blocks:
        try:
            # strict=False: real pages put raw newlines inside JSON strings
            recipe = _find_recipe(json.loads(block, strict=False))
        except (ValueError, RecursionError):
            continue
        if recipe:
            break
    if not recipe:
        return None

    return {
        **{key: recipe[key] for key in _PASS_THROUGH if key in recipe},
        "image": _first_image(recipe.get("image")),
        "recipeIngredient": _lines(recipe.get("recipeIngredient") or recipe.get("ingredients")),
        "recipeInstructions": _lines(display_steps(recipe.get("recipeInstructions"))),
    }
