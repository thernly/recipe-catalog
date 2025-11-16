"""
Standalone script to add custom_cuisines and custom_categories columns to user_preferences table.
This fixes the database schema for existing databases.

Run this script from the backend directory:
    python fix_user_preferences_schema.py
"""

import sqlite3
from pathlib import Path

# Find the database file
db_path = Path(__file__).parent.parent / "backend" / "recipes.db"

if not db_path.exists():
    print(f"❌ Database not found at: {db_path}")
    print("\nPlease ensure the database exists or update the db_path in this script.")
    exit(1)

print(f"📁 Found database at: {db_path}")

# Connect to the database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(user_preferences)")
    columns = [row[1] for row in cursor.fetchall()]

    needs_custom_cuisines = "custom_cuisines" not in columns
    needs_custom_categories = "custom_categories" not in columns

    if not needs_custom_cuisines and not needs_custom_categories:
        print("✅ Database schema is already up to date!")
        print("   - custom_cuisines column exists")
        print("   - custom_categories column exists")
    else:
        # Add missing columns
        if needs_custom_cuisines:
            print("\n🔧 Adding custom_cuisines column...")
            cursor.execute("""
                ALTER TABLE user_preferences
                ADD COLUMN custom_cuisines TEXT NOT NULL DEFAULT '[]'
            """)
            print("✅ Added custom_cuisines column")

        if needs_custom_categories:
            print("🔧 Adding custom_categories column...")
            cursor.execute("""
                ALTER TABLE user_preferences
                ADD COLUMN custom_categories TEXT NOT NULL DEFAULT '[]'
            """)
            print("✅ Added custom_categories column")

        # Commit the changes
        conn.commit()
        print("\n✅ Database schema updated successfully!")
        print("\nYou can now restart your backend server.")

except sqlite3.Error as e:
    print(f"\n❌ Error updating database: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

print("\n" + "=" * 60)
print("Note: In the future, you can also run Alembic migrations:")
print("  cd backend")
print("  alembic upgrade head")
print("=" * 60)
