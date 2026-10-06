"""Tests for the cleanup backfill (plan, report, backup, apply)."""

import sqlite3
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from app.services.ingredient_parser import PARSED_BY_MODEL
from app.services.recipe_backfill import (
    apply_backfill,
    backup_sqlite_database,
    plan_backfill,
    render_report,
    sqlite_path_from_url,
)
from app.services.recipe_cleanup import clean_recipe_data


OLD = datetime(2025, 1, 2, 3, 4, 5)


async def _recipe(db: AsyncSession, user_id: int, name: str, data: dict, **kwargs) -> Recipe:
    recipe = Recipe(
        user_id=user_id,
        name=name,
        recipe_data=data,
        created_at=OLD,
        updated_at=OLD,
        **kwargs,
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)
    return recipe


@pytest.fixture
async def recipes(db: AsyncSession, test_user):
    messy = await _recipe(
        db,
        test_user.id,
        "Messy",
        {
            "recipeYield": "6 6 servings",
            "prepTime": "15 mins",
            "cookTime": "1 hr",
            "recipeIngredient": ["2 cups flour", "Seeds scraped from 1 vanilla pod"],
        },
    )
    clean_data = clean_recipe_data(
        {"recipeYield": "4 servings", "totalTime": "PT30M", "recipeIngredient": ["1 egg"]}
    ).data
    clean = await _recipe(db, test_user.id, "Clean", clean_data, total_time_minutes=30)
    trashed = await _recipe(
        db, test_user.id, "Trashed", {"recipeYield": "2 2"}, deleted_at=datetime.now(UTC)
    )
    return messy, clean, trashed


async def test_plan_reports_changes_without_writing(db: AsyncSession, recipes):
    messy, clean, _ = recipes
    plan = await plan_backfill(db)

    assert [p.recipe_id for p in plan] == [messy.id, clean.id]  # trash excluded
    first = plan[0]
    assert first.changes == {
        "recipeYield": ("6 6 servings", "6 servings"),
        "prepTime": ("15 mins", "PT15M"),
        "cookTime": ("1 hr", "PT1H"),
        "total_time_minutes": (None, 75),
    }
    assert first.parsed_changed
    assert (first.parsed_lines, first.ingredient_lines) == (1, 2)
    assert first.unparsed == ["Seeds scraped from 1 vanilla pod"]
    assert not plan[1].changed

    await db.refresh(messy)
    assert messy.recipe_data["recipeYield"] == "6 6 servings"


async def test_plan_can_include_trash(db: AsyncSession, recipes):
    plan = await plan_backfill(db, include_deleted=True)
    assert [p.name for p in plan] == ["Messy", "Clean", "Trashed"]


async def test_report_lists_changes_and_every_unparsed_line(db: AsyncSession, recipes):
    messy, clean, _ = recipes
    plan = await plan_backfill(db)

    report = render_report(plan)
    assert "Recipes scanned: 2" in report
    assert "Recipes with yield or time changes: 1" in report
    assert "Ingredient lines parsed: 2/3 (66.7%)" in report
    assert f"### {messy.id}: Messy" in report
    assert "recipeYield: `6 6 servings` -> `6 servings`" in report
    assert f"- {messy.id} (Messy): `Seeds scraped from 1 vanilla pod`" in report

    excluded = render_report(plan, excluded={messy.id})
    assert f"Excluded: 1 ({messy.id})" in excluded
    assert "Messy" not in excluded


async def test_apply_writes_changes_and_keeps_updated_at(db: AsyncSession, recipes):
    messy, clean, _ = recipes
    plan = await plan_backfill(db)

    written = await apply_backfill(db, plan)

    assert written == 1
    row = (await db.execute(select(Recipe).where(Recipe.id == messy.id))).scalar_one()
    await db.refresh(row)
    assert row.recipe_data["recipeYield"] == "6 servings"
    assert row.recipe_data["recipeIngredient"] == [
        "2 cups flour",
        "Seeds scraped from 1 vanilla pod",
    ]
    assert row.recipe_data["parsedIngredients"][0]["item"] == "flour"
    assert row.total_time_minutes == 75
    assert row.updated_at == OLD
    assert row.is_modified is False

    # Running again finds nothing to do
    assert not any(p.changed for p in await plan_backfill(db))


async def test_apply_respects_exclusions(db: AsyncSession, recipes):
    messy, _, _ = recipes
    plan = await plan_backfill(db)

    assert await apply_backfill(db, plan, excluded={messy.id}) == 0
    await db.refresh(messy)
    assert messy.recipe_data["recipeYield"] == "6 6 servings"


async def test_backfill_keeps_model_parses(db: AsyncSession, test_user):
    data = clean_recipe_data({"recipeIngredient": ["Seeds scraped from 1 vanilla pod"]}).data
    data["parsedIngredients"][0].update(item="lemon", parsedBy=PARSED_BY_MODEL)
    recipe = await _recipe(db, test_user.id, "Lemonade", data)

    plan = await plan_backfill(db)

    entry = next(p for p in plan if p.recipe_id == recipe.id)
    assert not entry.parsed_changed
    assert entry.new_data["parsedIngredients"][0]["item"] == "lemon"


def test_backup_copies_sqlite_database(tmp_path):
    db_path = tmp_path / "recipes.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    conn.close()

    backup = backup_sqlite_database(f"sqlite+aiosqlite:///{db_path}")

    assert backup.name.startswith("recipes.db.bak-")
    copy = sqlite3.connect(backup)
    assert copy.execute("SELECT x FROM t").fetchall() == [(42,)]
    copy.close()


@pytest.mark.parametrize(
    "url",
    ["sqlite+aiosqlite:///:memory:", "postgresql://u@h/db", "sqlite+aiosqlite://"],
)
def test_backup_refuses_non_file_databases(url):
    with pytest.raises(ValueError):
        sqlite_path_from_url(url)


def test_backup_requires_existing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup_sqlite_database(f"sqlite:///{tmp_path / 'missing.db'}")
