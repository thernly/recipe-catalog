import sqlite3


conn = sqlite3.connect("recipes.db")
cursor = conn.cursor()

# Check for specific user
cursor.execute(
    "SELECT email, is_active, is_verified FROM users WHERE email = 'testuser@test.example.com'"
)
result = cursor.fetchone()
print("User found:", result if result else "No user found")

# List all users
cursor.execute("SELECT email, is_active, is_verified FROM users")
all_users = cursor.fetchall()
print("\nAll users in database:")
for user in all_users:
    print(f"  Email: {user[0]}, Active: {user[1]}, Verified: {user[2]}")

conn.close()
