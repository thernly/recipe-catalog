# AI Recipe and Menu Generation

AI features use the OpenRouter API. Two modes:

- **Recipe generation** (`/ai-generate` page) — enter ingredients plus optional cuisine, time limit, dietary preferences and equipment; review and edit the generated schema.org recipe, then save it.
- **Menu generation** (`/ai-menu` page) — suggest meals for 1–14 days across chosen meal types. The default **catalog-first** mode picks from the household's own non-deleted recipes and can apply the suggestions to the current week's meal plan; **ai-only** mode suggests new dishes.

Both require authentication and show food-safety disclaimers.

## Setup

1. Create an API key at [OpenRouter](https://openrouter.ai/).
2. Add to `backend/.env`:

```bash
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet   # default in config.py
AI_RATE_LIMIT_PER_HOUR=50                      # default
```

Any [OpenRouter model](https://openrouter.ai/models) id works for `OPENROUTER_MODEL`.

## API

### `POST /api/v1/ai/generate-recipe`

```json
{
  "ingredients": ["chicken breast", "bell peppers", "onion", "rice"],
  "cuisine": "Asian",
  "time_limit": 45,
  "dietary_preferences": ["gluten-free"],
  "equipment": ["Stovetop", "Rice cooker"]
}
```

Response: `{"recipe": {...schema.org Recipe fields...}, "source_type": "ai-generated"}`. The recipe uses camelCase schema.org fields (`recipeIngredient`, `recipeInstructions`, ISO 8601 `prepTime`/`cookTime`/`totalTime`, `recipeYield`, …). Nothing is saved until the user saves it through the normal recipe create path.

### `POST /api/v1/ai/generate-menu`

```json
{
  "days": 7,
  "meals_per_day": ["breakfast", "dinner"],
  "dietary_preferences": ["vegetarian"],
  "cuisine": "Italian",
  "mode": "catalog-first",
  "household_recipe_ids": [1, 2, 3]
}
```

`days` is 1–14, `meals_per_day` at most 4 entries, `mode` is `catalog-first` (default) or `ai-only`. In catalog-first mode the backend sends the household's recipes (optionally narrowed to `household_recipe_ids`, capped at `MAX_RECIPES_IN_PROMPT`) to the model, and any returned `recipe_id` not in that set is nulled.

Response: `{"suggestions": [{"day", "meal_type", "recipe_id", "recipe_name", "description", "prep_time", "cook_time"}], "mode": "..."}`.

### Rate limiting

Both endpoints are limited to `AI_RATE_LIMIT_PER_HOUR` requests per hour **per client IP** (slowapi `get_remote_address`), not per user. Exceeding it returns 429.

## Code

- `backend/app/api/ai.py` — endpoints, rate limits, catalog lookup
- `backend/app/services/ai.py` — OpenRouter client, prompts, response parsing
- `backend/app/schemas/ai.py` — request/response schemas
- `frontend/src/routes/ai-generate/+page.svelte`, `frontend/src/routes/ai-menu/+page.svelte`
- `frontend/src/lib/api/ai.ts`

## Troubleshooting

AI failures raise `AIServiceError` and return 503 with the standard envelope:

```json
{"error_code": "AI_SERVICE_ERROR", "message": "...", "details": ..., "correlation_id": "..."}
```

Common `message` values:

- **"AI service is not configured."** — `OPENROUTER_API_KEY` is unset; set it and restart.
- **"AI service timed out…" / "Could not connect to the AI service…"** — check OpenRouter status and network.
- **"AI returned invalid JSON…" / "AI returned an invalid recipe/menu…"** — the model's output didn't parse; retry or try a different model.

Search backend logs by the `correlation_id` for the classified provider error. Also check the key is valid and the OpenRouter account has credits.

## Privacy and cost

Ingredient lists, preferences and (in catalog-first mode) recipe names and categories are sent to OpenRouter; its privacy policy applies. OpenRouter bills per token; monitor usage in its dashboard.
