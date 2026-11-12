# Shopping lists: review

Reviewed 2026-11-08 after a user report: "there seems to be no way to access the shopping lists (I can't find a link). When I added a new list I was able to see another list but was not able to edit or delete existing lists."

## What exists today

**Backend** (`backend/app/api/shopping_lists.py`, mounted at `/api/v1/shopping-lists`)

- `GET /categories`: fixed category list (Produce, Dairy, Meat, …).
- `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`, `POST /{id}/archive`, `POST /{id}/duplicate`.
- `POST /{id}/items`, `PATCH /items/{item_id}`, `DELETE /items/{item_id}`.
- `POST /from-recipe`: one item per ingredient line, using the stored `parsedIngredients[].raw` text (quantity and notes stay in the item name). Header lines are skipped. *(Superseded: see "Follow-up changes" below.)*
- `POST /from-meal-plan`: collects `parsedIngredients` (`item`, `quantityMax` or `quantity`, `unit`) from every planned meal and merges them with `consolidate_ingredients` in `app/services/ingredient_parser.py` (it groups on singularized base name and unit and adds up quantities).
- Models: `ShoppingList` (`household_id`, `created_by_user_id`, `status` active/archived) and `ShoppingListItem` (all quantities are strings). There is no `user_id` column.

**Scoping.** Every endpoint, reads and mutations alike, filters on `household_id`. Shopping lists are a shared household resource, so any member can rename, check off, archive or delete any list in the household. This is not the owner-scoped mutation rule that recipes and collections follow. It does mean the API never rejects an edit to another member's list.

**Frontend**

- `src/lib/api/shopping-lists.ts`: one wrapper per endpoint.
- `/shopping-lists`: Active/Archived/All tabs, a card grid where each card links to its list, and a "New List" dialog.
- `/shopping-lists/[id]`: rename and edit description, Duplicate, Archive, Delete, add item, check off, delete item, sort, hide checked.
- Entry points before this change: the meal-plan page ("Generate Shopping List from Meal Plan", "Create Blank Shopping List") and the recipe page's "Shopping List" button. Each one creates a list and opens it. Nothing linked to the index page.

## Reported problems: root causes

1. **No link.** `Navbar.svelte` had no Shopping Lists entry, so users could only reach the index by typing the URL or by going back from a list that had just been created. The navbar has a single layout with no separate mobile menu, so one link covers both.
2. **"Saw another list" but could not edit or delete it.** The other list belongs to the household: a member's list, or one created earlier from a recipe or meal plan, since the index shows every household list. The backend accepts edits and deletes from any member, and the new API test confirms this. The failures came from the frontend:
   - The index cards are links only, with no edit or delete controls. All management happens on the detail page, behind a small "Edit" text link.
   - The detail page loaded the list only in `onMount`. SvelteKit reuses the component when going from one list to another (Duplicate does this), so the old list stayed on screen while Rename, Archive and Delete acted on the new id. The user saw one list and changed another.
   - Clearing the description sent `undefined`, which the PATCH ignores, so the old description came back.
   - Duplicate, Archive, the item rows and the add-item panel used hardcoded `bg-gray-100` and `bg-white` with inherited text color. In the dark theme their labels were close to invisible.

## Fixes made

- `frontend/src/lib/components/Navbar.svelte`: added a "Shopping Lists" link after Meal Plans, using the same `nav-link` and `isActive` pattern.
- `frontend/src/routes/shopping-lists/[id]/+page.svelte`:
  - Reloads on `listId` changes (`$: if (listId) void loadShoppingList()`) instead of only in `onMount`.
  - Sends `description: ""` so a cleared description is saved.
  - Added accessible names: "Edit list", "List name" and "List description".
  - Theme tokens replace the hardcoded colors on the action buttons, item rows, add-item panel and title input.
- Tests:
  - `frontend/src/routes/shopping-lists/[id]/page.test.ts`: rename, reload when the id changes without a remount, and delete after confirmation.
  - `backend/tests/test_shopping_lists.py::test_edit_and_delete_list_via_api`: rename, clear the description, delete, then get a 404.

No owner-gating was added, because the API allows household-wide edits (see recommendation 2).

## Recommendations (priority order)

