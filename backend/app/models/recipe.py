"""Recipe model."""

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models._utils import utc_now


class Recipe(Base):
    """Recipe model."""

    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    household_id = Column(
        Integer, ForeignKey("households.id"), nullable=True, index=True
    )

    # Basic info
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    image_url = Column(Text)

    # Full recipe data as JSON
    recipe_data = Column(JSON, nullable=False)

    # Metadata
    source_url = Column(Text, index=True)
    source_type = Column(
        String(20), default="manual", nullable=False
    )  # 'imported' or 'manual'
    is_modified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    imported_at = Column(DateTime)

    # Soft delete
    deleted_at = Column(DateTime, index=True)

    # Denormalized fields for search/filter performance
    cuisine = Column(String(100), index=True)
    category = Column(String(100), index=True)
    total_time_minutes = Column(Integer, index=True)

    # Relationships
    owner = relationship("User", back_populates="recipes")
    household = relationship("Household", back_populates="recipes")
    collections = relationship(
        "RecipeCollection", back_populates="recipe", cascade="all, delete-orphan"
    )
