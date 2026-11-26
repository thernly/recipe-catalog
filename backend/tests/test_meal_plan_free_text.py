"""A planned meal can be free text ("Leftovers") instead of a recipe."""

import json

from httpx import AsyncClient

from tests.test_backup_restore import _backup, _restore
from tests.test_recipe_notes import _login, _recipe


PLANS = "/api/v1/meal-plans"
WEEK = "2026-11-23"


async def _plan(client: AsyncClient, headers) -> dict:
    return (
        await client.get(f"{PLANS}/current", params={"week_start": WEEK}, headers=headers)
    ).json()


async def _add(client: AsyncClient, headers, plan_id: int, **fields):
    body = {"day_of_week": 0, "meal_type": "dinner", **fields}
    return await client.post(f"{PLANS}/{plan_id}/meals", json=body, headers=headers)


async def test_free_text_meal_is_added_listed_and_counted(client: AsyncClient):
    headers = await _login(client, "owner@example.com")
    plan = await _plan(client, headers)

    added = await _add(client, headers, plan["id"], title="  Leftovers  ")
    assert added.status_code == 201, added.text
    assert (added.json()["title"], added.json()["recipe_id"]) == ("Leftovers", None)

    shown = (await _plan(client, headers))["planned_meals"]
    assert [(m["title"], m["recipe_name"]) for m in shown] == [("Leftovers", None)]

    summaries = (await client.get(f"{PLANS}/", headers=headers)).json()
    assert [s["meal_count"] for s in summaries] == [1]


async def test_a_meal_needs_a_recipe_or_a_title_but_not_both(client: AsyncClient):
    headers = await _login(client, "owner@example.com")
    plan = await _plan(client, headers)
    recipe_id = await _recipe(client, headers)

    assert (await _add(client, headers, plan["id"])).status_code == 422
    assert (await _add(client, headers, plan["id"], title="   ")).status_code == 422
    both = await _add(client, headers, plan["id"], title="Leftovers", recipe_id=recipe_id)
    assert both.status_code == 422


async def test_a_meal_can_switch_between_recipe_and_free_text(client: AsyncClient):
    headers = await _login(client, "owner@example.com")
    plan = await _plan(client, headers)
    recipe_id = await _recipe(client, headers)
    meal_id = (await _add(client, headers, plan["id"], title="Eating out")).json()["id"]

    renamed = await client.patch(f"{PLANS}/{meal_id}", json={"title": "Takeaway"}, headers=headers)
    assert (renamed.json()["title"], renamed.json()["recipe_id"]) == ("Takeaway", None)

    cooked = await client.patch(
        f"{PLANS}/{meal_id}", json={"recipe_id": recipe_id}, headers=headers
    )
    assert (cooked.json()["title"], cooked.json()["recipe_name"]) == (None, "Soup")

    back = await client.patch(f"{PLANS}/{meal_id}", json={"title": "Leftovers"}, headers=headers)
    assert (back.json()["title"], back.json()["recipe_id"]) == ("Leftovers", None)


async def test_shopping_list_skips_free_text_meals(client: AsyncClient):
    headers = await _login(client, "owner@example.com")
    plan = await _plan(client, headers)
    recipe_id = await _recipe(client, headers)
    await _add(client, headers, plan["id"], title="Leftovers")
    await _add(client, headers, plan["id"], recipe_id=recipe_id, day_of_week=1)

    made = await client.post(
        "/api/v1/shopping-lists/from-meal-plan", json={"meal_plan_id": plan["id"]}, headers=headers
    )

    assert made.status_code == 200, made.text
    assert [i["item_name"] for i in made.json()["items"]] == ["stock"]


async def test_backup_and_restore_keep_free_text_meals(client: AsyncClient):
    headers = await _login(client, "owner@example.com")
    plan = await _plan(client, headers)
    await _add(client, headers, plan["id"], title="Leftovers")
    content = await _backup(client, headers)
    assert json.loads(content)["meal_plans"][0]["meals"][0]["title"] == "Leftovers"
    await client.delete(f"{PLANS}/{plan['id']}", headers=headers)

    assert (await _restore(client, headers, content)).status_code == 200
    # Restoring the same file again adds nothing
    assert (await _restore(client, headers, content)).status_code == 200

    shown = (await _plan(client, headers))["planned_meals"]
    assert [m["title"] for m in shown] == ["Leftovers"]
