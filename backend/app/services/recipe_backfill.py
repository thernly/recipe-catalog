"""
One-off backfill of recipe cleanup over existing recipes (design doc §9).

Deterministic only. `plan_backfill` computes what `clean_recipe_data` would change for
every recipe, `render_report` turns that into the dry-run report the owner reviews, and
`apply_backfill` writes it in one transaction after `backup_sqlite_database`.

Applying does not mark recipes as modified and keeps their `updated_at`, since nobody
edited them.
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from app.services.recipe_cleanup import clean_recipe_data, derive_total_time_minutes


@dataclass
class RecipeBackfill:
    recipe_id: int
    name: str
    new_data: dict[str, Any]
    new_total_time_minutes: int | None
    # field -> (before, after) for yield, times and total_time_minutes
    changes: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    parsed_changed: bool = False
    ingredient_lines: int = 0
    parsed_lines: int = 0
    unparsed: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.changes) or self.parsed_changed


async def plan_backfill(
    session: AsyncSession, include_deleted: bool = False
) -> list[RecipeBackfill]:
    """Compute the cleanup for every recipe without writing anything."""
    query = select(Recipe).order_by(Recipe.id)
    if not include_deleted:
        query = query.where(Recipe.deleted_at.is_(None))
    recipes = (await session.execute(query)).scalars().all()

    plan: list[RecipeBackfill] = []
    for recipe in recipes:
        original: dict[str, Any] = dict(recipe.recipe_data or {})
        result = clean_recipe_data(original, original.get("parsedIngredients"))
        changes = dict(result.changes)

        current_total = cast(int | None, recipe.total_time_minutes)
        new_total = current_total
        derived = derive_total_time_minutes(result.data)
        if derived is not None and derived != current_total:
            changes["total_time_minutes"] = (current_total, derived)
            new_total = derived

        plan.append(
            RecipeBackfill(
                recipe_id=int(recipe.id),
                name=str(recipe.name),
                new_data=result.data,
                new_total_time_minutes=new_total,
                changes=changes,
                parsed_changed=original.get("parsedIngredients")
                != result.data.get("parsedIngredients"),
                ingredient_lines=result.ingredient_lines,
                parsed_lines=result.parsed_lines,
                unparsed=result.unparsed,
            )
        )
    return plan


def _fmt(value: Any) -> str:
    if value is None or value == "":
        return "(empty)"
    return f"`{value}`"


def render_report(plan: list[RecipeBackfill], excluded: set[int] | None = None) -> str:
    """Markdown dry-run report: per-recipe changes, then every line that did not parse."""
    excluded = excluded or set()
    included = [p for p in plan if p.recipe_id not in excluded]
    total_lines = sum(p.ingredient_lines for p in included)
    parsed_lines = sum(p.parsed_lines for p in included)
    field_changes = [p for p in included if p.changes]
    rate = f"{parsed_lines / total_lines:.1%}" if total_lines else "n/a"

    out = [
        "# Recipe cleanup backfill report",
        "",
        f"Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
        f"- Recipes scanned: {len(plan)}",
        f"- Excluded: {len(plan) - len(included)}"
        + (f" ({', '.join(str(i) for i in sorted(excluded))})" if excluded else ""),
        f"- Recipes with yield or time changes: {len(field_changes)}",
        f"- Recipes that would be written (including new parsedIngredients): "
        f"{sum(1 for p in included if p.changed)}",
        f"- Ingredient lines parsed: {parsed_lines}/{total_lines} ({rate})",
        "",
        "## Per recipe",
        "",
    ]

    for p in included:
        out.append(f"### {p.recipe_id}: {p.name}")
        out.append("")
        if p.changes:
            for name, (before, after) in p.changes.items():
                out.append(f"- {name}: {_fmt(before)} -> {_fmt(after)}")
        else:
            out.append("- No yield or time changes")
        out.append(f"- Ingredient lines parsed: {p.parsed_lines}/{p.ingredient_lines}")
        out.append("")

    out.append("## Lines that did not parse")
    out.append("")
    any_unparsed = False
    for p in included:
        for line in p.unparsed:
            any_unparsed = True
            out.append(f"- {p.recipe_id} ({p.name}): `{line}`")
    if not any_unparsed:
        out.append("- None")
    out.append("")
    return "\n".join(out)


def sqlite_path_from_url(database_url: str) -> Path:
    """Return the file path of a SQLite database URL, refusing anything else."""
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        raise ValueError(f"Backfill backups support SQLite only, not {url.drivername}")
    if not url.database or url.database == ":memory:":
        raise ValueError("Backfill needs an on-disk SQLite database")
    return Path(url.database)


def backup_sqlite_database(database_url: str) -> Path:
    """Copy the SQLite database with the online backup API. Returns the backup path."""
    source_path = sqlite_path_from_url(database_url)
    if not source_path.exists():
        raise FileNotFoundError(f"Database not found: {source_path}")
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    backup_path = source_path.with_name(f"{source_path.name}.bak-{stamp}")
    if backup_path.exists():
        raise FileExistsError(f"Backup already exists: {backup_path}")

    source = sqlite3.connect(source_path)
    try:
        target = sqlite3.connect(backup_path)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
    return backup_path


async def apply_backfill(
    session: AsyncSession, plan: list[RecipeBackfill], excluded: set[int] | None = None
) -> int:
    """Write the planned changes in one transaction. Returns the number of recipes written."""
    excluded = excluded or set()
    written = 0
    for p in plan:
        if p.recipe_id in excluded or not p.changed:
            continue
        await session.execute(
            update(Recipe)
            .where(Recipe.id == p.recipe_id)
            .values(
                recipe_data=p.new_data,
                total_time_minutes=p.new_total_time_minutes,
                # Explicitly keep the old value so the onupdate default does not fire
                updated_at=Recipe.updated_at,
            )
        )
        written += 1
    await session.commit()
    return written
