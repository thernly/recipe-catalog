"""
Hand-written ingredient lines covering each pattern the parser handles (design doc §8,
the in-repo half of the eval set). Real recipes stay outside git; see
app/services/intake_eval.py.
"""

import pytest

from app.services.ingredient_parser import (
    PARSED_BY_MODEL,
    PARSED_BY_REGEX,
    detect_group_header,
    parse_ingredient_line,
    parse_ingredient_lines,
    unparsed_lines,
)


# (raw, quantity, quantityMax, unit, item, note)
PARSED_LINES = [
    # Plain quantity + unit + item
    ("2 cups flour", 2, None, "cup", "flour", None),
    ("1 tsp salt", 1, None, "teaspoon", "salt", None),
    ("3 Tbsp butter", 3, None, "tablespoon", "butter", None),
    ("1 1/2 tbsp. olive oil", 1.5, None, "tablespoon", "olive oil", None),
    ("8 oz cream cheese", 8, None, "ounce", "cream cheese", None),
    ("2 lbs chicken thighs", 2, None, "pound", "chicken thighs", None),
    ("2 fl. oz. cream", 2, None, "fluid ounce", "cream", None),
    ("1 c. sugar", 1, None, "cup", "sugar", None),
    ("1 qt chicken stock", 1, None, "quart", "chicken stock", None),
    # Fractions, decimals, unicode
    ("1/2 cup milk", 0.5, None, "cup", "milk", None),
    ("0.75 cup water", 0.75, None, "cup", "water", None),
    ("½ cup milk", 0.5, None, "cup", "milk", None),
    ("1½ cups milk", 1.5, None, "cup", "milk", None),
    ("1 ¼ cups stock", 1.25, None, "cup", "stock", None),
    ("1/3 cup honey", 0.333, None, "cup", "honey", None),
    # Attached units
    ("500g plain flour", 500, None, "gram", "plain flour", None),
    ("250ml milk", 250, None, "milliliter", "milk", None),
    # Ranges
    ("1-2 cloves garlic", 1, 2, "clove", "garlic", None),
    ("1–2 tsp chili flakes", 1, 2, "teaspoon", "chili flakes", None),
    ("2 to 3 tablespoons lemon juice", 2, 3, "tablespoon", "lemon juice", None),
    ("1 or 2 bay leaves", 1, 2, None, "bay leaves", None),
    # No unit
    ("3 eggs", 3, None, None, "eggs", None),
    ("3 large eggs", 3, None, None, "large eggs", None),
    ("2 carrots, peeled and diced", 2, None, None, "carrots", "peeled and diced"),
    # Number words and articles before a unit
    ("one onion, diced", 1, None, None, "onion", "diced"),
    ("a pinch of salt", 1, None, "pinch", "salt", None),
    ("an 8 oz block feta", None, None, None, None, None),  # see UNPARSED_LINES
    # Notes after a comma
    ("2 cups flour, sifted", 2, None, "cup", "flour", "sifted"),
    ("1 cup butter, softened, cubed", 1, None, "cup", "butter", "softened, cubed"),
    # Notes in parentheses
    ("1 cup milk (warm)", 1, None, "cup", "milk", "warm"),
    ("1 cup (240 ml) milk", 1, None, "cup", "milk", "240 ml"),
    ("1 cup sugar (optional)", 1, None, "cup", "sugar", "optional"),
    ("2 onions (about 1 lb), sliced", 2, None, None, "onions", "about 1 lb; sliced"),
    # Nested parentheses stay together in one note
    (
        "1 medium turnip (peeled and diced (about 300–350g))",
        1,
        None,
        None,
        "medium turnip",
        "peeled and diced (about 300-350g)",
    ),
    ("1 cup stock (low sodium) (or water)", 1, None, "cup", "stock", "low sodium; or water"),
    (
        "1 large parsnip (grated (1 cup / 90 g))",
        1,
        None,
        None,
        "large parsnip",
        "grated (1 cup / 90 g)",
    ),
    # Range with a space on one side of the dash, plus nested parentheses
    ("1 –2 cups fresh dill (chopped (15–25g))", 1, 2, "cup", "fresh dill", "chopped (15-25g)"),
    # Alternative measures after a slash
    (
        "2 sticks/1 cup (226 grams) unsalted butter, cubed and kept cold",
        2,
        None,
        "stick",
        "unsalted butter",
        "1 cup; 226 grams; cubed and kept cold",
    ),
    ("8 oz / 225 g cheddar, grated", 8, None, "ounce", "cheddar", "225 g; grated"),
    ("1 cup/240ml milk", 1, None, "cup", "milk", "240 ml"),
    ("2/3 cup sugar", 0.667, None, "cup", "sugar", None),
    # Additions after "plus" or "+": first measure kept, the rest goes to the note
    ("1 cup plus 2 tablespoons sugar", 1, None, "cup", "sugar", "plus 2 tablespoons"),
    (
        "1/3 cup plus 1 tablespoon walnut oil (preferably toasted)",
        0.333,
        None,
        "cup",
        "walnut oil",
        "plus 1 tablespoon; preferably toasted",
    ),
    ("2 tbsp + 1 tsp honey", 2, None, "tablespoon", "honey", "plus 1 tsp"),
    # Package sizes
    ("1 (14-ounce) can diced tomatoes", 1, None, "can", "diced tomatoes", "14-ounce"),
    ("1 15-ounce can black beans, rinsed", 1, None, "can", "black beans", "15-ounce; rinsed"),
    # "of" after the unit
    ("2 cups of flour", 2, None, "cup", "flour", None),
    # Trailing notes without a comma
    ("salt and pepper to taste", None, None, None, "salt and pepper", "to taste"),
    ("parsley for garnish", None, None, None, "parsley", "for garnish"),
    # No quantity
    ("Salt", None, None, None, "Salt", None),
    ("pinch of nutmeg", None, None, "pinch", "nutmeg", None),
    # Quantity after a comma
    ("Butter, 2 tablespoons", 2, None, "tablespoon", "Butter", None),
    ("Eggs, 3", 3, None, None, "Eggs", None),
    # Bullets and checkbox glyphs from scraped pages
    ("▢ 2 cups flour", 2, None, "cup", "flour", None),
    ("• 1 tsp vanilla extract", 1, None, "teaspoon", "vanilla extract", None),
    # Extra whitespace
    ("2   cups    flour ", 2, None, "cup", "flour", None),
]

