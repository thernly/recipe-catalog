# Meal Planning Data Model

Weekly meal planning uses two tables, `meal_plans` and `planned_meals`. Code: `backend/app/models/meal_plan.py`, `backend/app/schemas/meal_plan.py`, `backend/app/api/meal_plans.py`.

```
Household ──1:N── MealPlan ──1:N── PlannedMeal ──N:1── Recipe
User ─────1:N──┘ (creator)         └──N:1── User (creator, nullable)
```

## Tables

### meal_plans

| Column             | Type     | Constraints                                         |
|--------------------|----------|-----------------------------------------------------|
| id                 | INTEGER  | PK                                                  |
| household_id       | INTEGER  | NOT NULL, FK `households.id` ON DELETE CASCADE, indexed |
| week_start_date    | DATE     | NOT NULL, indexed; always a Monday                  |
| created_by_user_id | INTEGER  | NOT NULL, FK `users.id` ON DELETE CASCADE           |
| created_at         | DATETIME | NOT NULL                                            |
| updated_at         | DATETIME | NOT NULL                                            |

Unique constraint `uq_household_week` on `(household_id, week_start_date)`: one plan per household per week.

### planned_meals

| Column             | Type        | Constraints                                          |
|--------------------|-------------|------------------------------------------------------|
| id                 | INTEGER     | PK                                                   |
| meal_plan_id       | INTEGER     | NOT NULL, FK `meal_plans.id` ON DELETE CASCADE, indexed |
| recipe_id          | INTEGER     | NOT NULL, FK `recipes.id` ON DELETE CASCADE          |
| created_by_user_id | INTEGER     | NULL, FK `users.id` ON DELETE SET NULL               |
| day_of_week        | INTEGER     | NOT NULL; 0=Monday … 6=Sunday                        |
| meal_type          | VARCHAR(20) | NOT NULL; breakfast, lunch, dinner, snack, other     |
| servings           | INTEGER     | NULL                                                 |
| notes              | TEXT        | NULL                                                 |
| created_at         | DATETIME    | NOT NULL                                             |
| updated_at         | DATETIME    | NOT NULL                                             |

Composite index `ix_planned_meals_day_meal` on `(meal_plan_id, day_of_week, meal_type)`. Several recipes may share the same day and meal type.

Deleting a meal plan deletes its planned meals (FK cascade plus ORM `delete-orphan`). Hard-deleting a recipe deletes planned meals that reference it; soft-deleting does not.

## Migrations

- `004_add_meal_planning.py` — created both tables.
- `20261107_household_integrity.py` — added `planned_meals.created_by_user_id` (backfilled from the plan creator when they are a household member), rebuilt foreign keys to the `ondelete` rules above, and repaired plans whose creator was in a different household (moved or merged into the creator's household plan for that week).

## Access rules

- Every read and write is scoped by household (`Depends(get_user_household)`, `MealPlan.household_id == household.id`). Any household member can view, add, edit and delete plans and meals.
- `GET /current` gets or creates the plan for the current week, computed in the user's preferred timezone; a supplied date is normalized to its Monday.
- Adding or changing a planned meal requires the recipe to be non-deleted and in the same household.
- Reads outer-join recipes filtered to `deleted_at IS NULL` and the same household, so a planned meal whose recipe was soft-deleted is still returned with `recipe_name: null`. Summary `meal_count` likewise counts only meals with a live recipe.

## API Schemas

```python
class PlannedMealBase(BaseModel):
    recipe_id: int
    day_of_week: int = Field(..., ge=0, le=6)
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack|other)$")
    servings: int | None = Field(None, ge=1)
    notes: str | None = Field(None, max_length=10000)  # sanitize_html on create/update

class PlannedMeal(PlannedMealBase):  # response
    id: int
    meal_plan_id: int
    recipe_name: str | None = None
    created_at: datetime
    updated_at: datetime

class MealPlan(BaseModel):  # response
    id: int
    household_id: int
    week_start_date: date
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    planned_meals: list[PlannedMeal] = []

class MealPlanSummary(BaseModel):
    id: int
    household_id: int
    week_start_date: date
    created_at: datetime
    meal_count: int = 0
```

`PlannedMealUpdate` makes every field optional.

## Related

- Shopping lists: `POST /api/v1/shopping-lists/from-meal-plan` builds a list from a plan's meals (`backend/app/api/shopping_lists.py`).
- AI menu generation can apply catalog-first suggestions to the current week's plan; see `AI_RECIPE_GENERATION.md`.
- Original requirements: `docs/requirements/old/Recipe_Catalog_App_PRD_Next_Features_v2.1.md`, Feature 16.
