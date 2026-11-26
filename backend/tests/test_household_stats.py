"""Stats tell a person's own counts apart from what their household can see."""

from httpx import AsyncClient

from tests.test_recipe_notes import _household, _recipe


async def test_member_of_a_full_household_does_not_see_zero_recipes(client: AsyncClient):
    owner, member = await _household(client)
    await _recipe(client, owner)
    await _recipe(client, owner)

    stats = (await client.get("/api/v1/users/me/stats", headers=member)).json()

    # The member added nothing, but can see the owner's two recipes
    assert stats["total_recipes"] == 0
    assert stats["household_recipes"] == 2


async def test_household_counts_leave_out_trash(client: AsyncClient):
    owner, member = await _household(client)
    await _recipe(client, owner)
    binned = await _recipe(client, member)
    await client.delete(f"/api/v1/recipes/{binned}", headers=member)

    stats = (await client.get("/api/v1/users/me/stats", headers=owner)).json()

    assert stats["household_recipes"] == 1
    assert stats["household_collections"] >= 1  # at least the default Favorites
