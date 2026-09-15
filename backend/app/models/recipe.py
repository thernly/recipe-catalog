"""Recipe model."""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models._utils import utc_now


class Recipe(Base):
    """Recipe model."""

    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=True, index=True)

    # Basic info
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    image_url = Column(Text)

    # Full recipe data as JSON following schema.org/Recipe format
    # Note: Uses camelCase (e.g., recipeIngredient, recipeInstructions) per schema.org standard,
    # not Python's snake_case convention. This enables compatibility with recipe import/export.
    recipe_data = Column(JSON, nullable=False)

    # Metadata
    source_url = Column(Text, index=True)
    source_type = Column(String(20), default="manual", nullable=False)  # 'imported' or 'manual'
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

    # Composite indexes for the household-scoped list and search queries.
    # Created in migration 291505919b8f; declared here so --autogenerate does not
    # propose dropping them.
    __table_args__ = (
        Index("idx_recipes_household_deleted", "household_id", "deleted_at"),
        Index("idx_recipes_household_created", "household_id", "created_at"),
    )
