"""Household API endpoints."""


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.household import Household
from app.models.user import User
from app.schemas.household import (
    Household as HouseholdSchema,
)
from app.schemas.household import (
    HouseholdCreate,
    HouseholdInvitationCreate,
    HouseholdUpdate,
    HouseholdWithMembers,
    InvitationAcceptRequest,
    InvitationDeclineRequest,
)
from app.schemas.household import (
    HouseholdInvitation as HouseholdInvitationSchema,
)
from app.schemas.household import (
    HouseholdMember as HouseholdMemberSchema,
)
from app.services import household as household_service


router = APIRouter()


# ============================================
# Household Management
# ============================================


@router.post("/", response_model=HouseholdSchema, status_code=status.HTTP_201_CREATED)
async def create_household(
    household_data: HouseholdCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new household.

    Args:
        household_data: Household creation data
        current_user: The authenticated user
        db: Database session

    Returns:
        Created household
    """
    household = await household_service.create_household(db, household_data.name, current_user.id)
    return household


@router.get("/me", response_model=HouseholdWithMembers)
async def get_my_household(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current user's household with members and invitations.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        User's household with members
    """
    household = await household_service.get_user_household(db, current_user.id)

    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not belong to a household",
        )

    # Get members with user details
    members = await household_service.get_household_members(db, household.id)
    members_with_details = []

    for member in members:
        user_result = await db.execute(select(User).where(User.id == member.user_id))
        user = user_result.scalar_one()

        member_schema = HouseholdMemberSchema(
            id=member.id,
            household_id=member.household_id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            user_email=user.email,
            user_display_name=user.display_name,
        )
        members_with_details.append(member_schema)

    # Get pending invitations
    invitations = await household_service.get_pending_invitations(db, household.id)

    return HouseholdWithMembers(
        id=household.id,
        name=household.name,
        owner_user_id=household.owner_user_id,
        max_members=household.max_members,
        created_at=household.created_at,
        updated_at=household.updated_at,
        members=members_with_details,
        pending_invitations=invitations,
    )


@router.patch("/{household_id}", response_model=HouseholdSchema)
async def update_household(
    household_id: int,
    household_data: HouseholdUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update household name (owner only).

    Args:
        household_id: Household ID
        household_data: Update data
        current_user: The authenticated user
        db: Database session

    Returns:
        Updated household
    """
    household = await household_service.update_household(
        db, household_id, current_user.id, household_data.name
    )
    return household


@router.delete("/{household_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_household(
    household_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a household (owner only).

    Args:
        household_id: Household ID
        current_user: The authenticated user
        db: Database session
    """
    await household_service.delete_household(db, household_id, current_user.id)


# ============================================
# Household Members
# ============================================


@router.get("/{household_id}/members", response_model=list[HouseholdMemberSchema])
async def get_household_members(
    household_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all members of a household.

    Args:
        household_id: Household ID
        current_user: The authenticated user
        db: Database session

    Returns:
        List of household members
    """
    # Verify user has access to this household
    if not await household_service.check_user_household_access(db, current_user.id, household_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this household",
        )

    members = await household_service.get_household_members(db, household_id)

    # Add user details to each member
    members_with_details = []
    for member in members:
        user_result = await db.execute(select(User).where(User.id == member.user_id))
        user = user_result.scalar_one()

        member_schema = HouseholdMemberSchema(
            id=member.id,
            household_id=member.household_id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            user_email=user.email,
            user_display_name=user.display_name,
        )
        members_with_details.append(member_schema)

    return members_with_details


@router.delete("/{household_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_household_member(
    household_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a member from the household (owner only).

    Args:
        household_id: Household ID
        user_id: User ID to remove
        current_user: The authenticated user
        db: Database session
    """
    await household_service.remove_household_member(db, household_id, user_id, current_user.id)


# ============================================
# Household Invitations
# ============================================


@router.post(
    "/{household_id}/invitations",
    response_model=HouseholdInvitationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    household_id: int,
    invitation_data: HouseholdInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Invite a member to the household (owner only).

    Args:
        household_id: Household ID
        invitation_data: Invitation data
        current_user: The authenticated user
        db: Database session

    Returns:
        Created invitation
    """
    invitation = await household_service.create_invitation(
        db, household_id, current_user.id, invitation_data.invitee_email
    )
    return invitation


@router.get("/{household_id}/invitations", response_model=list[HouseholdInvitationSchema])
async def get_pending_invitations(
    household_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get pending invitations for a household.

    Args:
        household_id: Household ID
        current_user: The authenticated user
        db: Database session

    Returns:
        List of pending invitations
    """
    # Verify user has access to this household
    if not await household_service.check_user_household_access(db, current_user.id, household_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this household",
        )

    invitations = await household_service.get_pending_invitations(db, household_id)
    return invitations


@router.get("/invitations/{token}", response_model=HouseholdInvitationSchema)
async def get_invitation_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get invitation details by token (public endpoint for invitation landing page).

    Args:
        token: Invitation token
        db: Database session

    Returns:
        Invitation details with household and inviter information
    """
    invitation = await household_service.get_invitation_by_token(db, token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or expired",
        )

    # Get household details
    household_result = await db.execute(
        select(Household).where(Household.id == invitation.household_id)
    )
    household = household_result.scalar_one_or_none()

    # Get inviter details
    inviter_result = await db.execute(select(User).where(User.id == invitation.inviter_user_id))
    inviter = inviter_result.scalar_one_or_none()

    return HouseholdInvitationSchema(
        id=invitation.id,
        household_id=invitation.household_id,
        inviter_user_id=invitation.inviter_user_id,
        invitee_email=invitation.invitee_email,
        token=invitation.token,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        created_at=invitation.created_at,
        household_name=household.name if household else None,
        inviter_display_name=inviter.display_name if inviter else None,
    )


@router.post("/invitations/accept", response_model=HouseholdMemberSchema)
async def accept_invitation(
    request: InvitationAcceptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a household invitation.

    Args:
        request: Invitation acceptance request with token
        current_user: The authenticated user
        db: Database session

    Returns:
        Created household member
    """
    member = await household_service.accept_invitation(db, request.token, current_user.id)

    # Get user details
    user_result = await db.execute(select(User).where(User.id == member.user_id))
    user = user_result.scalar_one()

    return HouseholdMemberSchema(
        id=member.id,
        household_id=member.household_id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
        user_email=user.email,
        user_display_name=user.display_name,
    )


@router.post("/invitations/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline_invitation(
    request: InvitationDeclineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Decline/revoke a household invitation.

    Args:
        request: Invitation decline request with token
        current_user: The authenticated user
        db: Database session
    """
    await household_service.decline_invitation(db, request.token, current_user.id)
