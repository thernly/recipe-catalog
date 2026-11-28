"""GET /recipes/{id}/photo serves the stored main photo, so lists never hotlink it."""

import base64

from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe


PICTURE = b"\xff\xd8\xff\xe0 a jpeg"
PHOTO = {
    "url": "https://example.com/gone.jpg",
    "data": base64.b64encode(PICTURE).decode(),
    "mimeType": "image/jpeg",
}


async def _recipe(client: AsyncClient, headers: dict, db: AsyncSession, images: list) -> int:
    created = (
        await client.post(
            "/api/v1/recipes/",
            json={
                "name": "Grissini",
                "image_url": "https://example.com/gone.jpg",
                "recipe_data": {"recipeIngredient": ["flour"]},
            },
            headers=headers,
        )
    ).json()
    # Photos arrive through imports; stored here directly
    recipe = (await db.execute(select(Recipe).where(Recipe.id == created["id"]))).scalar_one()
    recipe.recipe_data = {**recipe.recipe_data, "images": images}
    await db.commit()
    return int(created["id"])


async def _headers_for(client: AsyncClient, email: str) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123!", "display_name": "Other"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"}
    )
    return {"Authorization": f"Bearer {login.cookies.get('access_token')}"}


async def test_serves_the_stored_main_photo(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe(client, test_user_headers, db, [PHOTO])

    response = await client.get(f"/api/v1/recipes/{recipe_id}/photo", headers=test_user_headers)

    assert response.status_code == 200
    assert response.content == PICTURE
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == "private, no-cache"


async def test_an_unchanged_photo_is_not_sent_again(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe(client, test_user_headers, db, [PHOTO])
    url = f"/api/v1/recipes/{recipe_id}/photo"
    etag = (await client.get(url, headers=test_user_headers)).headers["etag"]

    again = await client.get(url, headers={**test_user_headers, "If-None-Match": etag})

    assert again.status_code == 304
    assert again.content == b""


async def test_list_says_which_recipes_have_a_stored_photo(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    with_photo = await _recipe(client, test_user_headers, db, [PHOTO])
    address_only = await _recipe(client, test_user_headers, db, [{**PHOTO, "data": ""}])

    listed = (await client.get("/api/v1/recipes/search", headers=test_user_headers)).json()

    flags = {r["id"]: r["has_photo"] for r in listed["recipes"]}
    assert flags == {with_photo: True, address_only: False}


async def test_no_stored_photo_is_not_found(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe(client, test_user_headers, db, [{**PHOTO, "data": ""}])

    response = await client.get(f"/api/v1/recipes/{recipe_id}/photo", headers=test_user_headers)

    assert response.status_code == 404


async def test_only_image_types_are_served(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    page = {**PHOTO, "mimeType": "text/html"}
    recipe_id = await _recipe(client, test_user_headers, db, [page])

    response = await client.get(f"/api/v1/recipes/{recipe_id}/photo", headers=test_user_headers)

    assert response.status_code == 404


async def test_another_household_cannot_see_the_photo(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe(client, test_user_headers, db, [PHOTO])
    stranger = await _headers_for(client, "stranger@example.com")

    response = await client.get(f"/api/v1/recipes/{recipe_id}/photo", headers=stranger)

    assert response.status_code == 404
