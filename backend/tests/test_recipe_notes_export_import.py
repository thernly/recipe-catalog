"""Recipe notes in every export format, and restored on import."""

import json
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.utils import pdf_export
from app.utils.recipe_format import MAX_IMPORTED_NOTES, notes_from_schema
from tests.test_recipe_notes import RECIPES, _add, _household, _login, _recipe


async def _recipe_with_notes(client: AsyncClient) -> tuple[dict, dict, int]:
    """Olive's recipe with a note from Olive, then one from Milo."""
    owner, member = await _household(client)
    recipe_id = await _recipe(client, owner)
    await _add(client, owner, recipe_id, "Needs more salt")
    await _add(client, member, recipe_id, "Halved the sugar,\nstill sweet")
    return owner, member, recipe_id


async def _export(client: AsyncClient, headers: dict, recipe_id: int, fmt: str):
    response = await client.get(f"{RECIPES}/{recipe_id}/export?format={fmt}", headers=headers)
    assert response.status_code == 200, response.text
    return response


async def test_json_export_uses_schema_org_comments(client: AsyncClient):
    owner, _, recipe_id = await _recipe_with_notes(client)

    exported = json.loads((await _export(client, owner, recipe_id, "json")).text)

    comments = exported["comment"]
    # Oldest first, like a log
    assert [(c["author"]["name"], c["text"]) for c in comments] == [
        ("Olive", "Needs more salt"),
        ("Milo", "Halved the sugar,\nstill sweet"),
    ]
    assert comments[0]["@type"] == "Comment"
    assert comments[0]["author"]["@type"] == "Person"
    assert datetime.fromisoformat(comments[0]["dateCreated"]).tzinfo is not None
    # Notes are not mixed into the recipe's own "Notes & Tips"
    assert exported["notes"] == ""


async def test_markdown_and_text_exports_have_a_cooking_notes_section(client: AsyncClient):
    owner, _, recipe_id = await _recipe_with_notes(client)

    markdown = (await _export(client, owner, recipe_id, "markdown")).text
    assert "## Cooking Notes" in markdown
    assert "- **Milo, " in markdown
    assert " UTC:** Halved the sugar,\n  still sweet" in markdown

    text = (await _export(client, owner, recipe_id, "text")).text
    assert "COOKING NOTES:" in text
    assert "  - Olive, " in text
    assert " UTC: Halved the sugar,\n    still sweet" in text


async def test_pdf_export_renders_the_notes(client: AsyncClient, monkeypatch):
    owner, _, recipe_id = await _recipe_with_notes(client)
    written: list[str] = []
    original = pdf_export.RecipePDF.multi_cell

    def spy(self, w, h=None, text="", *args, **kwargs):
        written.append(text)
        return original(self, w, h, text, *args, **kwargs)

    monkeypatch.setattr(pdf_export.RecipePDF, "multi_cell", spy)

    response = await _export(client, owner, recipe_id, "pdf")

    assert response.headers["content-type"] == "application/pdf"
    assert "Halved the sugar,\nstill sweet" in written
    assert any(line.startswith("Milo, ") and line.endswith(" UTC") for line in written)


async def test_bulk_and_backup_exports_include_notes(client: AsyncClient):
    owner, _, _ = await _recipe_with_notes(client)

    as_json = (await client.get("/api/v1/export/recipes?format=json", headers=owner)).json()
    assert [c["text"] for c in as_json[0]["comment"]] == [
        "Needs more salt",
        "Halved the sugar,\nstill sweet",
    ]
    markdown = (await client.get("/api/v1/export/recipes?format=markdown", headers=owner)).text
    assert "## Cooking Notes" in markdown and "Needs more salt" in markdown
    text = (await client.get("/api/v1/export/recipes?format=text", headers=owner)).text
    assert "COOKING NOTES:" in text and "Needs more salt" in text

    backup = (await client.get("/api/v1/export/all", headers=owner)).json()
    assert [c["author"]["name"] for c in backup["recipes"][0]["comment"]] == ["Olive", "Milo"]


async def test_collection_pdf_export_loads_notes(client: AsyncClient):
    owner, _, recipe_id = await _recipe_with_notes(client)
    collection = await client.post("/api/v1/collections/", json={"name": "Soups"}, headers=owner)
    assert collection.status_code == 201, collection.text
    collection_id = collection.json()["id"]
    added = await client.post(
        f"/api/v1/collections/{collection_id}/recipes",
        json={"recipe_ids": [recipe_id]},
        headers=owner,
    )
    assert added.status_code == 200, added.text

    response = await client.get(f"/api/v1/collections/{collection_id}/export/pdf", headers=owner)

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"


