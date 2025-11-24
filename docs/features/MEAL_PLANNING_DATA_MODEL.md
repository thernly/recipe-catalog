# Meal Planning Data Model

## Overview

This document describes the database schema and data model for the Weekly Meal Planning feature (Feature 16). The meal planning system consists of two main entities: `MealPlan` and `PlannedMeal`.

## Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐
│  Household  │────┬────│   MealPlan   │
└─────────────┘    │    └──────────────┘
                   │            │
┌─────────────┐    │            │ 1:N
│    User     │────┘            │
└─────────────┘                 ▼
                        ┌──────────────┐         ┌─────────────┐
                        │ PlannedMeal  │────────▶│   Recipe    │
                        └──────────────┘   N:1   └─────────────┘
```

## Database Tables

### meal_plans

The `meal_plans` table stores weekly meal planning containers for each household.

#### Columns

| Column Name        | Data Type    | Constraints                  | Description                                    |
|-------------------|--------------|------------------------------|------------------------------------------------|
| id                | INTEGER      | PRIMARY KEY, AUTO INCREMENT  | Unique identifier for the meal plan            |
| household_id      | INTEGER      | NOT NULL, FOREIGN KEY, INDEX | Reference to the household that owns this plan |
| week_start_date   | DATE         | NOT NULL, INDEX              | Monday of the week (always a Monday)           |
| created_by_user_id| INTEGER      | NOT NULL, FOREIGN KEY        | User who created this meal plan                |
| created_at        | DATETIME     | NOT NULL, DEFAULT NOW()      | Timestamp when the record was created          |
| updated_at        | DATETIME     | NOT NULL, DEFAULT NOW()      | Timestamp when the record was last updated     |

#### Constraints

- **Primary Key**: `id`
- **Foreign Keys**:
  - `household_id` → `households.id`
  - `created_by_user_id` → `users.id`
- **Unique Constraint**: `(household_id, week_start_date)` - Ensures only one meal plan per household per week
- **Indexes**:
  - `ix_meal_plans_household_id` on `household_id`
  - `ix_meal_plans_week_start_date` on `week_start_date`

#### Notes

- `week_start_date` must always be a Monday (day 0 of the week)
- The unique constraint prevents duplicate meal plans for the same household and week
- Deleting a meal plan cascades to all associated planned meals

### planned_meals

The `planned_meals` table stores individual meal entries within a meal plan.

#### Columns

| Column Name   | Data Type    | Constraints                  | Description                                           |
|--------------|--------------|------------------------------|-------------------------------------------------------|
| id           | INTEGER      | PRIMARY KEY, AUTO INCREMENT  | Unique identifier for the planned meal                |
| meal_plan_id | INTEGER      | NOT NULL, FOREIGN KEY, INDEX | Reference to the parent meal plan                     |
| recipe_id    | INTEGER      | NOT NULL, FOREIGN KEY        | Reference to the recipe being planned                 |
| day_of_week  | INTEGER      | NOT NULL                     | Day of week: 0=Monday, 1=Tuesday, ..., 6=Sunday       |
| meal_type    | VARCHAR(20)  | NOT NULL                     | Type of meal: breakfast, lunch, dinner, snack, other  |
| servings     | INTEGER      | NULLABLE                     | Number of servings planned (optional)                 |
| notes        | TEXT         | NULLABLE                     | Optional notes for the planned meal                   |
| created_at   | DATETIME     | NOT NULL, DEFAULT NOW()      | Timestamp when the record was created                 |
| updated_at   | DATETIME     | NOT NULL, DEFAULT NOW()      | Timestamp when the record was last updated            |

#### Constraints

- **Primary Key**: `id`
- **Foreign Keys**:
  - `meal_plan_id` → `meal_plans.id` (CASCADE on delete)
  - `recipe_id` → `recipes.id`
- **Indexes**:
  - `ix_planned_meals_meal_plan_id` on `meal_plan_id`
  - `ix_planned_meals_day_meal` on `(meal_plan_id, day_of_week, meal_type)` - Composite index for efficient querying by day and meal type

#### Valid Values

- **day_of_week**: 0-6 (Monday through Sunday)
- **meal_type**: Must be one of:
  - `breakfast`
  - `lunch`
  - `dinner`
  - `snack`
  - `other`

#### Notes

- Multiple recipes can be planned for the same `(meal_plan_id, day_of_week, meal_type)` combination
- When a meal plan is deleted, all associated planned meals are automatically deleted (CASCADE)
- The `servings` field is optional; if not specified, it defaults to the recipe's default servings

## Relationships

### MealPlan Relationships

1. **household** (N:1): Each meal plan belongs to one household
   - Foreign key: `household_id` → `households.id`
   - A household can have many meal plans (one per week)

2. **creator** (N:1): Each meal plan is created by one user
   - Foreign key: `created_by_user_id` → `users.id`
   - A user can create many meal plans

3. **planned_meals** (1:N): Each meal plan can have many planned meals
   - Back-reference from `PlannedMeal.meal_plan_id`
   - Cascade delete: deleting a meal plan removes all its planned meals

### PlannedMeal Relationships

1. **meal_plan** (N:1): Each planned meal belongs to one meal plan
   - Foreign key: `meal_plan_id` → `meal_plans.id`
   - CASCADE delete behavior

2. **recipe** (N:1): Each planned meal references one recipe
   - Foreign key: `recipe_id` → `recipes.id`
   - Many planned meals can reference the same recipe

## Data Access Patterns

### Common Queries

#### Get or Create Meal Plan for Current Week

```python
week_start = get_week_start(date.today())
meal_plan = await db.execute(
    select(MealPlan).where(
        and_(
            MealPlan.household_id == household.id,
            MealPlan.week_start_date == week_start,
        )
    )
)
```

#### List All Meal Plans for Household

```python
meal_plans = await db.execute(
    select(MealPlan)
    .where(MealPlan.household_id == household.id)
    .order_by(MealPlan.week_start_date.desc())
)
```

#### Get All Planned Meals for a Week

```python
planned_meals = await db.execute(
    select(PlannedMeal)
    .where(PlannedMeal.meal_plan_id == meal_plan.id)
    .order_by(PlannedMeal.day_of_week, PlannedMeal.meal_type)
)
```

#### Get Meals for Specific Day and Meal Type

```python
meals = await db.execute(
    select(PlannedMeal).where(
        and_(
            PlannedMeal.meal_plan_id == meal_plan.id,
            PlannedMeal.day_of_week == 0,  # Monday
            PlannedMeal.meal_type == "dinner",
        )
    )
)
```

### Performance Considerations

1. **Composite Index**: The `(meal_plan_id, day_of_week, meal_type)` index optimizes queries for specific meal slots
2. **Week Lookup**: The `week_start_date` index enables fast lookup of meal plans by date
3. **Household Scoping**: The `household_id` index ensures efficient filtering by household

## Business Rules

### Meal Plan Rules

1. **One Plan Per Week**: A household can have only one meal plan per week (enforced by unique constraint)
2. **Week Start on Monday**: All meal plans start on Monday (normalized by `get_week_start()` function)
3. **Household Scoping**: Meal plans are scoped to households; users can only access their household's plans
4. **No Empty Plans**: Empty meal plans (with no planned meals) are allowed and valid

### Planned Meal Rules

1. **Multiple Recipes Allowed**: Multiple recipes can be assigned to the same day and meal type
2. **Recipe Validation**: The recipe must exist and belong to the same household as the meal plan
3. **Soft Delete Handling**: If a recipe is soft-deleted, the planned meal remains but should be handled gracefully in the UI
4. **Cascade Deletion**: Deleting a meal plan automatically deletes all its planned meals

## API Schemas

### Pydantic Models

#### PlannedMealBase

```python
class PlannedMealBase(BaseModel):
    recipe_id: int
    day_of_week: int = Field(..., ge=0, le=6)
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack|other)$")
    servings: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None
