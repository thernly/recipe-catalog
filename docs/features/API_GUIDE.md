# Recipe Catalog API Client Guide

How external clients import recipes in [schema.org/Recipe](https://schema.org/Recipe)
format. Two routes exist:

- **`POST /api/v1/intake`** — one recipe, authenticated with a personal API token. Use
  this for browser extensions and scripts.
- **`POST /api/v1/import/recipes/json`** — a batch, authenticated with a logged-in
  cookie session plus CSRF header.

Base URL: `http://localhost:8000` in development, or your deployed origin. Interactive
OpenAPI docs are served at `/docs`.

---

## Personal API tokens and intake

### Creating a token

Tokens are managed from a normal (cookie) session at `/api/v1/users/me/api-tokens`:

| Method | Path | Result |
|---|---|---|
| `GET` | `/api/v1/users/me/api-tokens` | Active tokens (never includes the token value) |
| `POST` | `/api/v1/users/me/api-tokens` | `201`, body `{"name": "..."}`; the response's `token` field is the only time the plain value is shown |
| `DELETE` | `/api/v1/users/me/api-tokens/{id}` | `204`; the token stops working immediately |

Tokens start with `rcat_`, are stored as SHA-256 hashes, do not expire, and are
revocable. They authenticate **only** the intake routes; every other endpoint rejects
them.

### Using a token

Send `Authorization: Bearer rcat_...`. Intake requests carrying such a token skip the
CSRF check; no cookies are needed.

**`GET /api/v1/intake/check`** — returns `200 {"success": true, "message": "Token is valid"}`,
or `401` for an invalid or revoked token.

**`POST /api/v1/intake`** — body is a single schema.org Recipe object. Query param
`on_duplicate` is `skip` (default) or `update`; a duplicate is an existing,
non-deleted recipe you own with the same name.

```bash
curl -X POST "http://localhost:8000/api/v1/intake?on_duplicate=skip" \
  -H "Authorization: Bearer rcat_..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Recipe", "recipeIngredient": ["1 cup flour"], "recipeInstructions": ["Mix and bake"]}'
```

Response (`200`):

```json
{
  "success": true,
  "status": "created",
  "id": 42,
  "message": "Recipe imported",
  "url": "https://your-frontend/recipes/42"
}
```

`status` is `created`, `updated`, or `skipped` (`id` is then the existing recipe). A
recipe that cannot be converted returns `400 INVALID_INPUT` and nothing is saved.
Rate limit: `RATE_LIMIT_PER_HOUR` (default 1000) per IP.

---

## Batch import (cookie session)

### Logging in

`POST /api/v1/auth/login` with `{"email": "...", "password": "..."}` returns
`{"message": "Login successful", "csrf_token": "..."}` and sets cookies:

| Cookie | Readable by JS | Lifetime |
|---|---|---|
| `access_token` | No (httpOnly) | 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`) |
| `refresh_token` | No (httpOnly) | 30 days (`REFRESH_TOKEN_EXPIRE_DAYS`) |
| `csrf_token` | Yes | 30 days |

No token is returned in the body. Send the cookies on every request and echo the CSRF
token in `X-CSRF-Token` on POST/PUT/PATCH/DELETE; omitting it returns
`403 csrf_token_invalid`. When the access token expires (401), call
`POST /api/v1/auth/refresh` and retry once.

### `POST /api/v1/import/recipes/json`

- **Body**: a bare JSON **array** of schema.org Recipe objects (max 500).
- **Query params**:
  - `duplicate_handling`: `skip` (default) skips a recipe whose name matches one you
    own; `update` overwrites it; `create` always inserts.
  - `collection_id` (optional): add imported recipes to this collection. It must be a
    collection you own, otherwise `404`.
- **Rate limit**: 20,000/hour per IP.

New recipes are owned by you and shared with your household.

```bash
CSRF=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -c cookies.txt -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}' | jq -r '.csrf_token')

curl -X POST "http://localhost:8000/api/v1/import/recipes/json?duplicate_handling=skip&collection_id=1" \
  -b cookies.txt \
  -H "X-CSRF-Token: $CSRF" \
  -H "Content-Type: application/json" \
  -d '[{"name": "Test Recipe", "recipeIngredient": ["1 cup flour", "2 eggs"], "recipeInstructions": ["Mix", "Bake"]}]'
```

```python
import requests

s = requests.Session()  # holds the auth cookies
csrf = s.post(f"{base}/api/v1/auth/login",
              json={"email": email, "password": password}).json()["csrf_token"]
r = s.post(
    f"{base}/api/v1/import/recipes/json",
    params={"duplicate_handling": "skip", "collection_id": 1},
    headers={"X-CSRF-Token": csrf},
    json=recipes,  # a list of recipe dicts
)
```

Response (`200`, also for partial failure):

```json
{
  "success": true,
  "message": "Imported 2 new recipes, updated 0, skipped 1, failed 1",
  "details": {
    "total": 4,
    "created": 2,
    "updated": 0,
    "skipped": 1,
    "failed": 1,
    "errors": [{"index": 3, "name": "Bad Recipe", "error": "..."}],
    "items": [{"index": 0, "status": "created", "recipe_id": 42}]
  }
}
```

`items` has one entry per recipe that did not fail. A file-upload variant,
`POST /api/v1/import/recipes` (multipart `file`, with `duplicate_handling` and
`collection_id` as form fields), accepts a single object or an array.

---

## Errors

Errors use one envelope:

```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Collection not found",
  "details": {},
  "correlation_id": "..."
}
```

`error_code` is uppercase (`UNAUTHORIZED`, `INVALID_INPUT`, `VALIDATION_ERROR`,
`RESOURCE_NOT_FOUND`, `INTERNAL_ERROR`, ...); see `ErrorCode` in
`backend/app/core/exceptions.py`. Two exceptions: the CSRF failure uses
`csrf_token_invalid`, and rate limiting (`429`) returns slowapi's
`{"error": "Rate limit exceeded: ..."}`. Read `message`, not `detail`.

---

## Recipe format

Only `name` is required. Commonly used fields: `description`, `image` (URL string,
array of URLs, or `{url, data, mimeType}` objects), `author`, `recipeYield`,
`prepTime`/`cookTime`/`totalTime` (ISO 8601 durations, e.g. `PT1H30M`),
`recipeCategory`, `recipeCuisine`, `recipeIngredient` (array of strings),
`recipeInstructions` (string, array of strings, or `HowToStep` objects), `keywords`,
`nutrition`, `url`.

Conversion notes (`convert_from_schema_org`):

- `name` must be a string; HTML tags are stripped and it is truncated to 500 chars.
- `image`: at most 5 kept, http(s) URLs only. URLs without inline `data` are fetched
  server-side and stored as base64; a failed fetch keeps the URL with empty data.
  Inline `data` with a disallowed `mimeType` or over the size cap is dropped.
- `url` is kept only if it is http(s). Bad optional fields are dropped, not fatal.
- `recipeCategory`/`recipeCuisine`: the first value (truncated to 100 chars) feeds the
  search filter columns; the full value is stored.
- `author`, `recipeInstructions`, `nutrition`, and the other fields are stored as sent.

Every import runs the same cleanup as other write paths (yield and time
normalization, ingredient parsing). Source: `backend/app/api/import_recipes.py`,
`backend/app/api/intake.py`, `backend/app/utils/recipe_format.py`.
