"""
Backfill recipe cleanup (yield, times, parsedIngredients) over existing recipes.

Design doc §9: dry run first, the owner reviews the report, then apply. Applying backs
up the SQLite database first and writes everything in one transaction.

Run from backend/, like the app, so backend/.env supplies the settings (SECRET_KEY,
DATABASE_URL). Stop the app before --apply: a recipe edited between planning and writing
would lose that edit.

Usage (from backend/):
    uv run python scripts/backfill_cleanup.py                       # dry run + report
    uv run python scripts/backfill_cleanup.py --exclude 12,40       # leave recipes out
    uv run python scripts/backfill_cleanup.py --apply --exclude 12  # back up, then write

Options:
    --database-url URL     defaults to DATABASE_URL from the app settings
    --report PATH          where to write the Markdown report
                           (default backfill-report-<timestamp>.md)
    --exclude IDS          comma-separated recipe ids to leave alone
    --exclude-file PATH    file with recipe ids, one per line (# comments allowed)
    --include-deleted      also clean recipes in the trash
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings  # noqa: E402
from app.services.recipe_backfill import (  # noqa: E402
    apply_backfill,
    backup_sqlite_database,
    plan_backfill,
    render_report,
)


def _parse_ids(text: str) -> set[int]:
    ids: set[int] = set()
    for part in text.replace("\n", ",").split(","):
        part = part.split("#", 1)[0].strip()
        if part:
            ids.add(int(part))
    return ids


async def run(args: argparse.Namespace) -> int:
    excluded: set[int] = set()
    if args.exclude:
        excluded |= _parse_ids(args.exclude)
    if args.exclude_file:
        excluded |= _parse_ids(Path(args.exclude_file).read_text(encoding="utf-8"))

    engine = create_async_engine(args.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            plan = await plan_backfill(session, include_deleted=args.include_deleted)

            report_path = Path(
                args.report or f"backfill-report-{datetime.now(UTC):%Y%m%d-%H%M%S}.md"
            )
            report_path.write_text(render_report(plan, excluded), encoding="utf-8")

            changed = [p for p in plan if p.changed and p.recipe_id not in excluded]
            print(f"Scanned {len(plan)} recipes; {len(changed)} would be written.")
            print(f"Report: {report_path}")

            if not args.apply:
                print("Dry run: nothing was written. Re-run with --apply after review.")
                return 0

            backup_path = backup_sqlite_database(args.database_url)
            print(f"Backup: {backup_path}")
            written = await apply_backfill(session, plan, excluded)
            print(f"Applied: {written} recipes updated.")
            return 0
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill recipe cleanup")
    parser.add_argument("--database-url", default=settings.DATABASE_URL)
    parser.add_argument("--report", default=None)
    parser.add_argument("--exclude", default="")
    parser.add_argument("--exclude-file", default=None)
    parser.add_argument("--include-deleted", action="store_true")
    parser.add_argument("--apply", action="store_true")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
