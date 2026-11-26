"""What deleting an account does to shopping lists and meal plans."""

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.household import Household
from app.models.meal_plan import MealPlan, PlannedMeal
from app.models.shopping_list import ShoppingList, ShoppingListItem
from tests.test_recipe_notes import _household, _login


LISTS = "/api/v1/shopping-lists"
PLANS = "/api/v1/meal-plans"
WEEK = "2026-11-23"


async def _list_and_plan(client: AsyncClient, headers: dict[str, str]) -> int:
    """A shopping list with one item and a week with one meal, made by `headers`."""
    made = await client.post(f"{LISTS}/", json={"name": "Weekly"}, headers=headers)
    assert made.status_code == 201, made.text
    list_id = int(made.json()["id"])
    await client.post(f"{LISTS}/{list_id}/items", json={"item_name": "milk"}, headers=headers)
    plan = await client.get(f"{PLANS}/current", params={"week_start": WEEK}, headers=headers)
    added = await client.post(
        f"{PLANS}/{plan.json()['id']}/meals",
        json={"day_of_week": 0, "meal_type": "dinner", "title": "Leftovers"},
        headers=headers,
    )
    assert added.status_code == 201, added.text
    return list_id


async def test_a_members_lists_and_plans_stay_with_the_household(client: AsyncClient):
    owner, member = await _household(client)
    list_id = await _list_and_plan(client, member)

    deleted = await client.delete("/api/v1/users/me", headers=member)
    assert deleted.status_code == 200, deleted.text

    shown = await client.get(f"{LISTS}/{list_id}", headers=owner)
    assert shown.status_code == 200, shown.text
    assert [item["item_name"] for item in shown.json()["items"]] == ["milk"]
    assert shown.json()["created_by_name"] is None
    listed = await client.get(f"{LISTS}/", headers=owner)
    assert [summary["name"] for summary in listed.json()] == ["Weekly"]
    plan = await client.get(f"{PLANS}/current", params={"week_start": WEEK}, headers=owner)
    assert [meal["title"] for meal in plan.json()["planned_meals"]] == ["Leftovers"]


async def test_a_sole_users_lists_and_plans_go_with_the_account(
    client: AsyncClient, db: AsyncSession
):
    headers = await _login(client, "solo@example.com")
    await _list_and_plan(client, headers)

    deleted = await client.delete("/api/v1/users/me", headers=headers)
    assert deleted.status_code == 200, deleted.text

    for model in (Household, ShoppingList, ShoppingListItem, MealPlan, PlannedMeal):
        left = await db.scalar(select(func.count()).select_from(model))
        assert left == 0, model.__name__
