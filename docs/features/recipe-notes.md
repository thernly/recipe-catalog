# Recipe notes — plan

Household members leave dated notes on a recipe from their experience cooking it
("used half the sugar, still sweet enough"). A recipe can have many notes; each shows
who wrote it and when. Notes survive recipe edits and re-imports.

## Decisions (owner, 2026-11-14)

1. **Who adds:** any household member who can see the recipe.
2. **Edit / delete:** only the note's author edits it; the author *or* the recipe's owner
   can delete it.
3. **Author name shown:** the user's `display_name`, else the part of their email before
   `@`. Looked up live, so a rename updates old notes. (Imported notes are the exception —
   see 6.)
4. **Existing "Notes & Tips"** (`recipe_data.notes`) stays as it is: recipe content from
   the source/AI. The new feature is a separate "Cooking notes" section. No data migration.
5. **Export:** notes are included in every export format (JSON, Markdown, text, PDF; single
   and bulk).
6. **Import:** notes in an imported JSON file are restored as notes, keeping the original
   author name and timestamp.
7. **Import duplicates:** notes follow the recipe's duplicate choice. New or updated
   recipe → add the file's notes, skipping ones already present (same author name +
   timestamp + text). Skipped recipe → untouched.

## Why a separate table

`recipe_data` is replaced wholesale on edit (`app/api/recipes/crud.py`) and on "update"
re-import (`app/api/import_recipes.py:183`). Notes in their own table are never touched
by those paths, which is how requirement "retained if the recipe is updated" is met
without any special-case code.

## Data model

New `RecipeNote` model in `app/models/recipe_note.py` (new module → `Mapped[...]` /
`mapped_column`, fully mypy-checked; export it from `app/models/__init__.py`):

| column        | type                         | notes                                           |
|---------------|------------------------------|-------------------------------------------------|
| `id`          | int PK                       |                                                 |
| `recipe_id`   | FK `recipes.id`, indexed     | `ondelete="CASCADE"`                            |
| `user_id`     | FK `users.id`, indexed       | the account that added it (or imported it)      |
| `author_name` | `String(100)`, nullable      | set only for imported notes; overrides lookup   |
| `text`        | `Text`, max 10 000 chars     | plain text, sanitized like meal-plan notes      |
| `created_at`  | `DateTime`, `utc_now`        | original timestamp for imported notes           |
| `updated_at`  | `DateTime`, nullable         | set when edited; UI shows "edited"              |

Relationships: `Recipe.notes` (`cascade="all, delete-orphan"`, ordered by `created_at`)
and `RecipeNote.user`. Soft-deleting a recipe leaves its notes; restoring brings them back;
a manual purge deletes them via the cascade. Deleting an account deletes that user's
notes too (`User.recipe_notes` cascade), matching how account deletion removes the
user's other content. *(Assumption made during PR 1 — owner to confirm.)*

Migration: `alembic revision --autogenerate -m "add recipe notes"` on top of
`20261107_solo_households_personal`; review it and test up + down.

## API

New `app/api/recipes/notes.py`, included in `app/api/recipes/__init__.py` (before
`crud_router`). All under `/api/v1/recipes/{recipe_id}/notes`.

| method   | path               | access                                                        |
|----------|--------------------|---------------------------------------------------------------|
| `GET`    | `/notes`           | recipe in caller's household, not deleted. Newest first.      |
| `POST`   | `/notes`           | same as GET → note authored by caller                         |
| `PATCH`  | `/notes/{note_id}` | note's `user_id == current_user.id`, else 403                 |
| `DELETE` | `/notes/{note_id}` | note author **or** `recipe.user_id == current_user.id`        |

This is a deliberate exception to "mutations scope by owner": adding a note is a
household-level action, while editing and deleting are checked against the note's
author and the recipe's owner. Every endpoint first loads the recipe with the
household-scoped query from `app/api/recipes/search.py`, so a note on another
household's recipe returns 404, not 403.

