# Recipe Intake Autopilot — session handoff (2026-10-05)

A short status note for picking the work up again. The design and the full work order
are in [`recipe-intake-autopilot.md`](recipe-intake-autopilot.md) (§7.1); read that first.

## Where things stand

| Step | State | Where |
|---|---|---|
| C1: safe fetch, API tokens, intake routes, CSRF skip | merged | catalog #362 |
| C2: siphon on the new routes | merged | siphon #99 (+ #100–103: update by default, option to turn off) |
| L1a / L1b: end to end against the real deployment | passed | owner saved and updated recipes through the siphon |
| Docs catch-up | merged | catalog #366 (first commit), siphon #104 |
| C3: shared cleanup, `parsedIngredients`, eval harness, backfill | merged | catalog #366 |
| Eval fix: read the complete-backup export | merged | catalog #367 |
| **L2: build the eval set, run the harness, backfill dry run** | **in progress (owner)** | see below |

Decisions made since the design doc was written are recorded in it: the importer's own
recipe with the same name follows `on_duplicate` (overwrite by default; the siphon
checkbox switches to skip) and is not a review flag (§4.8, §12).

## L2: where the owner is

- The complete backup (`complete_backup_<date>.json` from the Export page) is in
  `backend/eval-data/inputs/`, and `uv run python scripts/intake_eval.py draft` has
  written about **1400 cases** to `backend/eval-data/cases/`. None are checked yet.
- Hand-checking 1400 cases is not realistic. The approach:
  1. **Sample (built).** `draft --sample 40 [--seed S]` drafts a repeatable random set
     of about 40 recipes (~400 lines), enough to measure line accuracy within a few
     percent. To switch, delete the unchecked full set (`rm -r eval-data/cases`) and
     re-draft with `--sample 40`.
  2. **Originals (built).** `originals` writes each case's source record to
     `eval-data/originals/<case name>.json`, image data omitted, for side-by-side
     comparison.
  3. **Flag suspicious lines** in each drafted case (unparsed, notes, ranges, unusual
     units), so the owner skims the flagged lines instead of every line. Not built;
     proposed.
  4. **Model-assisted labelling, done locally.** A local Claude Code session (the recipes
     must not leave the owner's machine) fills in `expected` for the sampled cases and
     marks what it is unsure of; the owner audits and sets `"checked": true`.
  5. **Coverage over all 1400 now:** the backfill dry run already lists every line the
     parser could not handle, with no hand-checking. C3b can start from that list.
- Still to run: `uv run python scripts/backfill_cleanup.py` (dry run, writes
  `backfill-report-<timestamp>.md`). **Do not `--apply`** until the parser is agreed
  good enough (that is L2b).

## Next session: what to do

1. Ask the owner for: the `intake_eval.py run` output (if any cases are checked), the
   backfill report's summary and its "Lines that did not parse" section, and whether
   to build line flagging (item 3 above).
2. If yes, build it on the catalog (small PR: `app/services/intake_eval.py`,
   `scripts/intake_eval.py`, `tests/test_intake_eval.py`).
3. Then **C3b**: parser fixes in `app/services/ingredient_parser.py` driven by the
   unparsed lines and mismatches the owner pastes. Add each new pattern as a case in
   `tests/test_ingredient_parser.py`. Never paste the owner's real recipe text into the
   repo; write equivalent made-up lines.
4. After C3b and L2b (owner re-runs the harness, then backs up and applies the
   backfill): C4, C5 and C6 run back to back in the cloud (§7.1).

## Parser conventions to keep (or change deliberately in C3b)

- Units are canonical and singular whatever the quantity: `cup`, `tablespoon`,
  `teaspoon`, `gram`, `ounce`. Owner confirmed (2026-10-05); display pluralizes.
- Alternative measures ("2 sticks/1 cup (226 grams) butter") keep the first measure as
  quantity and unit; the others go to `note`.
- Size words stay in the item: "3 large eggs" gives `item: "large eggs"`.
- Notes come from parentheses, the text after the first comma, and a trailing
  "to taste" / "optional" / "for garnish"; several are joined with `"; "`.
- Ranges: "1-2" gives `quantity: 1, quantityMax: 2`.
- Group headers ("For the dressing:", "FILLING", "--- Sauce ---") produce
  `{"raw", "header": true, "group", "parsedBy"}` with no ingredient fields, and set
  `group` on the lines after them. Owner confirmed this shape (2026-10-05).
- Times stay ISO 8601 (`PT1H15M`) in the data; the app displays them readably. Owner
  confirmed (2026-10-05).
- Doubtful lines get `parsedBy: null` (numbers left in the item, "plus", unbalanced
  parentheses, sentence-length lines). These are the lines C6 will send to a model.
- On save, unchanged lines keep stored **model** parses; regex entries are recomputed.

## Practical notes

- Run every backend script from `backend/` (`cd backend` first): `intake_eval.py` looks
  for `eval-data/` there, and `backfill_cleanup.py` reads `backend/.env`.
- `backend/eval-data/` and `backfill-report-*.md` are git-ignored; real recipes stay out
  of git.
- Stop the app before `backfill_cleanup.py --apply`: an edit made between planning and
  writing would be overwritten. Apply makes `recipes.db.bak-<timestamp>` first.
- Cloud sessions see only GitHub. The siphon repo is attached on request
  (`thernly/recipe-siphon`); the eval data and the real database are only on the
  owner's machine.
- Separate known bug, not part of this work: saving a recipe from the edit form drops
  `images`, `nutrition`, `author` and other fields the form does not show, because the
  form sends a fresh `recipe_data` that replaces the stored one. Queued as its own task.
