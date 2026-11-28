"""normalize_categories: what a typed or imported list of categories becomes."""

from app.core.constants import DEFAULT_CATEGORIES
from app.services.categories import MAX_CATEGORIES, normalize_categories


def test_splits_comma_and_semicolon_lists_and_strips_blanks():
    assert normalize_categories(["dinner, pastas; main course", " ", "", "Bread "]) == [
        "dinner",
        "pastas",
        "main course",
        "Bread",
    ]


def test_dedupes_case_insensitively_keeping_the_first_spelling():
    assert normalize_categories(["Soup", "soup", "SOUP", "Dinner"]) == ["Soup", "Dinner"]


def test_known_options_take_the_known_spelling():
    assert normalize_categories(["main course", "soup", "Weeknight"], DEFAULT_CATEGORIES) == [
        "Main Course",
        "Soup",
        "Weeknight",
    ]


def test_cuts_long_names_and_caps_the_count():
    long = "x" * 150
    assert normalize_categories([long]) == ["x" * 100]
    many = [f"c{i}" for i in range(30)]
    assert normalize_categories(many) == many[:MAX_CATEGORIES]


def test_ignores_entries_that_are_not_text():
    assert normalize_categories([None, 3, {"name": "Soup"}, "Soup"]) == ["Soup"]
