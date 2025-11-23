"""Fix recipes missing household_id by assigning them to user's household."""

import sqlite3


conn = sqlite3.connect("recipes.db")
cursor = conn.cursor()

# Update recipes to have the correct household_id
cursor.execute("""
    UPDATE recipes
    SET household_id = (
        SELECT household_id
        FROM household_members
        WHERE household_members.user_id = recipes.user_id
        LIMIT 1
    )
    WHERE household_id IS NULL
""")

updated = cursor.rowcount
conn.commit()

print(f"✅ Updated {updated} recipes with household_id")

# Verify
cursor.execute("""
    SELECT user_id, household_id, COUNT(*)
    FROM recipes
    WHERE deleted_at IS NULL
    GROUP BY user_id, household_id
""")
print("\nRecipes by user and household after fix:")
for row in cursor.fetchall():
    print(f"  User {row[0]}, Household {row[1]}: {row[2]} recipes")

conn.close()
