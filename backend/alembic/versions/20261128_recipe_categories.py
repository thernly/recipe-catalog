"""A recipe can have several categories

Categories move from the recipes.category column to a recipe_categories table, one
row per category. The stored value is split on "," and ";" ("dinner, pastas, main
course" becomes three rows), and recipe_data.recipeCategory is written as the same
list so export round-trips. Where recipe_data already holds a non-empty
recipeCategory list, that list wins over the column (it is the import's full list;
the column kept only the first entry).

Revision ID: 20261128_recipe_categories
Revises: 20261126_planned_meal_title
"""

import json

import sqlalchemy as sa

from alembic import op


revision = "20261128_recipe_categories"
down_revision = "20261126_planned_meal_title"
branch_labels = None
depends_on = None


def _split(value: object) -> list[str]:
    """The category names in a stored value: a string (maybe a comma list) or a list."""
    entries = value if isinstance(value, list) else [value]
    names: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, str):
            continue
        for part in entry.replace(";", ",").split(","):
            name = part.strip()[:100].strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                names.append(name)
    return names[:20]


def _load(raw: object) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        data = json.loads(raw) if isinstance(raw, str | bytes) else None
    except ValueError:
        data = None
    return data if isinstance(data, dict) else {}


def upgrade() -> None:
    op.create_table(
        "recipe_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipe_id", "name", name="uq_recipe_categories_name"),
    )
    op.create_index("ix_recipe_categories_recipe_id", "recipe_categories", ["recipe_id"])

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, category, recipe_data FROM recipes")).fetchall()
    for recipe_id, category, raw in rows:
        data = _load(raw)
        stored = data.get("recipeCategory")
        names = _split(stored if isinstance(stored, list) and stored else category)
        for name in names:
            bind.execute(
                sa.text("INSERT INTO recipe_categories (recipe_id, name) VALUES (:id, :name)"),
                {"id": recipe_id, "name": name},
            )
        if stored != names:
            data["recipeCategory"] = names
            bind.execute(
                sa.text("UPDATE recipes SET recipe_data = :data WHERE id = :id"),
                {"data": json.dumps(data), "id": recipe_id},
            )

    with op.batch_alter_table("recipes") as batch:
        batch.drop_index("ix_recipes_category")
        batch.drop_column("category")


def downgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.add_column(sa.Column("category", sa.String(length=100), nullable=True))
        batch.create_index("ix_recipes_category", ["category"])
    # The column held one category: keep each recipe's first
    op.execute(
        """UPDATE recipes SET category = (
            SELECT name FROM recipe_categories c
            WHERE c.recipe_id = recipes.id ORDER BY c.id LIMIT 1)"""
    )
    op.drop_index("ix_recipe_categories_recipe_id", table_name="recipe_categories")
    op.drop_table("recipe_categories")
