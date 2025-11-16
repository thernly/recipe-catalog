-- Recipe Catalog Database Schema
-- SQLite database schema for reference
-- Actual tables are created via SQLAlchemy models

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    is_verified BOOLEAN DEFAULT 0 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    theme VARCHAR(50) DEFAULT 'classic' NOT NULL,
    default_view VARCHAR(20) DEFAULT 'grid' NOT NULL,
    default_sort VARCHAR(50) DEFAULT 'recently_added' NOT NULL,
    recipes_per_page INTEGER DEFAULT 24 NOT NULL,
    email_notifications BOOLEAN DEFAULT 0 NOT NULL,
    timezone VARCHAR(100) DEFAULT 'UTC' NOT NULL,
    custom_cuisines TEXT DEFAULT '[]' NOT NULL,
    custom_categories TEXT DEFAULT '[]' NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Recipes table
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    image_url TEXT,
    recipe_data JSON NOT NULL,
    source_url TEXT,
    source_type VARCHAR(20) DEFAULT 'manual' NOT NULL,
    is_modified BOOLEAN DEFAULT 0 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    imported_at DATETIME,
    deleted_at DATETIME,
    cuisine VARCHAR(100),
    category VARCHAR(100),
    total_time_minutes INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON recipes(user_id);
CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(name);
CREATE INDEX IF NOT EXISTS idx_recipes_source_url ON recipes(source_url);
CREATE INDEX IF NOT EXISTS idx_recipes_created_at ON recipes(created_at);
CREATE INDEX IF NOT EXISTS idx_recipes_deleted_at ON recipes(deleted_at);
CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine);
CREATE INDEX IF NOT EXISTS idx_recipes_category ON recipes(category);
CREATE INDEX IF NOT EXISTS idx_recipes_total_time_minutes ON recipes(total_time_minutes);

-- Collections table
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT 0 NOT NULL,
    icon VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_user_collection_name UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_collections_user_id ON collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collections_is_default ON collections(is_default);

-- Recipe-Collection junction table
CREATE TABLE IF NOT EXISTS recipe_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    collection_id INTEGER NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    CONSTRAINT uq_recipe_collection UNIQUE (recipe_id, collection_id)
);

CREATE INDEX IF NOT EXISTS idx_recipe_collections_recipe_id ON recipe_collections(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_collections_collection_id ON recipe_collections(collection_id);
