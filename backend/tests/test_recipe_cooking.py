"""A recipe's household rating and last-cooked date."""

from httpx import AsyncClient
from sqlalchemy import select

from app.models.recipe import Recipe
from tests.test_backup_restore import _backup, _restore, _seed, _wipe
from tests.test_recipe_notes import RECIPES, _household, _login, _recipe


async def _cooking(client: AsyncClient, headers, recipe_id: int, body: dict):
    return await client.patch(f"{RECIPES}/{recipe_id}/cooking", json=body, headers=headers)


async def test_any_household_member_rates_and_marks_cooked(client: AsyncClient):
    owner, member = await _household(client)
    recipe_id = await _recipe(client, owner)

    rated = await _cooking(client, member, recipe_id, {"rating": 4})
    assert rated.json() == {"rating": 4, "last_cooked_on": None}

    # A field left out is not changed
    cooked = await _cooking(client, owner, recipe_id, {"last_cooked_on": "2026-11-26"})
    assert cooked.json() == {"rating": 4, "last_cooked_on": "2026-11-26"}

    recipe = (await client.get(f"{RECIPES}/{recipe_id}", headers=member)).json()
    assert (recipe["rating"], recipe["last_cooked_on"]) == (4, "2026-11-26")

    # null clears
    cleared = await _cooking(client, member, recipe_id, {"rating": None})
    assert cleared.json() == {"rating": None, "last_cooked_on": "2026-11-26"}


async def test_rating_must_be_one_to_five(client: AsyncClient):
    owner = await _login(client, "owner@example.com")
    recipe_id = await _recipe(client, owner)
    for rating in (0, 6):
        assert (await _cooking(client, owner, recipe_id, {"rating": rating})).status_code == 422


async def test_other_household_gets_404(client: AsyncClient):
    owner = await _login(client, "owner@example.com")
    stranger = await _login(client, "stranger@example.com")
    recipe_id = await _recipe(client, owner)

    assert (await _cooking(client, stranger, recipe_id, {"rating": 5})).status_code == 404


async def test_sorts_put_unrated_and_never_cooked_recipes_last(client: AsyncClient):
    owner = await _login(client, "owner@example.com")
    plain, older, newer = [await _recipe(client, owner) for _ in range(3)]
    await _cooking(client, owner, older, {"rating": 5, "last_cooked_on": "2026-11-01"})
    await _cooking(client, owner, newer, {"rating": 3, "last_cooked_on": "2026-11-20"})

    async def order(sort_by: str) -> list[int]:
        found = await client.get(f"{RECIPES}/search", params={"sort_by": sort_by}, headers=owner)
        return [r["id"] for r in found.json()["recipes"]]

    assert await order("recently_cooked") == [newer, older, plain]
    assert await order("rating_desc") == [older, newer, plain]


async def test_duplicate_starts_unrated(client: AsyncClient):
    owner = await _login(client, "owner@example.com")
    recipe_id = await _recipe(client, owner)
    await _cooking(client, owner, recipe_id, {"rating": 5, "last_cooked_on": "2026-11-01"})

    copy = (await client.post(f"{RECIPES}/{recipe_id}/duplicate", headers=owner)).json()

    assert (copy["rating"], copy["last_cooked_on"]) == (None, None)


async def test_backup_and_restore_keep_them(client, test_db, test_user_headers):
    await _seed(test_db)
    recipe = (await test_db.execute(select(Recipe))).scalar_one()
    await _cooking(
        client, test_user_headers, recipe.id, {"rating": 4, "last_cooked_on": "2026-11-20"}
    )
    content = await _backup(client, test_user_headers)
    await _wipe(test_db)

    assert (await _restore(client, test_user_headers, content)).status_code == 200

    test_db.expire_all()
    restored = (await test_db.execute(select(Recipe))).scalar_one()
    assert (restored.rating, str(restored.last_cooked_on)) == (4, "2026-11-20")
