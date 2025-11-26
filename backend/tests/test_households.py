"""Tests for household functionality."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models._utils import is_expired
from app.models.user import User
from app.services import household as household_service


@pytest.mark.asyncio
async def test_create_household(db: AsyncSession, test_user: User):
    """Test creating a household."""
    household = await household_service.create_household(db, "Test Household", test_user.id)

    assert household.id is not None
    assert household.name == "Test Household"
    assert household.owner_user_id == test_user.id
    assert household.max_members == 10

    # Verify owner is automatically added as a member
    members = await household_service.get_household_members(db, household.id)
    assert len(members) == 1
    assert members[0].user_id == test_user.id
    assert members[0].role == "owner"


@pytest.mark.asyncio
async def test_create_household_user_already_in_household(db: AsyncSession, test_user: User):
    """Test that a user cannot create multiple households."""
    # Create first household
    await household_service.create_household(db, "First Household", test_user.id)

    # Attempt to create second household should fail
    with pytest.raises(Exception) as exc_info:
        await household_service.create_household(db, "Second Household", test_user.id)

    assert "already belongs to a household" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_user_household(db: AsyncSession, test_user: User):
    """Test getting a user's household."""
    created_household = await household_service.create_household(db, "Test Household", test_user.id)

    household = await household_service.get_user_household(db, test_user.id)

    assert household is not None
    assert household.id == created_household.id
    assert household.name == "Test Household"


@pytest.mark.asyncio
async def test_update_household(db: AsyncSession, test_user: User):
    """Test updating household name."""
    household = await household_service.create_household(db, "Original Name", test_user.id)

    updated = await household_service.update_household(
        db, household.id, test_user.id, "Updated Name"
    )

    assert updated.name == "Updated Name"


@pytest.mark.asyncio
async def test_update_household_non_owner(db: AsyncSession, test_user: User):
    """Test that non-owners cannot update household."""
    household = await household_service.create_household(db, "Test Household", test_user.id)

    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(other_user)
    await db.commit()
    await db.refresh(other_user)

    # Attempt to update as non-owner should fail
    with pytest.raises(Exception) as exc_info:
        await household_service.update_household(db, household.id, other_user.id, "New Name")

    assert "owner" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_invitation(db: AsyncSession, test_user: User):
    """Test creating a household invitation."""
    household = await household_service.create_household(db, "Test Household", test_user.id)

    invitation = await household_service.create_invitation(
        db, household.id, test_user.id, "invitee@example.com"
    )

    assert invitation.id is not None
    assert invitation.household_id == household.id
    assert invitation.inviter_user_id == test_user.id
    assert invitation.invitee_email == "invitee@example.com"
    assert invitation.token is not None
    # SQLite stores datetime as naive, so we need to compare properly
    assert not is_expired(invitation.expires_at)
    assert invitation.accepted_at is None


@pytest.mark.asyncio
async def test_accept_invitation(db: AsyncSession, test_user: User):
    """Test accepting a household invitation."""
    # Create household
    household = await household_service.create_household(db, "Test Household", test_user.id)

    # Create invitee user
    invitee = User(
        email="invitee@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(invitee)
    await db.commit()
    await db.refresh(invitee)

    # Create invitation
    invitation = await household_service.create_invitation(
        db, household.id, test_user.id, "invitee@example.com"
    )

    # Accept invitation
    member = await household_service.accept_invitation(db, invitation.token, invitee.id)

    assert member.household_id == household.id
    assert member.user_id == invitee.id
    assert member.role == "member"

    # Verify invitation is marked as accepted
    await db.refresh(invitation)
    assert invitation.accepted_at is not None

    # Verify household now has 2 members
    members = await household_service.get_household_members(db, household.id)
    assert len(members) == 2


@pytest.mark.asyncio
async def test_accept_invitation_wrong_email(db: AsyncSession, test_user: User):
    """Test that invitation cannot be accepted by wrong email."""
    household = await household_service.create_household(db, "Test Household", test_user.id)

    # Create invitation for specific email
    invitation = await household_service.create_invitation(
        db, household.id, test_user.id, "invitee@example.com"
    )

    # Create user with different email
    wrong_user = User(
        email="wrong@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(wrong_user)
    await db.commit()
    await db.refresh(wrong_user)

    # Attempt to accept should fail
    with pytest.raises(Exception) as exc_info:
        await household_service.accept_invitation(db, invitation.token, wrong_user.id)

    assert "different email" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_remove_household_member(db: AsyncSession, test_user: User):
    """Test removing a member from household."""
    household = await household_service.create_household(db, "Test Household", test_user.id)

    # Add a member
    member_user = User(
        email="member@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(member_user)
    await db.commit()
    await db.refresh(member_user)

    invitation = await household_service.create_invitation(
        db, household.id, test_user.id, "member@example.com"
    )
    await household_service.accept_invitation(db, invitation.token, member_user.id)

    # Verify 2 members
    members = await household_service.get_household_members(db, household.id)
    assert len(members) == 2

    # Remove the member
    await household_service.remove_household_member(db, household.id, member_user.id, test_user.id)

    # Verify back to 1 member
    members = await household_service.get_household_members(db, household.id)
    assert len(members) == 1
    assert members[0].user_id == test_user.id


@pytest.mark.asyncio
async def test_cannot_remove_owner(db: AsyncSession, test_user: User):
    """Test that household owner cannot be removed."""
    household = await household_service.create_household(db, "Test Household", test_user.id)

    # Attempt to remove owner should fail
    with pytest.raises(Exception) as exc_info:
        await household_service.remove_household_member(
            db, household.id, test_user.id, test_user.id
        )

    assert "owner" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_household_size_limit(db: AsyncSession, test_user: User):
    """Test household size limit enforcement."""
    # Create household with small limit
    household = await household_service.create_household(
        db, "Test Household", test_user.id, max_members=2
    )

    # Add one member (household now has 2: owner + member)
    member_user = User(
        email="member@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(member_user)
    await db.commit()
    await db.refresh(member_user)

    invitation = await household_service.create_invitation(
        db, household.id, test_user.id, "member@example.com"
    )
    await household_service.accept_invitation(db, invitation.token, member_user.id)

    # Attempt to invite another member should fail (would exceed limit)
    with pytest.raises(Exception) as exc_info:
        await household_service.create_invitation(
            db, household.id, test_user.id, "another@example.com"
        )

    assert "maximum size" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_check_household_access(db: AsyncSession, test_user: User):
    """Test checking user household access."""
    household = await household_service.create_household(db, "Test Household", test_user.id)

    # User should have access to their household
    has_access = await household_service.check_user_household_access(db, test_user.id, household.id)
    assert has_access is True

    # Other user should not have access
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(other_user)
    await db.commit()
    await db.refresh(other_user)

    has_access = await household_service.check_user_household_access(
        db, other_user.id, household.id
    )
    assert has_access is False


@pytest.mark.asyncio
async def test_decline_invitation(db: AsyncSession, test_user: User):
    """Test declining an invitation."""
    household = await household_service.create_household(db, "Test Household", test_user.id)

    # Create invitee user
    invitee = User(
        email="invitee@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(invitee)
    await db.commit()
    await db.refresh(invitee)

    # Create invitation
    invitation = await household_service.create_invitation(
        db, household.id, test_user.id, "invitee@example.com"
    )

    # Decline invitation
    await household_service.decline_invitation(db, invitation.token, invitee.id)

    # Verify invitation is deleted
    pending = await household_service.get_pending_invitations(db, household.id)
    assert len(pending) == 0
