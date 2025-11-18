"""Shopping list models."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models._utils import utc_now


class ShoppingList(Base):
    """Shopping list model."""

    __tablename__ = "shopping_lists"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(
        Integer, ForeignKey("households.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(20), nullable=False, default="active", index=True
    )  # active, archived
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    household = relationship("Household")
    creator = relationship("User", foreign_keys=[created_by_user_id])
    items = relationship(
        "ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan"
    )


class ShoppingListItem(Base):
    """Shopping list item model."""

    __tablename__ = "shopping_list_items"

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(
        Integer, ForeignKey("shopping_lists.id"), nullable=False, index=True
    )
    item_name = Column(String(255), nullable=False)
    quantity = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    checked = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")

    # Constraints and indexes
    __table_args__ = (Index("ix_shopping_list_items_checked", "list_id", "checked"),)
