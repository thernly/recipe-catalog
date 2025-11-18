"""Household service functions."""

import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException, status

from app.models.household import Household, HouseholdMember, HouseholdInvitation
from app.models.user import User
from app.core.email import email_service


# ============================================
# Household Management
# ============================================


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
            detail="User already belongs to a household",
        )

    # Create household
    household = Household(
        name=name, owner_user_id=owner_user_id, max_members=max_members
    )
    db.add(household)
    await db.flush()

    # Add owner as a member with owner role
    member = HouseholdMember(
        household_id=household.id, user_id=owner_user_id, role="owner"
    )
    db.add(member)
    await db.commit()
    await db.refresh(household)

    return household


async def get_household(db: AsyncSession, household_id: int) -> Optional[Household]:
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


async def get_user_household(db: AsyncSession, user_id: int) -> Optional[Household]:
    """
    Get the household that a user belongs to.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Household or None
    """
    result = await db.execute(
        select(Household)
        .join(HouseholdMember)
        .where(HouseholdMember.user_id == user_id)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Household not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Household not found"
        )

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


async def get_household_members(
    db: AsyncSession, household_id: int
) -> list[HouseholdMember]:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Household not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

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
        select(func.count(HouseholdMember.id)).where(
            HouseholdMember.household_id == household_id
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Household not found"
        )

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
                detail="User already belongs to a household",
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


async def send_invitation_email(
    db: AsyncSession, invitation: HouseholdInvitation
) -> None:
    """
    Send invitation email to invitee.

    Args:
        db: Database session
        invitation: Invitation to send
    """
    household = await get_household(db, invitation.household_id)
    inviter_result = await db.execute(
        select(User).where(User.id == invitation.inviter_user_id)
    )
    inviter = inviter_result.scalar_one()

    # Construct invitation URL (this would be your frontend URL)
    # For now, we'll just use a placeholder
    invitation_url = (
        f"http://localhost:5173/invitations/accept?token={invitation.token}"
    )

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


async def get_pending_invitations(
    db: AsyncSession, household_id: int
) -> list[HouseholdInvitation]:
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
            inv.expires_at.replace(tzinfo=UTC)
            if inv.expires_at.tzinfo is None
            else inv.expires_at
        )
        if expires_at_utc > now_utc:
            active_invitations.append(inv)

    return active_invitations


async def get_invitation_by_token(
    db: AsyncSession, token: str
) -> Optional[HouseholdInvitation]:
    """
    Get invitation by token (for public invitation landing page).

    Args:
        db: Database session
        token: Invitation token

    Returns:
        Invitation if found and not expired, None otherwise
    """
    result = await db.execute(
        select(HouseholdInvitation).where(HouseholdInvitation.token == token)
    )
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


async def accept_invitation(
    db: AsyncSession, token: str, user_id: int
) -> HouseholdMember:
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
    result = await db.execute(
        select(HouseholdInvitation).where(HouseholdInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )

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
            detail="User already belongs to a household",
        )

    # Check household size limit
    if not await check_household_size_limit(db, invitation.household_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Household has reached its maximum size",
        )

    # Create household member
    member = HouseholdMember(
        household_id=invitation.household_id, user_id=user_id, role="member"
    )
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
    result = await db.execute(
        select(HouseholdInvitation).where(HouseholdInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )

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


async def check_user_household_access(
    db: AsyncSession, user_id: int, household_id: int
) -> bool:
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
