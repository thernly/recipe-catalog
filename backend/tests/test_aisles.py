"""Store categories guessed for shopping list items."""

import pytest

from app.services.aisles import _PHRASE_CATEGORY, _WORD_CATEGORY, DEFAULT_CATEGORIES, guess_category


@pytest.mark.parametrize(
    ("name", "category"),
    [
        ("cherry tomatoes", "Produce"),
        ("garlic cloves", "Produce"),
        ("red bell pepper", "Produce"),
        ("eggs", "Dairy"),
        ("unsalted butter", "Dairy"),
        ("peanut butter", "Oils & Condiments"),
        ("coconut milk", "Canned & Jarred"),
        ("chicken stock", "Canned & Jarred"),
        ("boneless chicken thighs", "Meat"),
        ("Olive Oil", "Oils & Condiments"),
        ("canned tomatoes", "Canned & Jarred"),
        # Pantry is dry goods only; the rest has its own section
        ("dry navy beans", "Pantry"),
        ("dried beans", "Pantry"),
        ("dried apricots", "Pantry"),
        ("spaghetti", "Pantry"),
        ("sunflower seeds", "Pantry"),
        ("tomato paste", "Canned & Jarred"),
        ("low-sodium chicken broth", "Canned & Jarred"),
        ("all-purpose flour", "Baking"),
        ("dark brown sugar", "Baking"),
        ("active dry yeast", "Baking"),
        ("baking soda", "Baking"),
        ("baking powder", "Baking"),
        ("molasses", "Baking"),
        ("coarse kosher salt", "Spices & Seasonings"),
        ("freshly ground black pepper", "Spices & Seasonings"),
        ("smoked paprika", "Spices & Seasonings"),
        ("bay leaves", "Spices & Seasonings"),
        ("sesame seeds", "Spices & Seasonings"),
        ("garlic powder", "Spices & Seasonings"),
        ("dried thyme", "Spices & Seasonings"),
        ("ground ginger", "Spices & Seasonings"),
        ("fresh thyme", "Produce"),
        ("ground beef", "Meat"),
        ("apple cider vinegar", "Oils & Condiments"),
        ("whole grain mustard", "Oils & Condiments"),
        ("worcestershire sauce", "Oils & Condiments"),
        ("dark english ale", "Drinks"),
        ("orange juice", "Drinks"),
        ("lemon juice", "Produce"),
        ("sparkling water", "Drinks"),
        ("frozen peas", "Frozen"),
        ("ice cream", "Frozen"),
        ("burger buns", "Bakery"),
        ("paper towels", "Household"),
        ("gochujang", None),
        ("eggplant", "Produce"),  # whole words only: not "egg"
    ],
)
def test_guess_category(name, category):
    assert guess_category(name) == category


def test_every_guess_is_a_default_category():
    assert set(_WORD_CATEGORY.values()) | set(_PHRASE_CATEGORY.values()) <= set(DEFAULT_CATEGORIES)


async def test_items_are_shown_in_a_guessed_category_until_one_is_picked(client, test_user_headers):
    created = await client.post(
        "/api/v1/shopping-lists/", json={"name": "Weekly"}, headers=test_user_headers
    )
    list_id = created.json()["id"]
    added = await client.post(
        f"/api/v1/shopping-lists/{list_id}/items",
        json={"item_name": "carrots"},
        headers=test_user_headers,
    )
    assert added.json()["category"] == "Produce"

    changed = await client.patch(
        f"/api/v1/shopping-lists/items/{added.json()['id']}",
        json={"category": "Other"},
        headers=test_user_headers,
    )
    assert changed.json()["category"] == "Other"

    fetched = await client.get(f"/api/v1/shopping-lists/{list_id}", headers=test_user_headers)
    assert [i["category"] for i in fetched.json()["items"]] == ["Other"]
