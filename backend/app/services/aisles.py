"""Guess which part of the shop a shopping list item is found in."""

import re

from app.services.ingredient_parser import singularize_ingredient


# Default store categories, in the order the list shows its sections
DEFAULT_CATEGORIES = [
    "Produce",
    "Dairy",
    "Meat",
    "Bakery",
    "Frozen",
    "Pantry",
    "Canned & Jarred",
    "Baking",
    "Spices & Seasonings",
    "Oils & Condiments",
    "Drinks",
    "Household",
    "Other",
]

# Names whose last known word would file them in the wrong place: "peanut butter" is
# not dairy, "garlic cloves" are not a spice.
_PHRASES = {
    "Produce": "bell pepper, chili pepper, chilli pepper, lemon juice, lime juice, "
    "green bean, garlic clove",
    "Dairy": "half and half",
    "Frozen": "ice cream, puff pastry, filo pastry, phyllo dough",
    "Pantry": "almond milk, oat milk, soy milk, rice paper, bread crumb, corn flake, "
    "sunflower seed, pumpkin seed, chia seed, flax seed",
    "Canned & Jarred": "coconut milk, coconut cream, tomato puree, tomato sauce",
    "Baking": "baking soda, bicarbonate of soda, baking powder, cocoa powder, milk powder, "
    "custard powder, cocoa butter, condensed milk, evaporated milk, cream of tartar",
    "Spices & Seasonings": "bay leaf",
    "Oils & Condiments": "peanut butter, almond butter, nut butter",
    "Household": "plastic wrap, cling film",
}

# ponytail: hand-picked word lists, matched on whole singular words; extend as misses turn up
_WORDS = {
    "Produce": "apple apricot artichoke arugula asparagus aubergine avocado banana basil "
    "beet beetroot berry blackberry blueberry broccoli cabbage cantaloupe carrot "
    "cauliflower celery chard cherry chive cilantro clementine coriander corn courgette "
    "cranberry cucumber dill eggplant endive fennel fig garlic ginger grape grapefruit "
    "greens herb jalapeno jalapeño kale leek lemon lemongrass lettuce lime mango melon "
    "mint mushroom nectarine onion orange parsley parsnip peach pear pea pineapple plum "
    "pomegranate potato pumpkin radish raspberry rhubarb rocket rosemary sage salad "
    "scallion shallot spinach sprout squash strawberry tarragon thyme tofu tomato "
    "turnip watercress watermelon yam zucchini",
    "Dairy": "butter buttermilk cheddar cheese cream creme egg feta ghee gouda halloumi "
    "kefir margarine mascarpone milk mozzarella paneer parmesan ricotta yoghurt yogurt",
    "Meat": "anchovy bacon beef breast brisket chicken chop chorizo clam cod crab duck "
    "fillet fish ham lamb lobster mince mussel pancetta pork prawn prosciutto salami "
    "salmon sausage scallop shrimp sirloin steak thigh tuna turkey veal wing",
    "Bakery": "bagel baguette bread brioche bun ciabatta croissant focaccia loaf muffin "
    "naan pita pitta roll sourdough tortilla wrap",
    "Pantry": "almond barley bean breadcrumb cashew cereal chickpea coconut cornmeal "
    "couscous cracker granola hazelnut lentil macaroni noodle nut oat oats pasta peanut "
    "pecan pistachio polenta quinoa raisin rice spaghetti walnut",
    "Canned & Jarred": "bouillon broth olive passata paste stock",
    "Baking": "chocolate cocoa cornstarch flour gelatin icing molasses starch sugar syrup "
    "treacle yeast",
    "Spices & Seasonings": "allspice anise cardamom cayenne chili chilli cinnamon clove "
    "cumin curry extract fenugreek flake nutmeg oregano paprika pepper peppercorn powder "
    "saffron salt seasoning seed spice sumac turmeric vanilla",
    "Oils & Condiments": "chutney dressing honey jam jelly ketchup marmalade mayonnaise "
    "mustard oil pickle salsa sauce tahini vinegar",
    "Drinks": "ale beer cider coffee juice lager soda tea water wine",
    "Household": "battery bleach detergent foil napkin paper shampoo soap sponge tissue "
    "toothpaste towel",
}

# Fresh these are produce; "dried thyme" and "ground ginger" are jars on the spice shelf
_SPICE_WHEN_DRIED = {
    "basil", "chive", "cilantro", "coriander", "dill", "garlic", "ginger", "herb", "mint",
    "onion", "parsley", "rosemary", "sage", "tarragon", "thyme",
}  # fmt: skip

_PHRASE_CATEGORY = {
    phrase: category for category, text in _PHRASES.items() for phrase in text.split(", ")
}
_WORD_CATEGORY = {word: category for category, text in _WORDS.items() for word in text.split()}


def guess_category(item_name: str) -> str | None:
    """
    The store category for an item name, or None when no word is recognised.

    "frozen", "canned" and "tinned" decide first, then a dried or ground herb. Then a
    known phrase, then single words from the last one back, because the last word
    usually names the thing: "chicken stock" is stock, "cherry tomatoes" are tomatoes.
    Anything else dried is a dry good: "dried apricots" are not produce.
    """
    words = [singularize_ingredient(word) for word in re.findall(r"[a-zà-ÿ]+", item_name.lower())]
    if "frozen" in words:
        return "Frozen"
    if {"canned", "tinned"} & set(words):
        return "Canned & Jarred"
    if {"dried", "ground"} & set(words) and _SPICE_WHEN_DRIED & set(words):
        return "Spices & Seasonings"
    text = f" {' '.join(words)} "
    category = next(
        (c for phrase, c in _PHRASE_CATEGORY.items() if f" {phrase} " in text), None
    ) or next((_WORD_CATEGORY[w] for w in reversed(words) if w in _WORD_CATEGORY), None)
    if "dried" in words and category != "Spices & Seasonings":
        return "Pantry"
    return category
