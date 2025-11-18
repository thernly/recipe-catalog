"""Collection models."""

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models._utils import utc_now


class Collection(Base):
    """Collection model."""

    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    household_id = Column(
        Integer, ForeignKey("households.id"), nullable=True, index=True
    )
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False, nullable=False, index=True)
    icon = Column(String(50))
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="collections")
    household = relationship("Household", back_populates="collections")
    recipes = relationship(
        "RecipeCollection", back_populates="collection", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_collection_name"),
    )


class RecipeCollection(Base):
    """Recipe-Collection junction table."""

    __tablename__ = "recipe_collections"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False, index=True)
    collection_id = Column(
        Integer, ForeignKey("collections.id"), nullable=False, index=True
    )
    added_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="collections")
    collection = relationship("Collection", back_populates="recipes")

    # Constraints
    __table_args__ = (
        UniqueConstraint("recipe_id", "collection_id", name="uq_recipe_collection"),
    )
