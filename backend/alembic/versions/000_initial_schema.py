"""Frozen pre-001 schema for installations starting with an empty database.

Existing installations stamped at 001 or later do not execute this revision.
"""

from alembic import op


revision = "000_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE TABLE users (\n\tid INTEGER NOT NULL, \n\temail VARCHAR(255) NOT NULL, \n\thashed_password VARCHAR(255) NOT NULL, \n\tdisplay_name VARCHAR(100), \n\tis_active BOOLEAN NOT NULL, \n\tis_verified BOOLEAN NOT NULL, \n\tcreated_at DATETIME NOT NULL, \n\tupdated_at DATETIME NOT NULL, \n\tPRIMARY KEY (id)\n)"
    )
    op.execute("CREATE UNIQUE INDEX ix_users_email ON users (email)")
    op.execute("CREATE INDEX ix_users_id ON users (id)")
    op.execute(
        "CREATE TABLE collections (\n\tid INTEGER NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tname VARCHAR(100) NOT NULL, \n\tdescription TEXT, \n\tis_default BOOLEAN NOT NULL, \n\ticon VARCHAR(50), \n\tcreated_at DATETIME NOT NULL, \n\tupdated_at DATETIME NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tCONSTRAINT uq_user_collection_name UNIQUE (user_id, name)\n)"
    )
    op.execute("CREATE INDEX ix_collections_id ON collections (id)")
    op.execute("CREATE INDEX ix_collections_is_default ON collections (is_default)")
    op.execute("CREATE INDEX ix_collections_user_id ON collections (user_id)")
    op.execute(
        "CREATE TABLE password_reset_tokens (\n\tid INTEGER NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\ttoken VARCHAR(64) NOT NULL, \n\texpires_at DATETIME NOT NULL, \n\tused BOOLEAN, \n\tcreated_at DATETIME, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE\n)"
    )
    op.execute("CREATE INDEX ix_password_reset_tokens_id ON password_reset_tokens (id)")
    op.execute(
        "CREATE UNIQUE INDEX ix_password_reset_tokens_token ON password_reset_tokens (token)"
    )
    op.execute(
        "CREATE TABLE recipes (\n\tid INTEGER NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tname VARCHAR(500) NOT NULL, \n\tdescription TEXT, \n\timage_url TEXT, \n\trecipe_data JSON NOT NULL, \n\tsource_url TEXT, \n\tsource_type VARCHAR(20) NOT NULL, \n\tis_modified BOOLEAN NOT NULL, \n\tcreated_at DATETIME NOT NULL, \n\tupdated_at DATETIME NOT NULL, \n\timported_at DATETIME, \n\tdeleted_at DATETIME, \n\tcuisine VARCHAR(100), \n\tcategory VARCHAR(100), \n\ttotal_time_minutes INTEGER, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)"
    )
    op.execute("CREATE INDEX ix_recipes_category ON recipes (category)")
    op.execute("CREATE INDEX ix_recipes_created_at ON recipes (created_at)")
    op.execute("CREATE INDEX ix_recipes_cuisine ON recipes (cuisine)")
    op.execute("CREATE INDEX ix_recipes_deleted_at ON recipes (deleted_at)")
    op.execute("CREATE INDEX ix_recipes_id ON recipes (id)")
    op.execute("CREATE INDEX ix_recipes_name ON recipes (name)")
    op.execute("CREATE INDEX ix_recipes_source_url ON recipes (source_url)")
    op.execute("CREATE INDEX ix_recipes_total_time_minutes ON recipes (total_time_minutes)")
    op.execute("CREATE INDEX ix_recipes_user_id ON recipes (user_id)")
    op.execute(
        "CREATE TABLE user_preferences (\n\tid INTEGER NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\ttheme VARCHAR(50) NOT NULL, \n\tdefault_view VARCHAR(20) NOT NULL, \n\tdefault_sort VARCHAR(50) NOT NULL, \n\trecipes_per_page INTEGER NOT NULL, \n\temail_notifications BOOLEAN NOT NULL, \n\ttimezone VARCHAR(100) NOT NULL, \n\tcreated_at DATETIME NOT NULL, \n\tupdated_at DATETIME NOT NULL, \n\tPRIMARY KEY (id)\n)"
    )
    op.execute("CREATE INDEX ix_user_preferences_id ON user_preferences (id)")
    op.execute("CREATE UNIQUE INDEX ix_user_preferences_user_id ON user_preferences (user_id)")
    op.execute(
        "CREATE TABLE verification_tokens (\n\tid INTEGER NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\ttoken VARCHAR(64) NOT NULL, \n\texpires_at DATETIME NOT NULL, \n\tused BOOLEAN, \n\tcreated_at DATETIME, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE\n)"
    )
    op.execute("CREATE INDEX ix_verification_tokens_id ON verification_tokens (id)")
    op.execute("CREATE UNIQUE INDEX ix_verification_tokens_token ON verification_tokens (token)")
    op.execute(
        "CREATE TABLE recipe_collections (\n\tid INTEGER NOT NULL, \n\trecipe_id INTEGER NOT NULL, \n\tcollection_id INTEGER NOT NULL, \n\tadded_at DATETIME NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_recipe_collection UNIQUE (recipe_id, collection_id), \n\tFOREIGN KEY(recipe_id) REFERENCES recipes (id), \n\tFOREIGN KEY(collection_id) REFERENCES collections (id)\n)"
    )
    op.execute(
        "CREATE INDEX ix_recipe_collections_collection_id ON recipe_collections (collection_id)"
    )
    op.execute("CREATE INDEX ix_recipe_collections_id ON recipe_collections (id)")
    op.execute("CREATE INDEX ix_recipe_collections_recipe_id ON recipe_collections (recipe_id)")


def downgrade():
    op.drop_table("recipe_collections")
    op.drop_table("verification_tokens")
    op.drop_table("user_preferences")
    op.drop_table("recipes")
    op.drop_table("password_reset_tokens")
    op.drop_table("collections")
    op.drop_table("users")
