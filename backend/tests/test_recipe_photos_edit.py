"""Editing a recipe's photos: stored ones can be removed or reordered; uploads are checked."""

import base64
import io

from httpx2 import AsyncClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe


A = {"url": "https://example.com/a.jpg", "data": "QUFB", "mimeType": "image/jpeg"}
B = {"url": "https://example.com/b.jpg", "data": "QkJC", "mimeType": "image/jpeg"}
C = {"url": "", "data": "Q0ND", "mimeType": "image/png"}


async def _recipe_with_photos(client: AsyncClient, headers: dict, db: AsyncSession) -> int:
    created = (
        await client.post(
            "/api/v1/recipes/",
            json={"name": "Stew", "recipe_data": {"recipeIngredient": ["1 onion"]}},
            headers=headers,
        )
    ).json()
    # Photos arrive through imports; stored here directly
    recipe = (await db.execute(select(Recipe).where(Recipe.id == created["id"]))).scalar_one()
    recipe.recipe_data = {**recipe.recipe_data, "images": [A, B, C]}
    await db.commit()
    return int(created["id"])


async def _edit(client: AsyncClient, headers: dict, recipe_id: int, images=None, **extra):
    recipe_data = {"recipeIngredient": ["1 onion"], **extra}
    if images is not None:
        recipe_data["images"] = images
    return await client.patch(
        f"/api/v1/recipes/{recipe_id}", json={"recipe_data": recipe_data}, headers=headers
    )


async def test_photos_can_be_removed_and_reordered(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)

    response = await _edit(client, test_user_headers, recipe_id, images=[C, A])

    assert response.status_code == 200
    assert response.json()["recipe_data"]["images"] == [C, A]


async def test_every_photo_can_be_removed(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)

    response = await _edit(client, test_user_headers, recipe_id, images=[])

    assert response.json()["recipe_data"]["images"] == []


async def test_an_edit_without_a_photo_list_keeps_the_photos(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)

    response = await _edit(client, test_user_headers, recipe_id)

    assert response.json()["recipe_data"]["images"] == [A, B, C]


async def test_a_photo_the_recipe_does_not_have_is_refused(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)
    altered = {**A, "data": "ZXZpbA=="}

    response = await _edit(client, test_user_headers, recipe_id, images=[altered])

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"
    recipe = (await db.execute(select(Recipe).where(Recipe.id == recipe_id))).scalar_one()
    await db.refresh(recipe)
    assert recipe.recipe_data["images"] == [A, B, C]


async def test_more_than_five_photos_are_refused(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)

    response = await _edit(client, test_user_headers, recipe_id, images=[A, B, C, A, B, C])

    assert response.status_code == 400


async def test_a_photo_sent_twice_is_kept_once(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)

    response = await _edit(client, test_user_headers, recipe_id, images=[B, B])

    assert response.json()["recipe_data"]["images"] == [B]


async def test_a_new_recipe_cannot_bring_a_photo_with_an_address(
    client: AsyncClient, test_user_headers: dict
):
    response = await client.post(
        "/api/v1/recipes/",
        json={"name": "Stew", "recipe_data": {"recipeIngredient": ["1 onion"], "images": [A]}},
        headers=test_user_headers,
    )

    assert response.status_code == 400


def _picture(fmt: str = "JPEG", size: tuple[int, int] = (8, 6)) -> str:
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 80, 40)).save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode()


async def test_an_uploaded_photo_is_added(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)
    # The type is read from the picture, not taken from the request
    new = {"data": _picture("PNG"), "mimeType": "image/jpeg"}

    response = await _edit(client, test_user_headers, recipe_id, images=[new, A])

    assert response.status_code == 200
    assert response.json()["recipe_data"]["images"] == [
        {"url": "", "data": new["data"], "mimeType": "image/png"},
        A,
    ]


async def test_a_new_recipe_can_bring_an_uploaded_photo(
    client: AsyncClient, test_user_headers: dict
):
    new = {"url": "", "data": _picture(), "mimeType": "image/jpeg"}

    response = await client.post(
        "/api/v1/recipes/",
        json={"name": "Stew", "recipe_data": {"recipeIngredient": ["1 onion"], "images": [new]}},
        headers=test_user_headers,
    )

    assert response.status_code == 201
    assert response.json()["recipe_data"]["images"] == [new]


async def test_bad_uploads_are_refused(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)
    gif = _picture("GIF")
    not_a_picture = base64.b64encode(b"hello").decode()
    too_big = base64.b64encode(b"\xff" * (300 * 1024 + 1)).decode()

    for data in (gif, not_a_picture, too_big, "not base64!"):
        response = await _edit(
            client, test_user_headers, recipe_id, images=[{"data": data, "mimeType": "image/png"}]
        )
        assert response.status_code == 400, data[:20]


async def test_uploads_count_towards_five_photos(
    client: AsyncClient, test_user_headers: dict, db: AsyncSession
):
    recipe_id = await _recipe_with_photos(client, test_user_headers, db)
    one, two, three = ({"data": _picture(size=(n, n))} for n in (4, 5, 6))

    response = await _edit(client, test_user_headers, recipe_id, images=[A, B, C, one, two, three])

    assert response.status_code == 400