UNPARSED_LINES = [
    "",
    "   ",
    "Juice of 1 lemon",
    "1 cup plus a little more sugar",
    "2 cups",
    "an 8 oz block feta",
    "1 cup (240 ml milk",
    "1 cup milk) warm",
    "1 turnip (peeled (about 300g)",
    "Mix the flour and the sugar together in a large bowl and set aside until needed later on",
    "2 eggs or 3 egg whites",
]


@pytest.mark.parametrize(
    ("raw", "quantity", "quantity_max", "unit", "item", "note"),
    [line for line in PARSED_LINES if line[4] is not None],
)
def test_parsed_lines(raw, quantity, quantity_max, unit, item, note):
    entry = parse_ingredient_line(raw)

    assert entry["parsedBy"] == PARSED_BY_REGEX, entry
    assert entry["raw"] == raw
    if quantity is None:
        assert entry["quantity"] is None
    else:
        assert entry["quantity"] == pytest.approx(quantity, abs=0.001)
    assert entry["quantityMax"] == quantity_max
    assert entry["unit"] == unit
    assert entry["item"] == item
    assert entry["note"] == note
    assert entry["group"] is None


@pytest.mark.parametrize("raw", UNPARSED_LINES)
def test_unparsed_lines(raw):
    entry = parse_ingredient_line(raw)

    assert entry == {
        "raw": raw,
        "quantity": None,
        "quantityMax": None,
        "unit": None,
        "item": None,
        "note": None,
        "group": None,
        "parsedBy": None,
    }


def test_whole_numbers_are_ints():
    entry = parse_ingredient_line("2 cups flour")
    assert isinstance(entry["quantity"], int)


