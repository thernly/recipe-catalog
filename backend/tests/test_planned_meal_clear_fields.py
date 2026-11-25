"""Servings and notes on a planned meal can be cleared, not only changed."""


async def test_planned_meal_servings_and_notes_can_be_cleared(client, test_user_headers):
    recipe = await client.post(
        "/api/v1/recipes/", headers=test_user_headers, json={"name": "Soup", "recipe_data": {}}
    )
    plan = (await client.get("/api/v1/meal-plans/current", headers=test_user_headers)).json()
    meal = await client.post(
        f"/api/v1/meal-plans/{plan['id']}/meals",
        headers=test_user_headers,
        json={
            "recipe_id": recipe.json()["id"],
            "day_of_week": 0,
            "meal_type": "dinner",
            "servings": 6,
            "notes": "double the garlic",
        },
    )
    assert meal.status_code == 201, meal.text
    url = f"/api/v1/meal-plans/{meal.json()['id']}"

    # A field left out of the request is untouched.
    moved = await client.patch(url, headers=test_user_headers, json={"day_of_week": 2})
    assert moved.status_code == 200, moved.text
    assert (moved.json()["servings"], moved.json()["notes"]) == (6, "double the garlic")

    cleared = await client.patch(
        url, headers=test_user_headers, json={"servings": None, "notes": None}
    )
    assert cleared.status_code == 200, cleared.text
    assert (cleared.json()["servings"], cleared.json()["notes"]) == (None, None)
    assert cleared.json()["day_of_week"] == 2
