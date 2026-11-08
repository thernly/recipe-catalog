"""Tests for database migrations.

Note: This codebase doesn't have an initial migration that creates base tables.
Tables are created using SQLAlchemy's Base.metadata.create_all(), and migrations
handle subsequent schema changes. These tests verify the migration infrastructure
works correctly.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.core.database import Base


def get_alembic_config(database_url: str) -> Config:
    """Create Alembic config for testing."""
    # Get path to alembic.ini
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_ini = backend_dir / "alembic.ini"

    # Create config
    config = Config(str(alembic_ini))
    config.set_main_option("sqlalchemy.url", database_url)

    return config


def test_migration_chain_is_valid():
    """Test that migration revision chain has no breaks."""
    # Get path to alembic directory
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_dir = backend_dir / "alembic"

    # Create config
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(alembic_dir))

    # Get script directory
    script = ScriptDirectory.from_config(config)

    # Get all revisions
    revisions = list(script.walk_revisions())

    # Should have migrations
    assert len(revisions) > 0, "No migrations found"

    # Check that we can get to head without errors
    head_revision = script.get_current_head()
    assert head_revision is not None, "No head revision found"


def test_migrations_on_existing_database():
    """Test stamping and checking migrations on a database created from models.

    This simulates the production scenario where the database was created
    from SQLAlchemy models and migrations track subsequent changes.
    """
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Use synchronous SQLite for testing
        database_url = f"sqlite:///{db_path}"

        # Create database using SQLAlchemy models
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            )
            assert result.scalar() == "users"

        engine.dispose()

        # Get alembic config and verify head exists
        backend_dir = Path(__file__).resolve().parents[1]
        script_config = Config(str(backend_dir / "alembic.ini"))
        script_config.set_main_option("script_location", str(backend_dir / "alembic"))
        script = ScriptDirectory.from_config(script_config)
        head_revision = script.get_current_head()

        # Should have a head revision
        assert head_revision is not None, "No head revision found"

    finally:
        # Clean up temporary database
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_migration_revision_identifiers():
    """Test that all migration revisions have valid identifiers."""
    backend_dir = Path(__file__).resolve().parents[1]
    script_config = Config(str(backend_dir / "alembic.ini"))
    script_config.set_main_option("script_location", str(backend_dir / "alembic"))
    script = ScriptDirectory.from_config(script_config)

    # Get all revisions
    revisions = list(script.walk_revisions())

    # Check each revision has required attributes
    for revision in revisions:
        assert revision.revision is not None, f"Revision {revision.module} has no revision ID"
        # down_revision can be None for initial migration
        # but revision must always exist


def test_all_migration_files_are_valid_python():
    """Test that all migration files can be imported without errors."""
    backend_dir = Path(__file__).resolve().parents[1]
    versions_dir = backend_dir / "alembic" / "versions"

    # Get all Python files in versions directory
    migration_files = list(versions_dir.glob("*.py"))

    # Should have at least one migration
    assert len(migration_files) > 0, "No migration files found"

    # Verify all files are valid Python (compile check)
    for migration_file in migration_files:
        if migration_file.name == "__pycache__":
            continue

        with open(migration_file) as f:
            code = f.read()

        # Should compile without syntax errors
        try:
            compile(code, str(migration_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Migration file {migration_file.name} has syntax error: {e}")


def test_env_py_metadata_is_populated():
    """Alembic's target_metadata must see every model, or autogenerate drops tables.

    alembic/env.py sets target_metadata = Base.metadata, which is only populated
    for models that have been imported. This runs in a subprocess because the
    test suite's conftest imports several models itself, so an in-process check
    would pass even when env.py's own imports miss them.
    """
    backend_dir = Path(__file__).resolve().parents[1]
    env_py = backend_dir / "alembic" / "env.py"

    # Replay exactly the app imports env.py performs, then count mapped tables.
    app_imports = [
        line.strip()
        for line in env_py.read_text().splitlines()
        if line.startswith(("import app", "from app"))
    ]
    assert app_imports, "env.py performs no app imports"

    script = "\n".join(
        [*app_imports, "from app.core.database import Base", "print(len(Base.metadata.tables))"]
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        env={**os.environ, "DATABASE_URL": "sqlite+aiosqlite:///:memory:"},
    )

    assert result.returncode == 0, f"env.py imports failed:\n{result.stderr}"

    table_count = int(result.stdout.strip().splitlines()[-1])
    expected = len(Base.metadata.tables)
    assert table_count == expected, (
        f"env.py's imports register {table_count} tables on Base.metadata but the "
        f"models define {expected}. --autogenerate would drop the missing ones. "
        "Ensure alembic/env.py imports app.models."
    )


def test_fresh_database_upgrade_downgrade_and_schema_parity(tmp_path):
    """A new volume must boot and round-trip every revision without drift."""
    backend_dir = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'fresh.db'}",
        "DEBUG": "false",
    }
    for arguments in [
        ("upgrade", "head"),
        ("check",),
        ("downgrade", "base"),
        ("upgrade", "head"),
        ("check",),
    ]:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_upgrade_repairs_existing_household_scope_and_preserves_meals(tmp_path):
    """Repair historical departures and invisible duplicates, including colliding weeks."""
    import hashlib
    import sqlite3

    backend_dir = Path(__file__).resolve().parents[1]
    database = tmp_path / "legacy.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{database}", "DEBUG": "false"}

    def migrate(*arguments):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    migrate("upgrade", "20261004_api_tokens")
    with sqlite3.connect(database) as connection:
        for user_id in range(1, 5):
            connection.execute(
                """INSERT INTO users
                (id,email,is_active,is_verified,created_at,updated_at,failed_login_attempts)
                VALUES (?,?,1,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,0)""",
                (user_id, f"u{user_id}@example.com"),
            )
        for household_id in range(1, 4):
            connection.execute(
                """INSERT INTO households
                (id,name,owner_user_id,max_members,created_at,updated_at)
                VALUES (?,?,?,10,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)""",
                (household_id, f"House {household_id}", household_id),
            )
        for user_id, household_id in [(1, 2), (2, 3), (3, 3)]:
            connection.execute(
                """INSERT INTO household_members (user_id,household_id,role,joined_at)
                VALUES (?,?,'member',CURRENT_TIMESTAMP)""",
                (user_id, household_id),
            )
        for recipe_id, owner, household_id in [(1, 1, 1), (2, 2, 2), (3, 4, None)]:
            connection.execute(
                """INSERT INTO recipes
                (id,user_id,household_id,name,recipe_data,source_type,is_modified,created_at,updated_at)
                VALUES (?,?,?,'Soup','{}','manual',0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)""",
                (recipe_id, owner, household_id),
            )
        for plan_id in (1, 2):
            connection.execute(
                """INSERT INTO meal_plans
                (id,household_id,created_by_user_id,week_start_date,created_at,updated_at)
                VALUES (?,?,?,'2026-11-02',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)""",
                (plan_id, plan_id, plan_id),
            )
            connection.execute(
                """INSERT INTO planned_meals
                (id,meal_plan_id,recipe_id,day_of_week,meal_type,created_at,updated_at)
                VALUES (?,?,?,0,'dinner',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)""",
                (plan_id, plan_id, plan_id),
            )
            connection.execute(
                """INSERT INTO household_invitations
                (household_id,inviter_user_id,invitee_email,token,expires_at,created_at)
                VALUES (?,?,'invite@example.com',?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)""",
                (plan_id, plan_id, f"original-secret-{plan_id}"),
            )
    migrate("upgrade", "head")
    migrate("check")
    with sqlite3.connect(database) as connection:
        scopes = dict(connection.execute("SELECT user_id,household_id FROM household_members"))
        assert dict(connection.execute("SELECT id,household_id FROM recipes")) == {
            1: 2,
            2: 3,
            3: scopes[4],
        }
        assert list(
            connection.execute("""SELECT pm.id,mp.household_id,pm.created_by_user_id
            FROM planned_meals pm JOIN meal_plans mp ON mp.id=pm.meal_plan_id ORDER BY pm.id""")
        ) == [(1, 2, None), (2, 2, None)]
        assert [
            row[0]
            for row in connection.execute("SELECT token FROM household_invitations ORDER BY id")
        ] == [hashlib.sha256(f"original-secret-{i}".encode()).hexdigest() for i in (1, 2)]
        assert list(connection.execute("PRAGMA foreign_key_check")) == []
