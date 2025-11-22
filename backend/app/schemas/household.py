"""Household-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================
# Household Schemas
# ============================================


class HouseholdBase(BaseModel):
    """Base household schema."""

    name: str = Field(..., min_length=1, max_length=100)


class HouseholdCreate(HouseholdBase):
    """Schema for creating a household."""

    pass


class HouseholdUpdate(BaseModel):
    """Schema for updating a household."""

    name: str | None = Field(None, min_length=1, max_length=100)


class Household(HouseholdBase):
    """Full household schema (response)."""

    id: int
    owner_user_id: int
    max_members: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Household Member Schemas
# ============================================


class HouseholdMemberBase(BaseModel):
    """Base household member schema."""

    user_id: int
    role: str = Field("member", pattern="^(owner|member)$")


class HouseholdMember(HouseholdMemberBase):
    """Full household member schema (response)."""

    id: int
    household_id: int
    joined_at: datetime
    # Include user details for convenience
    user_email: str | None = None
    user_display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Household Invitation Schemas
# ============================================


class HouseholdInvitationCreate(BaseModel):
    """Schema for creating a household invitation."""

    invitee_email: EmailStr


class HouseholdInvitation(BaseModel):
    """Full household invitation schema (response)."""

    id: int
    household_id: int
    inviter_user_id: int
    invitee_email: str
    token: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime
    # Include related entity details for convenience
    household_name: str | None = None
    inviter_display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InvitationAcceptRequest(BaseModel):
    """Schema for accepting an invitation."""

    token: str


class InvitationDeclineRequest(BaseModel):
    """Schema for declining an invitation."""

    token: str


# ============================================
# Household Response with Members
# ============================================


class HouseholdWithMembers(Household):
    """Household schema with members included."""

    members: list[HouseholdMember] = []
    pending_invitations: list[HouseholdInvitation] = []