| # | Recommendation | Rationale | Effort |
|---|---|---|---|
| 1 | **Done.** Add a kebab menu or Rename/Delete buttons to each index card, with the card body as the link | The user looked for management controls on the list view. Today they are one click deeper | S (½ day) |
| 2 | **Done (kept shared).** Decide the sharing rule and write it down: keep household-wide edits (normal for a shared grocery list), or switch to the owner-scoped mutation rule. If it stays shared, add `created_by_user_id` and a creator name to `ShoppingListSummary` and show "Created by X" on cards | The current rule differs from CLAUDE.md's recipe and collection rule without saying so. Showing the creator explains where the "other list" came from | S |
| 3 | **Done** (`tests/test_shopping_list_scoping.py`). Add API tests for cross-household isolation on PATCH, DELETE and item routes, and for a second household member | Current tests use the ORM directly and never call the endpoints for these cases | S |
| 4 | **Dropped:** shopping items deliberately carry no recipe notes since #437. Keep ingredient notes when building a list from a meal plan. `from-meal-plan` builds `{quantity, unit, name}` from `parsedIngredients[].item` and drops `note` (for example "finely chopped" or "for garnish"), and `consolidate_ingredients` has no field for notes. Carry the notes into `ShoppingListItem.notes`, joining the distinct notes when lines merge | This is a known limit. Users lose prep and brand details that the from-recipe path keeps | M (1 day, including consolidation tests) |
| 5 | **Done.** Show `item.unit` and `item.notes` on the detail page (only `quantity` is shown now), and add a unit field to the add-item form | Meal-plan lists store units the UI never displays, so "2 cup flour" reads as "2 flour" | S |
| 6 | **Done.** Check items off optimistically instead of refetching the whole list after each toggle | Every tap costs a round trip, which is slow on a phone in a shop | S |
| 7 | **Done.** Let users add a recipe or meal plan to an existing list as well as creating a new one. `recipes/[id]/+page.svelte` has an unused `shoppingLists` and `showAddToShoppingListDialog` scaffold for this | Shopping for several recipes now produces several lists | M |
| 8 | **Done.** Remove the remaining hardcoded Tailwind grays and blues on both shopping-list pages, and move the index page's create dialog to a native `<dialog>` with focus handling | Theme and accessibility consistency with the rest of the app | S |
| 9 | **Unarchive done** (list page and card); drag-reordering not done. Add an unarchive action (PATCH `status: "active"` already works) and put item drag-reordering on `display_order` | Archived lists cannot be restored from the UI | S |

## Follow-up changes (recommendations 1, 2, 5 and 7)

**Sharing rule (decided).** Shopping lists stay a shared household resource: any member can rename, edit, check off, archive or delete any list in the household. This is a deliberate exception to the owner-scoped mutation rule for recipes and collections, because a grocery list is edited by whoever is shopping. Every endpoint scopes on `household_id`, and a list in another household returns 404 (`SHOPPING_LIST_NOT_FOUND`). Summary and detail responses carry `created_by_user_id` and `created_by_name` (the creator's `display_name`, loaded with a join, so there is no N+1). The UI shows "Created by you" or "Created by <name>".

**Merge on add.** Every add path goes through `add_or_merge_item` in `app/api/shopping_lists.py`: manual add (`POST /{id}/items`), `from-recipe` and `from-meal-plan` (new list or an existing one via `shopping_list_id`), and the single-ingredient button on the recipe page, which uses `POST /{id}/items`. A new item merges into an existing **unchecked** item on the same list when:

- the names have the same `ingredient_key` (the singular, lowercase base name that `consolidate_ingredients` groups on, so "Tomatoes" matches "tomato" and "garlic, minced" matches "garlic"), and
- the normalized units are equal (`normalize_unit`; no unit on both sides counts as equal). Units are never converted, and
- both quantities are numeric (`parse_quantity`: "2", "1/2", "1 1/2", "0.5"; a range counts as its upper bound) and are summed, formatted with `format_quantity` ("6", not "6.0"; "2 1/4"), or both quantities are blank.

Otherwise a separate item is added: different units, one quantity blank and the other not, or a non-numeric quantity such as "a pinch". Distinct notes are joined with "; ", and the existing item's name is kept. Checked items are never merged into. Editing an item's quantity or unit (inline on the detail page, through `PATCH /items/{id}`) does not merge.

**Other changes.**

- Index cards: the card body is a link; Rename (inline) and Delete (confirmed through the `dialog` store) sit outside it and are labelled with the list name.
- Detail page: shows the unit ("2 cups flour"; units are stored singular and pluralized for display) and notes, adds a unit field to the add-item form, and lets you edit a quantity and unit inline.
- `from-recipe` builds structured items from `parsedIngredients` (`quantityMax` or `quantity`, `unit`, `item`, with `note` in `notes`). Lines the parser could not handle keep their raw text as the name.
- `from-recipe` and `from-meal-plan` accept an optional `shopping_list_id` to add to an existing household list.
- The recipe page and the meal-plan page share `AddToShoppingListDialog.svelte`, which lists active lists (plus "New list" where that makes sense). Each recipe ingredient line other than headers has an "Add … to shopping list" button. The list used last is remembered in `sessionStorage`, so later adds take one click and are confirmed with a toast.