@pytest.mark.parametrize(
    ("line", "group"),
    [
        ("For the dressing:", "For the dressing"),
        ("Dressing:", "Dressing"),
        ("FILLING", "FILLING"),
        ("--- Sauce ---", "Sauce"),
        ("** Topping **", "Topping"),
        ("For the crust", "For the crust"),
        ("For the glaze :", "For the glaze"),
    ],
)
def test_group_headers(line, group):
    assert detect_group_header(line) == group


@pytest.mark.parametrize(
    "line",
    [
        "2 cups flour",
        "salt and pepper",
        "For the sauce: 2 tbsp soy sauce",
        "1/2 cup sugar:",
        "Olive oil, for frying",
        "",
    ],
)
def test_not_group_headers(line):
    assert detect_group_header(line) is None


def test_lines_get_groups_from_headers():
    parsed = parse_ingredient_lines(
        [
            "2 cups flour",
            "For the dressing:",
            "1/4 cup olive oil",
            "1 tbsp vinegar",
            "TOPPING",
            "1 cup nuts",
        ]
    )

    assert [e["group"] for e in parsed] == [
        None,
        "For the dressing",
        "For the dressing",
        "For the dressing",
        "TOPPING",
        "TOPPING",
    ]
    # A header is marked as one and carries no ingredient fields
    assert parsed[1] == {
        "raw": "For the dressing:",
        "header": True,
        "group": "For the dressing",
        "parsedBy": PARSED_BY_REGEX,
    }
    assert "header" not in parsed[2]
    assert parsed[2]["item"] == "olive oil"


def test_one_entry_per_line_in_order():
    lines = ["2 cups flour", "Juice of 1 lemon", "", "1 tsp salt"]
    parsed = parse_ingredient_lines(lines)

    assert [e["raw"] for e in parsed] == lines
    assert unparsed_lines(parsed) == ["Juice of 1 lemon"]


def test_non_string_lines_are_kept_unparsed():
    parsed = parse_ingredient_lines([{"name": "flour"}, 3])

    assert [e["parsedBy"] for e in parsed] == [None, None]
    assert parsed[1]["raw"] == "3"


def _model_entry(raw: str, **fields):
    return {
        "raw": raw,
        "quantity": None,
        "quantityMax": None,
        "unit": None,
        "item": None,
        "note": None,
        "group": None,
        "parsedBy": PARSED_BY_MODEL,
        **fields,
    }


def test_unchanged_lines_keep_model_parses():
    previous = [
        _model_entry("Juice of 1 lemon", quantity=1, item="lemon", note="juiced"),
        {"raw": "2 cups flour", "item": "WRONG", "parsedBy": PARSED_BY_REGEX},
    ]
    parsed = parse_ingredient_lines(
        ["For the sauce:", "2 cups flour", "Juice of 1 lemon"], previous
    )

    # The model entry is kept and takes the current group
    assert parsed[2]["parsedBy"] == PARSED_BY_MODEL
    assert parsed[2]["item"] == "lemon"
    assert parsed[2]["group"] == "For the sauce"
    # Regex entries are recomputed, never copied
    assert parsed[1]["item"] == "flour"


def test_changed_lines_are_reparsed_by_regex():
    previous = [_model_entry("Juice of 1 lemon", quantity=1, item="lemon")]
    parsed = parse_ingredient_lines(["Juice of 2 lemons"], previous)

    assert parsed[0]["parsedBy"] is None
    assert parsed[0]["raw"] == "Juice of 2 lemons"


def test_duplicate_raw_lines_reuse_in_order():
    previous = [
        _model_entry("Juice of 1 lemon", note="first"),
        _model_entry("Juice of 1 lemon", note="second"),
    ]
    parsed = parse_ingredient_lines(
        ["Juice of 1 lemon", "Juice of 1 lemon", "Juice of 1 lemon"], previous
    )

    assert [e["note"] for e in parsed] == ["first", "second", None]
    assert [e["parsedBy"] for e in parsed] == [PARSED_BY_MODEL, PARSED_BY_MODEL, None]


def test_malformed_previous_entries_are_ignored():
    parsed = parse_ingredient_lines(["2 cups flour"], ["junk", {"parsedBy": PARSED_BY_MODEL}])
    assert parsed[0]["item"] == "flour"