Response schema (`app/schemas/recipe_note.py`):
`{id, recipe_id, text, author_name, is_author, created_at, updated_at}`. `author_name` is
`note.author_name or user.display_name or email.split("@")[0]`. Email is never returned.
`is_author` lets the UI show the edit button; the delete button is shown when
`is_author` or the caller owns the recipe (already known on the recipe page).

## Export

All export paths go through `convert_to_schema_org` (`app/utils/recipe_format.py:31`).
Add schema.org's standard `comment` property (Recipe inherits it from CreativeWork):

```json
"comment": [{"@type": "Comment", "text": "…", "dateCreated": "2026-11-14T18:02:00Z",
             "author": {"@type": "Person", "name": "sam"}}]
```

Then render a "Cooking notes" section (author · date — text) in:
`app/services/recipe_export.py` (markdown, text), `app/utils/pdf_export.py`, and the
duplicated markdown/text formatters in `app/api/export.py`. Add `notes` to the
`export_all_data` backup too.

Async SQLAlchemy can't lazy-load, so every query feeding the converter needs
`selectinload(Recipe.notes).selectinload(RecipeNote.user)`:
`app/api/recipes/export.py:52`, `app/api/export.py` (recipes, collections, all),
and the PDF bulk path.

## Import

In `convert_from_schema_org`, read `comment` into a validated list
(`text` required and non-empty, ≤ 10 000 chars, sanitized; `author.name` → ≤ 100 chars,
default "Unknown"; `dateCreated` parsed, else import time; bad entries dropped, never
fatal; cap at 500 per recipe). Return it alongside `recipe_data`, **not inside it**.

In `_import_recipes_internal`, for created and "update" recipes only, add a `RecipeNote`
per entry with `user_id` = importing user, `author_name` and `created_at` from the
file, skipping entries whose (author name, timestamp, text) matches a note already on
the recipe. Skipped recipes get nothing. Intake (`/api/v1/intake`) is out of scope.

## Frontend

- `src/lib/api/recipe-notes.ts`: `listNotes`, `addNote`, `updateNote`, `deleteNote` via
  `apiRequest`; `RecipeNote` type.
- `src/lib/components/RecipeNotes.svelte`: list (newest first, `{#each}` keyed by
  `note.id`), add form (textarea + button), inline edit for own notes, delete via the
  `dialog` store, errors and success via the `toast` store. Timestamps with
  `toLocaleString()`. Theme variables only. Check garden-fresh, dark and high-contrast.
- Mount it on `src/routes/recipes/[id]/+page.svelte` below the existing "Notes & Tips"
  block. Not shown on the edit page; editing the recipe never sends notes.

## Tests

Backend (`tests/test_recipe_notes.py`, plus additions to export/import tests):
- household member can add/list; other household → 404
- only author can PATCH; author and recipe owner can DELETE; other member → 403
- **notes survive `PATCH /recipes/{id}`** and an "update" re-import
- author name fallback (display_name → email prefix); email not in response
- soft-delete hides recipe, restore shows notes again; cascade on hard delete
- each export format contains the notes; JSON uses `comment`
- import round-trip restores notes with original author/date; re-import doesn't
  duplicate; "skip" adds none; malformed comments dropped without failing the recipe
- migration up/down (`tests/test_migrations.py` pattern)

Frontend: `RecipeNotes.test.ts` covers rendering, add, the edit button shown only for
`is_author`, and delete going through the dialog.

## Delivery — three PRs (~400 lines each)

1. **Backend notes:** model, migration, schemas, API, tests, `docs/features/API_GUIDE.md`.
2. **Frontend notes:** API module, component, recipe-page wiring, tests.
3. **Export + import:** `comment` in converter, all export renderers, eager loads,
   import restore + dedupe, tests.

## Not in scope

Notes on recipe cards/search, notifications, rich text/markdown in notes, notes via the
intake API, per-note privacy.
