"""Saving a recipe from a web address: the page's own schema.org Recipe is imported."""

import json

import pytest
from httpx import AsyncClient

from app.services.recipe_page import extract_recipe
from app.utils.safe_fetch import FetchResult, SafeFetchError


URL = "/api/v1/import/url"
PAGE_URL = "https://example.com/dal"

RECIPE = {
    "@context": "https://schema.org",
    "@type": "Recipe",
    "name": "Mum&#39;s Dal",
    "description": "A weeknight dal.",
    "image": [
        {"@type": "ImageObject", "url": "https://example.com/dal-1x1.jpg"},
        "https://example.com/dal-4x3.jpg",
    ],
    "recipeYield": "4 servings",
    "totalTime": "PT40M",
    "recipeIngredient": ["1 cup red lentils", "  ", "salt &amp; pepper"],
    "recipeInstructions": [
        {"@type": "HowToStep", "text": "Rinse the lentils."},
        {
            "@type": "HowToSection",
            "name": "For the tarka",
            "itemListElement": [{"@type": "HowToStep", "text": "<p>Fry the cumin.</p>"}],
        },
    ],
    "comment": [{"@type": "Comment", "text": "Loved it", "author": {"name": "A reader"}}],
}


def _page(*blocks: object) -> str:
    scripts = "".join(
        f'<script type="application/ld+json">{block if isinstance(block, str) else json.dumps(block)}</script>'
        for block in blocks
    )
    return f"<html><head><title>Dal</title>{scripts}</head><body><p>Dal</p></body></html>"


def test_extracts_and_simplifies_the_recipe():
    recipe = extract_recipe(_page(RECIPE))

    assert recipe is not None
    assert recipe["name"] == "Mum&#39;s Dal"  # the importer cleans the name itself
    assert recipe["recipeIngredient"] == ["1 cup red lentils", "salt & pepper"]
    assert recipe["recipeInstructions"] == [
        "Rinse the lentils.",
        "For the tarka",
        "Fry the cumin.",
    ]
    # One photo, not every crop of it
    assert recipe["image"] == ["https://example.com/dal-1x1.jpg"]
    assert (recipe["recipeYield"], recipe["totalTime"]) == ("4 servings", "PT40M")
    # A page's reader comments are not this household's notes
    assert "comment" not in recipe


@pytest.mark.parametrize(
    "blocks",
    [
        ({"@context": "https://schema.org", "@graph": [{"@type": "WebSite"}, RECIPE]},),
        ([{"@type": "BreadcrumbList"}, RECIPE],),
        ({"@type": "WebPage", "mainEntity": RECIPE},),
        ({**RECIPE, "@type": ["Recipe", "NewsArticle"]},),
        ("{ this is not json", RECIPE),
    ],
    ids=["graph", "list", "main-entity", "type-list", "after-a-broken-block"],
)
def test_finds_the_recipe_wherever_the_page_puts_it(blocks):
    recipe = extract_recipe(_page(*blocks))

    assert recipe is not None
    assert recipe["recipeIngredient"][0] == "1 cup red lentils"


def test_a_page_without_a_recipe_gives_none():
    assert extract_recipe(_page({"@type": "Article", "name": "News"})) is None
    assert extract_recipe("<html><body>No data here</body></html>") is None


@pytest.fixture
def fake_web(monkeypatch):
    """Serve `pages` (address -> HTML) in place of the network; anything else fails."""
    pages: dict[str, str] = {}

    async def fetch(url: str, **_: object) -> FetchResult:
        if url not in pages:
            raise SafeFetchError("Upstream returned HTTP 404")
        return FetchResult(url=url, content=pages[url].encode(), content_type="text/html")

    monkeypatch.setattr("app.api.import_recipes.safe_fetch", fetch)
    monkeypatch.setattr("app.utils.recipe_format.safe_fetch", fetch)
    return pages


async def test_saves_the_recipe_from_a_web_address(
    client: AsyncClient, test_user_headers, fake_web
):
    fake_web[PAGE_URL] = _page(RECIPE)

    response = await client.post(URL, json={"url": f"  {PAGE_URL} "}, headers=test_user_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "created"
    saved = (await client.get(f"/api/v1/recipes/{body['id']}", headers=test_user_headers)).json()
    assert saved["name"] == "Mum's Dal"
    assert saved["source_url"] == PAGE_URL
    assert saved["total_time_minutes"] == 40
    assert saved["recipe_data"]["recipeIngredient"] == ["1 cup red lentils", "salt & pepper"]
    # Every write path runs clean_recipe_data
    assert saved["recipe_data"]["parsedIngredients"][0]["item"] == "red lentils"


async def test_the_same_address_twice_is_skipped(client: AsyncClient, test_user_headers, fake_web):
    fake_web[PAGE_URL] = _page(RECIPE)
    first = await client.post(URL, json={"url": PAGE_URL}, headers=test_user_headers)

    second = await client.post(URL, json={"url": PAGE_URL}, headers=test_user_headers)

    assert second.status_code == 200, second.text
    assert second.json()["status"] == "skipped"
    assert second.json()["id"] == first.json()["id"]


async def test_a_page_that_cannot_be_fetched_is_a_clear_error(
    client: AsyncClient, test_user_headers, fake_web
):
    response = await client.post(
        URL, json={"url": "https://example.com/gone"}, headers=test_user_headers
    )

    assert response.status_code == 400
    assert "could not be opened" in response.json()["message"]


async def test_a_page_without_a_recipe_is_a_clear_error(
    client: AsyncClient, test_user_headers, fake_web
):
    fake_web[PAGE_URL] = _page({"@type": "Article", "name": "News"})

    response = await client.post(URL, json={"url": PAGE_URL}, headers=test_user_headers)

    assert response.status_code == 400
    assert "No recipe was found" in response.json()["message"]


@pytest.mark.parametrize("url", ["javascript:alert(1)", "ftp://example.com/dal", "dal"])
async def test_only_web_addresses_are_accepted(
    client: AsyncClient, test_user_headers, fake_web, url: str
):
    response = await client.post(URL, json={"url": url}, headers=test_user_headers)

    assert response.status_code == 400
    assert "http" in response.json()["message"]


async def test_requires_sign_in(client: AsyncClient):
    response = await client.post(URL, json={"url": PAGE_URL})

    assert response.status_code == 401
