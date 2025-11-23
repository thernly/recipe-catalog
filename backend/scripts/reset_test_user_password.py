"""Reset testuser password to a known value."""

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User


async def reset_password():
    """Reset testuser@test.example.com password to 'password123'."""
    async with AsyncSessionLocal() as db:
        # Get the user
        result = await db.execute(select(User).where(User.email == "testuser@test.example.com"))
        user = result.scalar_one_or_none()

        if not user:
            print("User not found!")
            return

        # Update password and mark as verified
        new_password = "password123"
        hashed = get_password_hash(new_password)

        user.hashed_password = hashed
        user.is_verified = True  # Also mark as verified
        user.is_active = True

        await db.commit()

        print(f"✅ Password reset for {user.email}")
        print("   Email: testuser@test.example.com")
        print("   Password: password123")
        print(f"   Is Active: {user.is_active}")
        print(f"   Is Verified: {user.is_verified}")


if __name__ == "__main__":
    asyncio.run(reset_password())
