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
    "Pantry": "peanut butter, almond butter, nut butter, cocoa butter, coconut milk, "
    "coconut cream, almond milk, oat milk, soy milk, condensed milk, evaporated milk, "
    "cream of tartar, rice paper, tomato puree, bread crumb, bay leaf",
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
    "Pantry": "allspice almond barley bean bouillon breadcrumb broth cashew cayenne "
    "cereal chickpea chili chilli chocolate cinnamon clove cocoa coconut coffee cornmeal "
    "cornstarch couscous cracker cumin curry extract flake flour gelatin granola "
    "hazelnut honey jam jelly juice ketchup lentil macaroni mayonnaise molasses mustard "
    "noodle nut nutmeg oat oats oil olive oregano paprika pasta paste peanut pecan "
    "pepper peppercorn pickle pistachio polenta powder quinoa raisin rice salsa salt "
    "sauce seasoning seed soda spaghetti spice starch stock sugar syrup tahini tea "
    "turmeric vanilla vinegar walnut water wine yeast",
    "Household": "battery bleach detergent foil napkin paper shampoo soap sponge tissue "
    "toothpaste towel",
}

_PHRASE_CATEGORY = {
    phrase: category for category, text in _PHRASES.items() for phrase in text.split(", ")
}
_WORD_CATEGORY = {word: category for category, text in _WORDS.items() for word in text.split()}


def guess_category(item_name: str) -> str | None:
    """
    The store category for an item name, or None when no word is recognised.

    "frozen", "canned", "tinned" and "dried" decide first. Then a known phrase, then
    single words from the last one back, because the last word usually names the thing:
    "chicken stock" is stock, "cherry tomatoes" are tomatoes.
    """
    words = [singularize_ingredient(word) for word in re.findall(r"[a-zà-ÿ]+", item_name.lower())]
    if "frozen" in words:
        return "Frozen"
    if {"canned", "tinned", "dried"} & set(words):
        return "Pantry"
    text = f" {' '.join(words)} "
    for phrase, category in _PHRASE_CATEGORY.items():
        if f" {phrase} " in text:
            return category
    for word in reversed(words):
        if word in _WORD_CATEGORY:
            return _WORD_CATEGORY[word]
    return None
