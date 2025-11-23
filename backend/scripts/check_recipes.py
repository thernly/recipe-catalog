import sqlite3


conn = sqlite3.connect("recipes.db")
cursor = conn.cursor()

# Check users
cursor.execute("SELECT id, email FROM users")
print("Users in database:")
for row in cursor.fetchall():
    print(f"  User {row[0]}: {row[1]}")

# Check total recipes
cursor.execute("SELECT COUNT(*) FROM recipes WHERE deleted_at IS NULL")
total = cursor.fetchone()[0]
print(f"\nTotal non-deleted recipes: {total}")

# Check recipes per user
cursor.execute("SELECT user_id, COUNT(*) FROM recipes WHERE deleted_at IS NULL GROUP BY user_id")
print("\nRecipes per user:")
for row in cursor.fetchall():
    print(f"  User {row[0]}: {row[1]} recipes")

# Check if recipes have required fields
cursor.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN name IS NULL OR name = '' THEN 1 END) as no_name,
        COUNT(CASE WHEN recipe_data IS NULL THEN 1 END) as no_data
    FROM recipes
    WHERE deleted_at IS NULL
""")
row = cursor.fetchone()
print("\nData quality:")
print(f"  Total: {row[0]}")
print(f"  Missing name: {row[1]}")
print(f"  Missing recipe_data: {row[2]}")

# Sample a few recipes
cursor.execute("SELECT id, name, user_id FROM recipes WHERE deleted_at IS NULL LIMIT 5")
print("\nSample recipes:")
for row in cursor.fetchall():
    print(f'  Recipe {row[0]}: "{row[1]}" (User {row[2]})')

conn.close()