```

#### PlannedMeal (Response)

```python
class PlannedMeal(PlannedMealBase):
    id: int
    meal_plan_id: int
    created_at: datetime
    updated_at: datetime
```

#### MealPlan (Response)

```python
class MealPlan(BaseModel):
    id: int
    household_id: int
    week_start_date: date
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    planned_meals: List[PlannedMeal] = []
```

#### MealPlanSummary

```python
class MealPlanSummary(BaseModel):
    id: int
    household_id: int
    week_start_date: date
    created_at: datetime
    meal_count: int = 0
```

## Migration Script

### Alembic Migration

The meal planning tables were created in migration `004_add_meal_planning.py`:

```python
def upgrade():
    # Create meal_plans table
    op.create_table(
        'meal_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('week_start_date', sa.Date(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['household_id'], ['households.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('household_id', 'week_start_date', name='uq_household_week')
    )

    # Create indexes
    op.create_index('ix_meal_plans_household_id', 'meal_plans', ['household_id'])
    op.create_index('ix_meal_plans_week_start_date', 'meal_plans', ['week_start_date'])

    # Create planned_meals table
    op.create_table(
        'planned_meals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meal_plan_id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('meal_type', sa.String(20), nullable=False),
        sa.Column('servings', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['meal_plan_id'], ['meal_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_planned_meals_meal_plan_id', 'planned_meals', ['meal_plan_id'])
    op.create_index('ix_planned_meals_day_meal', 'planned_meals',
                   ['meal_plan_id', 'day_of_week', 'meal_type'])
```

## Security Considerations

### Household Scoping

- All meal plan queries must be scoped to the user's household
- The `get_user_household` dependency ensures users can only access their own household's data
- Cross-household access is prevented at the database query level

### Authorization

- Any household member can view and edit meal plans
- No special permissions required within a household
- Users cannot access meal plans from other households

### Data Validation

- Recipe IDs are validated to ensure they belong to the same household
- Day of week is validated to be 0-6
- Meal type is validated against allowed values
- Servings, if provided, must be >= 1

## Future Enhancements

### Potential Schema Changes

1. **Meal Plan Templates**: Add a `template` flag and `template_name` field
2. **Recurring Plans**: Add fields to support recurring weekly plans
3. **Nutritional Aggregation**: Add computed fields for total calories, macros, etc.
4. **Shopping List Integration**: Add relationship to shopping lists (Feature 17)
5. **Meal Prep Notes**: Add `prep_notes` field for meal prep instructions
6. **Visibility Control**: Add `is_public` flag for sharing meal plans

### Optimization Opportunities

1. **Materialized Views**: Create views for commonly accessed meal plan summaries
2. **Caching**: Cache current week meal plans for better performance
3. **Bulk Operations**: Add endpoints for bulk add/update/delete of planned meals
4. **Denormalization**: Store recipe names in planned_meals for faster display

## Related Documentation

- **API Documentation**: See `API_GUIDE.md` for endpoint details
- **User Guide**: See `MEAL_PLANNING_USER_GUIDE.md` for end-user instructions
- **Feature Requirements**: See `Recipe_Catalog_App_PRD_Next_Features_v2.1.md`, Feature 16

---

**Last Updated**: November 2025
**Version**: 1.0
**Database Version**: Migration 004
