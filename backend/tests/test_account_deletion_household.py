"""Deleting an account must not take the household away from its other members."""

from httpx import AsyncClient

from tests.test_recipe_notes import RECIPES, _household, _recipe


async def test_owner_with_members_must_hand_over_before_deleting_account(client: AsyncClient):
    owner, member = await _household(client)
    await _recipe(client, member)

    refused = await client.delete("/api/v1/users/me", headers=owner)

    assert refused.status_code == 400, refused.text
    assert "ownership" in refused.json()["message"].lower()
    # The member still has their household and their recipe
    assert (await client.get("/api/v1/households/me", headers=member)).status_code == 200
    found = await client.get(f"{RECIPES}/search", headers=member)
    assert found.json()["total"] == 1


async def test_member_can_delete_account_and_the_household_stays(client: AsyncClient):
    owner, member = await _household(client)
    await _recipe(client, owner)

    deleted = await client.delete("/api/v1/users/me", headers=member)

    assert deleted.status_code == 200, deleted.text
    household = await client.get("/api/v1/households/me", headers=owner)
    assert household.status_code == 200
    assert (await client.get(f"{RECIPES}/search", headers=owner)).json()["total"] == 1
