"""
Remove extra copies of the same picture from stored recipes.

Recipe pages list one picture several times at other sizes or crops, and imports before
this fix kept them all (up to 5), so the photo viewer paged through the same picture.
Each picture is kept once, at its largest size, where it first appeared. Recipes in the
trash are included. The rule is `picture_key` in app/utils/recipe_format.py.

A dry run lists what would change. --apply backs up the SQLite database next to it
(recipes.db.bak-<timestamp>), then writes everything in one transaction. Stop the app
before --apply: a recipe edited in between would lose that edit.

Usage (from backend/, so backend/.env supplies DATABASE_URL):
    uv run python scripts/dedupe_recipe_images.py            # dry run
    uv run python scripts/dedupe_recipe_images.py --apply    # back up, then write

Options:
    --database-url URL     defaults to DATABASE_URL from the app settings
"""

import argparse
import asyncio
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

import app.models  # noqa: E402, F401  (registers every model for the relationships)
from app.core.config import settings  # noqa: E402
from app.models.recipe import Recipe  # noqa: E402
from app.services.recipe_backfill import backup_sqlite_database  # noqa: E402
from app.utils.recipe_format import dedupe_recipe_images  # noqa: E402


async def run(database_url: str, apply: bool) -> int:
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            result = await session.execute(select(Recipe).order_by(Recipe.id))
            recipes = result.scalars().all()
            changed = 0
            for recipe in recipes:
                before = len((recipe.recipe_data or {}).get("images") or [])
                dropped = dedupe_recipe_images(recipe)
                if not dropped:
                    continue
                changed += 1
                print(f"#{recipe.id} {recipe.name}: {before} -> {before - len(dropped)} pictures")
                for image in dropped:
                    print(f"    drop {image.get('url') or '(no address)'}")

            print(f"{changed} recipes would change." if not apply else f"{changed} recipes.")
            if not apply:
                print("Dry run: nothing was written. Re-run with --apply to write.")
                return 0
            if not changed:
                return 0

            print(f"Backup: {backup_sqlite_database(database_url)}")
            await session.commit()
            print(f"Applied: {changed} recipes updated.")
            return 0
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove extra copies of the same picture")
    parser.add_argument("--database-url", default=settings.DATABASE_URL)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return asyncio.run(run(args.database_url, args.apply))


if __name__ == "__main__":
    sys.exit(main())
