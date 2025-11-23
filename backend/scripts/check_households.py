import sqlite3


conn = sqlite3.connect("recipes.db")
cursor = conn.cursor()

# Check users and their households
cursor.execute("""
    SELECT u.id, u.email, hm.household_id
    FROM users u
    LEFT JOIN household_members hm ON u.id = hm.user_id
""")
print("Users and their households:")
for row in cursor.fetchall():
    print(f"  User {row[0]} ({row[1]}): Household {row[2]}")

# Check recipes and their household assignments
cursor.execute("""
    SELECT user_id, household_id, COUNT(*)
    FROM recipes
    WHERE deleted_at IS NULL
    GROUP BY user_id, household_id
""")
print("\nRecipes by user and household:")
for row in cursor.fetchall():
    print(f"  User {row[0]}, Household {row[1]}: {row[2]} recipes")

# Check all households
cursor.execute("SELECT id, name, owner_id FROM households")
print("\nHouseholds:")
for row in cursor.fetchall():
    print(f"  Household {row[0]}: {row[1]} (Owner: {row[2]})")

conn.close()