async def test_import_restores_notes_with_original_author_and_date(client: AsyncClient):
    owner, _, recipe_id = await _recipe_with_notes(client)
    exported = json.loads((await _export(client, owner, recipe_id, "json")).text)

    newcomer = await _login(client, "newcomer@example.com", "Nina")
    imported = await client.post(
        "/api/v1/import/recipes/json?duplicate_handling=skip", json=[exported], headers=newcomer
    )
    assert imported.status_code == 200, imported.text
    new_id = imported.json()["details"]["items"][0]["recipe_id"]

    notes = (await client.get(f"{RECIPES}/{new_id}/notes", headers=newcomer)).json()
    # Newest first in the API, with the names and times from the file
    assert [(n["author_name"], n["text"]) for n in notes] == [
        ("Milo", "Halved the sugar,\nstill sweet"),
        ("Olive", "Needs more salt"),
    ]
    assert [datetime.fromisoformat(n["created_at"]) for n in notes] == [
        datetime.fromisoformat(c["dateCreated"]) for c in reversed(exported["comment"])
    ]
    # The importing account added them, so it may edit them
    assert all(n["is_author"] for n in notes)


async def test_reimport_does_not_duplicate_notes(client: AsyncClient):
    owner, _, recipe_id = await _recipe_with_notes(client)
    exported = json.loads((await _export(client, owner, recipe_id, "json")).text)

    # Same account, same recipe name: "update" re-adds nothing that is already there,
    # including the notes whose author name is looked up live
    response = await client.post(
        "/api/v1/import/recipes/json?duplicate_handling=update", json=[exported], headers=owner
    )
    assert response.status_code == 200, response.text
    assert response.json()["details"]["updated"] == 1

    notes = (await client.get(f"{RECIPES}/{recipe_id}/notes", headers=owner)).json()
    assert len(notes) == 2


async def test_update_import_adds_new_notes_but_skip_adds_none(client: AsyncClient):
    owner, _, recipe_id = await _recipe_with_notes(client)
    exported = json.loads((await _export(client, owner, recipe_id, "json")).text)
    extra = {
        "@type": "Comment",
        "text": "Froze well",
        "dateCreated": "2026-01-02T03:04:05Z",
        "author": {"@type": "Person", "name": "Grandma"},
    }
    exported["comment"].append(extra)

    skipped = await client.post(
        "/api/v1/import/recipes/json?duplicate_handling=skip", json=[exported], headers=owner
    )
    assert skipped.json()["details"]["skipped"] == 1
    assert len((await client.get(f"{RECIPES}/{recipe_id}/notes", headers=owner)).json()) == 2

    updated = await client.post(
        "/api/v1/import/recipes/json?duplicate_handling=update", json=[exported], headers=owner
    )
    assert updated.json()["details"]["updated"] == 1
    notes = (await client.get(f"{RECIPES}/{recipe_id}/notes", headers=owner)).json()
    assert len(notes) == 3
    assert ("Grandma", "Froze well", "2026-01-02T03:04:05") in {
        (n["author_name"], n["text"], n["created_at"][:19]) for n in notes
    }


async def test_bad_comments_never_fail_the_recipe(client: AsyncClient):
    headers = await _login(client, "cook@example.com", "Cook")
    recipe = {
        "name": "Stew",
        "comment": ["not a comment", {"text": 5}, {"text": "  "}, {"text": "Good", "author": 7}],
    }

    response = await client.post(
        "/api/v1/import/recipes/json?duplicate_handling=create", json=[recipe], headers=headers
    )

    assert response.status_code == 200, response.text
    assert response.json()["details"]["created"] == 1
    recipe_id = response.json()["details"]["items"][0]["recipe_id"]
    notes = (await client.get(f"{RECIPES}/{recipe_id}/notes", headers=headers)).json()
    assert [(n["author_name"], n["text"]) for n in notes] == [("Unknown", "Good")]


@pytest.mark.parametrize(
    ("comments", "expected"),
    [
        (None, []),
        ("just text", []),
        # A single Comment object rather than a list
        (
            {"text": "Solo", "author": {"name": "Ada"}, "dateCreated": "2026-03-04T05:06:07Z"},
            [("Solo", "Ada", datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC))],
        ),
        # Markup stripped; author as a plain string or a list; offsets moved to UTC
        (
            [
                {"text": "<b>Crisp</b> & golden", "author": "Bo"},
                {
                    "text": "Spicy",
                    "author": [{"name": "Cy"}],
                    "dateCreated": "2026-03-04T07:00:00+02:00",
                },
                {"text": "Odd date", "author": {"name": ""}, "dateCreated": "yesterday"},
            ],
            [
                ("Crisp & golden", "Bo", None),
                ("Spicy", "Cy", datetime(2026, 3, 4, 5, 0, tzinfo=UTC)),
                ("Odd date", "Unknown", None),
            ],
        ),
    ],
)
def test_notes_from_schema_validates_entries(comments, expected):
    notes = notes_from_schema(comments)

    assert [(n["text"], n["author_name"], n["created_at"]) for n in notes] == expected


def test_notes_from_schema_limits_count_and_length():
    notes = notes_from_schema([{"text": "x" * 20000}] * (MAX_IMPORTED_NOTES + 5))

    assert len(notes) == MAX_IMPORTED_NOTES
    assert len(notes[0]["text"]) == 10000
