"""Meal planning models."""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models._utils import utc_now


class MealPlan(Base):
    """Meal plan model for weekly meal planning."""

    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False, index=True)
    week_start_date = Column(Date, nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    household = relationship("Household", overlaps="meal_plans")
    creator = relationship("User", foreign_keys=[created_by_user_id])
    planned_meals = relationship(
        "PlannedMeal", back_populates="meal_plan", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("household_id", "week_start_date", name="uq_household_week"),
    )


class PlannedMeal(Base):
    """Planned meal model for individual meals in a meal plan."""

    __tablename__ = "planned_meals"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    meal_type = Column(String(20), nullable=False)  # breakfast, lunch, dinner, snack, other
    servings = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="planned_meals")
    recipe = relationship("Recipe")

    # Constraints and indexes
    __table_args__ = (
        Index("ix_planned_meals_day_meal", "meal_plan_id", "day_of_week", "meal_type"),
    )
