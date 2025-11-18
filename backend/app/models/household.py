"""Household models."""

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models._utils import utc_now


class Household(Base):
    """Household model for multi-user tenancy."""

    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    max_members = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_user_id])
    members = relationship(
        "HouseholdMember", back_populates="household", cascade="all, delete-orphan"
    )
    invitations = relationship(
        "HouseholdInvitation", back_populates="household", cascade="all, delete-orphan"
    )
    recipes = relationship("Recipe", back_populates="household")
    collections = relationship("Collection", back_populates="household")


class HouseholdMember(Base):
    """Household member junction table."""

    __tablename__ = "household_members"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(
        Integer, ForeignKey("households.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default="member", nullable=False)  # 'owner' or 'member'
    joined_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    household = relationship("Household", back_populates="members")
    user = relationship("User")

    # Constraints
    __table_args__ = (
        UniqueConstraint("household_id", "user_id", name="uq_household_user"),
    )


class HouseholdInvitation(Base):
    """Household invitation model."""

    __tablename__ = "household_invitations"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(
        Integer, ForeignKey("households.id"), nullable=False, index=True
    )
    inviter_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    household = relationship("Household", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_user_id])
