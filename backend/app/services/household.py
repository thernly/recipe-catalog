"""Household service functions."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from wonderwords import RandomWord

from app.core.email import email_service
from app.models.household import (
    Household,
    HouseholdInvitation,
    HouseholdInviteLink,
    HouseholdMember,
)
from app.models.user import User


# Initialize wonderwords random word generator
_random_word = RandomWord()


# ============================================
# Household Management
# ============================================

MSG_USER_ALREADY_IN_HOUSEHOLD = "User already belongs to a household"


async def create_default_household_for_new_user(
    db: AsyncSession, user: User, max_members: int = 10
) -> Household:
    """
    Create a default household for a newly registered user.

    This function is specifically for use during user registration and does not
    check for existing household membership (since the user is brand new).

    Args:
        db: Database session
        user: The newly created user
        max_members: Maximum number of members allowed (default 10)

    Returns:
        Created household
    """
    # Create a user-friendly default household name
    # Use display name if available, otherwise use email prefix
    if user.display_name:
        household_name = f"{user.display_name}'s Household"
    else:
        # Extract name from email (part before @)
        email_prefix = user.email.split("@")[0]
        household_name = f"{email_prefix}'s Household"

    # Create household
    household = Household(name=household_name, owner_user_id=user.id, max_members=max_members)
    db.add(household)
    await db.flush()

    # Add owner as a member with owner role
    member = HouseholdMember(household_id=household.id, user_id=user.id, role="owner")
    db.add(member)

    # Note: We don't commit here - let the calling function handle the transaction
    # This allows the household creation to be part of the larger registration transaction

    return household


async def create_household(
    db: AsyncSession, name: str, owner_user_id: int, max_members: int = 10
) -> Household:
    """
    Create a new household.

    Args:
        db: Database session
        name: Household name
        owner_user_id: ID of the user who owns the household
        max_members: Maximum number of members allowed (default 10)

    Returns:
        Created household

    Raises:
        HTTPException: If user already belongs to a household
    """
    # Check if user already belongs to a household (one household per user rule)
    existing_membership = await db.execute(
        select(HouseholdMember).where(HouseholdMember.user_id == owner_user_id)
    )
    if existing_membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_USER_ALREADY_IN_HOUSEHOLD,
        )

    # Create household
    household = Household(name=name, owner_user_id=owner_user_id, max_members=max_members)
    db.add(household)
    await db.flush()

    # Add owner as a member with owner role
    member = HouseholdMember(household_id=household.id, user_id=owner_user_id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(household)

    return household


async def get_household(db: AsyncSession, household_id: int) -> Household | None:
    """
    Get household by ID.

    Args:
        db: Database session
        household_id: Household ID

    Returns:
        Household or None
    """
    result = await db.execute(select(Household).where(Household.id == household_id))
    return result.scalar_one_or_none()


async def get_user_household(db: AsyncSession, user_id: int) -> Household | None:
    """
    Get the household that a user belongs to.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Household or None
    """
    result = await db.execute(
        select(Household).join(HouseholdMember).where(HouseholdMember.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_household(
    db: AsyncSession, household_id: int, user_id: int, name: str
) -> Household:
    """
    Update household name.

    Args:
        db: Database session
        household_id: Household ID
        user_id: User ID (must be owner)
        name: New household name

    Returns:
        Updated household

    Raises:
        HTTPException: If household not found or user is not owner
    """
    household = await get_household(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")

    if household.owner_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the household owner can update the household",
        )

    household.name = name
    await db.commit()
    await db.refresh(household)

    return household


async def delete_household(db: AsyncSession, household_id: int, user_id: int) -> None:
    """
    Delete a household (owner only).

    Args:
        db: Database session
        household_id: Household ID
        user_id: User ID (must be owner)

    Raises:
        HTTPException: If household not found or user is not owner
    """
    household = await get_household(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")

    if household.owner_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the household owner can delete the household",
        )

    await db.delete(household)
    await db.commit()


# ============================================
# Household Members
# ============================================


async def get_household_members(db: AsyncSession, household_id: int) -> list[HouseholdMember]:
    """
    Get all members of a household.

    Args:
        db: Database session
        household_id: Household ID

    Returns:
        List of household members
    """
    result = await db.execute(
        select(HouseholdMember).where(HouseholdMember.household_id == household_id)
    )
    return list(result.scalars().all())


async def remove_household_member(
    db: AsyncSession, household_id: int, member_user_id: int, requester_user_id: int
) -> None:
    """
    Remove a member from the household.

    Args:
        db: Database session
        household_id: Household ID
        member_user_id: User ID of the member to remove
        requester_user_id: User ID of the requester (must be owner)

    Raises:
        HTTPException: If household not found, user is not owner, or trying to remove owner
    """
    household = await get_household(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")

    if household.owner_user_id != requester_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the household owner can remove members",
        )

    if member_user_id == household.owner_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the household owner",
        )

    # Find and remove the member
    result = await db.execute(
        select(HouseholdMember).where(
            and_(
                HouseholdMember.household_id == household_id,
                HouseholdMember.user_id == member_user_id,
            )
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    await db.delete(member)
    await db.commit()


async def check_household_size_limit(db: AsyncSession, household_id: int) -> bool:
    """
    Check if household has reached its size limit.

    Args:
        db: Database session
        household_id: Household ID

    Returns:
        True if limit not reached, False otherwise
    """
    household = await get_household(db, household_id)
    if not household:
        return False

    result = await db.execute(
        select(func.count(HouseholdMember.id)).where(HouseholdMember.household_id == household_id)
    )
    current_size = result.scalar_one()

    return current_size < household.max_members


# ============================================
# Household Invitations
# ============================================


def generate_invitation_token() -> str:
    """Generate a secure random token for invitation."""
    return secrets.token_urlsafe(32)


async def create_invitation(
    db: AsyncSession,
    household_id: int,
    inviter_user_id: int,
    invitee_email: str,
    expiration_days: int = 7,
) -> HouseholdInvitation:
    """
    Create a household invitation.

    Args:
        db: Database session
        household_id: Household ID
        inviter_user_id: User ID of the inviter (must be owner)
        invitee_email: Email of the person to invite
        expiration_days: Number of days until invitation expires (default 7)

    Returns:
        Created invitation

    Raises:
        HTTPException: If household not found, user is not owner, or household is full
    """
    household = await get_household(db, household_id)
    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")

    if household.owner_user_id != inviter_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the household owner can invite members",
        )

    # Check household size limit
    if not await check_household_size_limit(db, household_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Household has reached its maximum size",
        )

    # Check if user is already invited or a member
    existing_invitation_result = await db.execute(
        select(HouseholdInvitation).where(
            and_(
                HouseholdInvitation.household_id == household_id,
                HouseholdInvitation.invitee_email == invitee_email,
                HouseholdInvitation.accepted_at.is_(None),
            )
        )
    )
    existing_invitation = existing_invitation_result.scalar_one_or_none()
    if existing_invitation:
        # Check if invitation is still valid (not expired)
        expires_at_utc = (
            existing_invitation.expires_at.replace(tzinfo=UTC)
            if existing_invitation.expires_at.tzinfo is None
            else existing_invitation.expires_at
        )
        if expires_at_utc > datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a pending invitation",
            )

    # Check if invitee is already a member
    invitee_user = await db.execute(select(User).where(User.email == invitee_email))
    invitee = invitee_user.scalar_one_or_none()
    if invitee:
        existing_member = await db.execute(
            select(HouseholdMember).where(HouseholdMember.user_id == invitee.id)
        )
        if existing_member.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_USER_ALREADY_IN_HOUSEHOLD,
            )

    # Create invitation
    token = generate_invitation_token()
    expires_at = datetime.now(UTC) + timedelta(days=expiration_days)

    invitation = HouseholdInvitation(
        household_id=household_id,
        inviter_user_id=inviter_user_id,
        invitee_email=invitee_email,
        token=token,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    # Send invitation email
    await send_invitation_email(db, invitation)

    return invitation


async def send_invitation_email(db: AsyncSession, invitation: HouseholdInvitation) -> None:
    """
    Send invitation email to invitee.

    Args:
        db: Database session
        invitation: Invitation to send
    """
    household = await get_household(db, invitation.household_id)
    inviter_result = await db.execute(select(User).where(User.id == invitation.inviter_user_id))
    inviter = inviter_result.scalar_one()

    # Construct invitation URL (this would be your frontend URL)
    # For now, we'll just use a placeholder
    invitation_url = f"http://localhost:5173/invitations/accept?token={invitation.token}"

    subject = f"You've been invited to join {household.name}"
    body = f"""
    Hello!

    {inviter.email} has invited you to join their household "{household.name}" on Recipe Catalog.

    Click the link below to accept the invitation:
    {invitation_url}

    This invitation will expire on {invitation.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")}.

    If you don't have an account yet, you'll be prompted to create one.

    Best regards,
    The Recipe Catalog Team
    """

    # Create HTML version of the email
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #F59E0B; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #F59E0B;
                      color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Recipe Catalog</h1>
            </div>
            <div class="content">
                <h2>You've been invited!</h2>
                <p>{inviter.email} has invited you to join their household "<strong>{household.name}</strong>" on Recipe Catalog.</p>
                <p style="text-align: center;">
                    <a href="{invitation_url}" class="button">Accept Invitation</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: #fff; padding: 10px; border-radius: 3px;">
                    {invitation_url}
                </p>
                <p><strong>This invitation will expire on {invitation.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")}.</strong></p>
                <p>If you don't have an account yet, you'll be prompted to create one.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Recipe Catalog. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    await email_service.send_email(invitation.invitee_email, subject, html_body, body)


async def get_pending_invitations(db: AsyncSession, household_id: int) -> list[HouseholdInvitation]:
    """
    Get pending invitations for a household.

    Args:
        db: Database session
        household_id: Household ID

    Returns:
        List of pending invitations
    """
    result = await db.execute(
        select(HouseholdInvitation).where(
            and_(
                HouseholdInvitation.household_id == household_id,
                HouseholdInvitation.accepted_at.is_(None),
            )
        )
    )
    invitations = list(result.scalars().all())

    # Filter out expired invitations (SQLite stores datetime as naive)
    now_utc = datetime.now(UTC)
    active_invitations = []
    for inv in invitations:
        expires_at_utc = (
            inv.expires_at.replace(tzinfo=UTC) if inv.expires_at.tzinfo is None else inv.expires_at
        )
        if expires_at_utc > now_utc:
            active_invitations.append(inv)

    return active_invitations


async def get_invitation_by_token(db: AsyncSession, token: str) -> HouseholdInvitation | None:
    """
    Get invitation by token (for public invitation landing page).

    Args:
        db: Database session
        token: Invitation token

    Returns:
        Invitation if found and not expired, None otherwise
    """
    result = await db.execute(select(HouseholdInvitation).where(HouseholdInvitation.token == token))
    invitation = result.scalar_one_or_none()

    if not invitation:
        return None

    # Check if expired (SQLite stores datetime as naive)
    now_utc = datetime.now(UTC)
    expires_at_utc = (
        invitation.expires_at.replace(tzinfo=UTC)
        if invitation.expires_at.tzinfo is None
        else invitation.expires_at
    )

    if expires_at_utc < now_utc:
        return None

    return invitation


async def accept_invitation(db: AsyncSession, token: str, user_id: int) -> HouseholdMember:
    """
    Accept a household invitation.

    Args:
        db: Database session
        token: Invitation token
        user_id: User ID accepting the invitation

    Returns:
        Created household member

    Raises:
        HTTPException: If invitation not found, expired, or user already in a household
    """
    # Find invitation
    result = await db.execute(select(HouseholdInvitation).where(HouseholdInvitation.token == token))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    # Check if already accepted
    if invitation.accepted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already accepted",
        )

    # Check if expired
    # SQLite stores datetime as naive, so we need to compare with naive datetime
    expires_at_utc = (
        invitation.expires_at.replace(tzinfo=UTC)
        if invitation.expires_at.tzinfo is None
        else invitation.expires_at
    )
    if expires_at_utc < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
        )

    # Verify email matches
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    if user.email != invitation.invitee_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitation is for a different email address",
        )

    # Check if user already belongs to a household
    existing_membership = await db.execute(
        select(HouseholdMember).where(HouseholdMember.user_id == user_id)
    )
    if existing_membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_USER_ALREADY_IN_HOUSEHOLD,
        )

    # Check household size limit
    if not await check_household_size_limit(db, invitation.household_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Household has reached its maximum size",
        )

    # Create household member
    member = HouseholdMember(household_id=invitation.household_id, user_id=user_id, role="member")
    db.add(member)

    # Mark invitation as accepted
    invitation.accepted_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(member)

    return member


async def decline_invitation(db: AsyncSession, token: str, user_id: int) -> None:
    """
    Decline/revoke a household invitation.

    Args:
        db: Database session
        token: Invitation token
        user_id: User ID declining the invitation

    Raises:
        HTTPException: If invitation not found
    """
    result = await db.execute(select(HouseholdInvitation).where(HouseholdInvitation.token == token))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    # Verify user has permission to decline (invitee or household owner)
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    household = await get_household(db, invitation.household_id)

    if user.email != invitation.invitee_email and user_id != household.owner_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to decline this invitation",
        )

    await db.delete(invitation)
    await db.commit()


async def check_user_household_access(db: AsyncSession, user_id: int, household_id: int) -> bool:
    """
    Check if a user has access to a household.

    Args:
        db: Database session
        user_id: User ID
        household_id: Household ID

    Returns:
        True if user is a member of the household
    """
    result = await db.execute(
        select(HouseholdMember).where(
            and_(
                HouseholdMember.user_id == user_id,
                HouseholdMember.household_id == household_id,
            )
        )
    )
    return result.scalar_one_or_none() is not None


# ============================================
# Household Invite Links
# ============================================


def generate_invite_code() -> str:
    """
    Generate a readable invite code using three random words.

    Uses wonderwords library to generate random nouns for easy-to-remember codes.

    Returns:
        A code in the format "word1-word2-word3"
    """
    words = [_random_word.word(include_parts_of_speech=["nouns"]) for _ in range(3)]
    return "-".join(words)


async def create_invite_link(
    db: AsyncSession, household_id: int, created_by_user_id: int, expires_in_days: int = 7
) -> HouseholdInviteLink:
    """
    Create a one-time use invite link for a household.

    Args:
        db: Database session
        household_id: Household ID
        created_by_user_id: User creating the invite link
        expires_in_days: Days until expiration (default 7)

    Returns:
        Created invite link

    Raises:
        HTTPException: If household not found or user doesn't have permission
    """
    # Verify household exists
    household_result = await db.execute(select(Household).where(Household.id == household_id))
    household = household_result.scalar_one_or_none()

    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")

    # Verify user is owner or member of household
    if not await check_user_household_access(db, created_by_user_id, household_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this household",
        )

    # Generate unique code
    max_attempts = 10
    for _ in range(max_attempts):
        code = generate_invite_code()
        # Check if code already exists
        existing = await db.execute(
            select(HouseholdInviteLink).where(HouseholdInviteLink.code == code)
        )
        if not existing.scalar_one_or_none():
            break
    else:
        # Fallback to UUID-based code if we can't generate unique word-based code
        import uuid

        code = str(uuid.uuid4())[:8]

    # Create invite link
    expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
    invite_link = HouseholdInviteLink(
        household_id=household_id,
        code=code,
        created_by_user_id=created_by_user_id,
        expires_at=expires_at,
    )
    db.add(invite_link)
    await db.commit()
    await db.refresh(invite_link)

    return invite_link


async def get_invite_link_by_code(db: AsyncSession, code: str) -> HouseholdInviteLink | None:
    """
    Get an invite link by its code.

    Args:
        db: Database session
        code: Invite code (case-insensitive, ignores hyphens and spaces)

    Returns:
        Invite link if found, None otherwise
    """
    # Normalize code: lowercase, remove hyphens and spaces
    normalized_code = code.lower().replace("-", "").replace(" ", "")

    # Try exact match first
    result = await db.execute(select(HouseholdInviteLink).where(HouseholdInviteLink.code == code))
    invite_link = result.scalar_one_or_none()

    if not invite_link:
        # Try normalized match (search all codes and normalize them)
        all_links_result = await db.execute(select(HouseholdInviteLink))
        all_links = all_links_result.scalars().all()

        for link in all_links:
            normalized_link_code = link.code.lower().replace("-", "").replace(" ", "")
            if normalized_link_code == normalized_code:
                invite_link = link
                break

    return invite_link


async def join_via_invite_link(db: AsyncSession, code: str, user_id: int) -> HouseholdMember:
    """
    Join a household using an invite link code.

    Args:
        db: Database session
        code: Invite code
        user_id: User ID joining the household

    Returns:
        Created household member

    Raises:
        HTTPException: If code invalid, expired, already used, or user already in household
    """
    # Find invite link
    invite_link = await get_invite_link_by_code(db, code)

    if not invite_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite code not found",
        )

    # Check if already used
    if invite_link.used_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invite code has already been used",
        )

    # Check if expired
    expires_at_utc = (
        invite_link.expires_at.replace(tzinfo=UTC)
        if invite_link.expires_at.tzinfo is None
        else invite_link.expires_at
    )
    if expires_at_utc < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invite code has expired",
        )

    # Check if user already belongs to a household
    existing_membership = await db.execute(
        select(HouseholdMember).where(HouseholdMember.user_id == user_id)
    )
    current_member = existing_membership.scalar_one_or_none()
    if current_member:
        # Get current household info for better error message
        household_result = await db.execute(
            select(Household).where(Household.id == current_member.household_id)
        )
        current_household = household_result.scalar_one_or_none()
        household_name = current_household.name if current_household else "a household"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are already in '{household_name}'. Leave your current household first to join this one.",
        )

    # Check household size limit
    if not await check_household_size_limit(db, invite_link.household_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Household has reached its maximum size",
        )

    # Create household member
    member = HouseholdMember(
        household_id=invite_link.household_id,
        user_id=user_id,
        role="member",
    )
    db.add(member)

    # Mark invite link as used (one-time use)
    invite_link.used_at = datetime.now(UTC)
    invite_link.used_by_user_id = user_id

    await db.commit()
    await db.refresh(member)

    return member


async def leave_household(db: AsyncSession, user_id: int) -> dict:
    """
    Remove a user from their household.

    Args:
        db: Database session
        user_id: User ID leaving the household

    Returns:
        Dictionary with message and whether household was deleted

    Raises:
        HTTPException: If user not in household or is owner with other members
    """
    # Find user's household membership
    member_result = await db.execute(
        select(HouseholdMember).where(HouseholdMember.user_id == user_id)
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of any household",
        )

    household_id = member.household_id

    # Get household
    household_result = await db.execute(select(Household).where(Household.id == household_id))
    household = household_result.scalar_one_or_none()

    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")

    # Check if user is the owner
    is_owner = member.role == "owner"

    # Count other members
    other_members_result = await db.execute(
        select(func.count(HouseholdMember.id)).where(
            and_(
                HouseholdMember.household_id == household_id,
                HouseholdMember.user_id != user_id,
            )
        )
    )
    other_members_count = other_members_result.scalar()

    if is_owner and other_members_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot leave household as owner while other members exist. Transfer ownership or remove other members first.",
        )

    # Remove user from household
    await db.delete(member)

    household_deleted = False

    # If owner leaving and no other members, delete the household
    if is_owner and other_members_count == 0:
        await db.delete(household)
        household_deleted = True

    await db.commit()

    return {
        "message": "Successfully left household"
        if not household_deleted
        else "Successfully left and deleted household",
        "household_deleted": household_deleted,
    }
