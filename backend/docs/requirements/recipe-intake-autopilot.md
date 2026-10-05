# Recipe Intake Autopilot — Design v0.3

Get recipes into the **Recipe Catalog** cleanly: direct from the **Recipe Siphon** browser extension, with messy fields normalized, ingredients parsed, and doubtful imports held for review.

> **Status (2026-10-04):** design settled over four question rounds with the owner, after reading both repos. Earlier drafts are kept beside this file as `recipe-intake-autopilot.v0.1.md` and `.v0.2.md`. Building happens in a separate session inside the two repos; this doc is the handoff.
>
> **Progress (2026-10-04):** Phase 0 is done. C1 is merged in the catalog (safe fetch, API tokens, intake and token-check routes, CSRF skip; `recipe-catalog` PR 362), and C2 in the siphon (`recipe-siphon` PR 99). L1a and L1b passed: the owner saved and updated recipes in the deployed catalog through the siphon, which exercised the token, the CSRF skip and the reverse proxy. After C1 and C2, intake gained `?on_duplicate=update` (catalog) and the siphon sends it by default, with an options checkbox to turn it off (siphon PRs 100–103). Next: C3.
>
> **Current status and next steps:** [`recipe-intake-handoff.md`](recipe-intake-handoff.md).
>
> Repos: `github.com/thernly/recipe-catalog`, `github.com/thernly/recipe-siphon`.

## 1. Problem

In priority order:

- **(a) Messy fields.** Recipes the siphon does extract arrive with defects such as `"recipeYield": "6 6 servings"`, inconsistent times, and notes jammed into ingredient lines.
- **(b) Pages the siphon fails on.** Twelve known URLs are listed in the siphon's `docs/not-parsing-correctly.txt`.
- **(c) New source types.** Cookbook photos, YouTube videos. Design deferred (§10).
- **(d) Better shopping lists** from properly parsed ingredients. Later.

Underneath all of them: today a recipe is downloaded from the siphon as JSON and uploaded to the catalog by hand. Direct, authenticated import does not work yet.

## 2. Current state (from the code)

**Catalog** (FastAPI, SvelteKit, SQLite, Alembic)
- Multi-user: households, OAuth, cookie auth with a bearer-header fallback, CSRF, rate limiting. Tables carry `user_id` and `household_id`; reads scope by household, writes by owner.
- Recipe content is one `recipe_data` JSON column in schema.org camelCase, deliberately, so import and export round-trip. `name`, `cuisine`, `category`, `total_time_minutes` are denormalized columns.
- Images are base64 inside `recipe_data.images`; `image_url` holds the original URL.
- Import: `POST /api/v1/import/recipes` (file) and `/api/v1/import/recipes/json` (list). Synchronous. Duplicates are matched by exact name per user with `skip | update | create`.
- `utils/recipe_format.py` parses ISO-8601 and prose durations to minutes, and contains `_fetch_and_encode_image`, which fetches any image URL in imported JSON with no address checks, no size cap, and a blocking client inside async handlers.
- `api/shopping_lists.py` holds a regex ingredient parser (`parse_quantity`, `parse_ingredient_string`, `normalize_unit`, `consolidate_ingredients`).
- `services/ai.py` calls OpenRouter with raw `httpx`: one model setting (`OPENROUTER_MODEL`, default `anthropic/claude-3.5-sonnet`), no `max_tokens`, no structured output. `AI_RATE_LIMIT_PER_HOUR` is 50.
- Frontend has `RecipeForm.svelte`, an `/import` page and a `/settings` page.
- Runs on Proxmox, served over HTTPS, reachable only inside the LAN. The docs describe a Cloudflare Workers + D1 deployment, but the repo has no Workers config or D1 driver for the backend.

**Siphon** (browser extension, no external dependencies)
- Extracts via JSON-LD, Microdata, RDFa, then a heuristic HTML fallback (`extractors/html-fallback.js`, `divider-sections.js`).
- Posts one recipe to `/api/v1/intake` with a bearer token and checks the token at `/api/v1/intake/check` (changed from `/api/recipes/import` and `/api/auth/validate`, which the catalog never had). The catalog now serves both routes and has API tokens.
- Its policy allows HTTPS connections only (satisfied by the LAN setup).
- `docs/API_INTEGRATION.md` specifies the request and response shapes it expects (`created | updated | skipped | needs_review`).
- Re-sending a recipe updates the existing one by default (`?on_duplicate=update`); the "Update recipes that already exist" option turns that off, and the catalog then skips the duplicate.
- Sends `equipment` and `notes`, the keys the catalog reads (§11).

## 3. Goals, non-goals, targets

**Goals**
- Direct, token-authenticated import from the siphon.
- One place in the catalog that normalizes every recipe, whatever path it arrived by.
- Parsed ingredients stored beside the original lines, never replacing them.
- Doubtful imports wait in a review inbox, outside the catalog, until their importer approves them.
- Model use is narrow, validated, and capped in cost.

**Non-goals for this project**
- Photos, YouTube, phone import, server-side page fetching (§10).
- Changing how recipes or images are stored.
- Tagging, dietary suggestions, fuzzy duplicate matching, scaling, "what can I make."
- Porting the backend to Cloudflare.

**Targets**, measured on the eval set (§8)
- 95% of ingredient lines parse correctly.
- 90% of siphon imports save with no edits needed.

## 4. Design

### 4.1 Flow

```
Siphon ──(bearer token)──► POST /api/v1/intake ─┐
Paste-text form ───────────────────────────────►├─► job row written (original payload)
                                                │
File upload (/import) ─► cleanup + regex only ──┼──────────────────────────────► save directly
Recipe create / edit ──► cleanup + regex only ──┘
                                                │
                                                ▼
                         deterministic cleanup: yield, times
                         regex ingredient parser
                                                │
                              lines the regex cannot handle ─► model (phase 3)
                              page text or pasted text ──────► model extraction (phase 4)
                                                │
                                                ▼
                                   validation + review triggers
                                                │
                              ┌─────────────────┴──────────────────┐
                          no flags                              any flag
                              │                                    │
                              ▼                                    ▼
                        recipes table                 draft on the job row (Imports page)
```

Everything runs inside the request. The siphon already allows 30 seconds.

### 4.2 Authentication

- **Personal API tokens**, created in account settings, shown once, stored hashed (reuse `hash_token`). Each has a label and can be revoked. No expiry. One per browser per person.
- Scope: the intake route and a token-check route. Nothing else.
- **Where secrets live.** Neither secret belongs in a repo.

  | Secret | Catalog side | Client side |
  |---|---|---|
  | Personal API token | Only its hash, in a database table | Pasted into the siphon's options page, kept in the browser's extension storage |
  | OpenRouter key | `backend/.env` on the container (already git-ignored; `OPENROUTER_API_KEY` in `.env.example`) | Never leaves the server |

  For the L1a test, the token is passed to the local session as an environment variable and revoked afterwards. Cloud sessions need neither secret, since the model is mocked.
- **CSRF:** the middleware currently rejects every POST lacking the CSRF cookie and header, bearer-authenticated or not. Requests authenticated by token must skip the check. Do not exempt the intake path outright: the paste-text form reaches it with cookies and still needs CSRF protection.

### 4.3 Intake endpoint

The routes are pinned here so the catalog (C1) and siphon (C2) work can proceed in parallel.

- `POST /api/v1/intake`: one recipe per request, as a JSON object in the shape the siphon already documents. Header `Authorization: Bearer <token>`.
- `GET /api/v1/intake/check`: returns 200 when the token is valid, 401 otherwise. Used by the siphon's "test connection."
- Both sit under `/api/v1/intake`, so a token's scope is that one prefix.
- **Success body:** `{"success": true, "status": "created" | "skipped" | "needs_review", "id": <recipe id or null>, "message": "...", "url": "<link to the recipe or the Imports page>"}`. `needs_review` arrives in phase 2.
- **Error body:** the catalog's standard envelope, `{"error_code", "message", "details", "correlation_id"}`. The siphon shows `message`.
- **Duplicates:** `POST /api/v1/intake?on_duplicate=skip|update` (default `skip`). On an exact-name match among the importer's own recipes, `skip` returns `skipped` with the existing recipe's id and `update` overwrites it and returns `updated`. The siphon sends `update` unless the user turns it off.
- **Built (C1, C2, follow-ups):** the catalog serves both routes and returns `created`, `updated` or `skipped`, with `url` built from `FRONTEND_URL`. The siphon uses both routes, treats `needs_review` as a success (shows `message` with a link to `url`), and shows the error envelope's `message`. The catalog does not return `needs_review` until phase 2.

### 4.4 Cleanup (no model)

One shared module, called from every write path: intake, file upload, recipe create, recipe edit.

- **Yield and times:** normalized and written back in place (`"6 6 servings"` becomes `"6 servings"`). The original stays on the job row. Reuse the existing duration parser. Structured yield (number plus unit) waits until scaling exists.
- **Ingredients:** move the regex parser out of `api/shopping_lists.py` into the shared module; shopping lists import it from there, behavior unchanged. Extend it for notes after commas and in parentheses, and for group headers ("For the dressing:"). The parser reports the lines it could not handle; the exact rules settle against the eval set.
- `recipeIngredient` lines stay verbatim.

Outright siphon bugs still get fixed in the siphon when cheap, but the catalog does not rely on that.

### 4.5 Parsed ingredients

A new key inside `recipe_data`, so there is no migration:

```json
"parsedIngredients": [
  {
    "raw": "2 cups flour, sifted",
    "quantity": 2, "quantityMax": null,
    "unit": "cup", "item": "flour", "note": "sifted",
    "group": null,
    "parsedBy": "regex"
  }
]
```

- One entry per `recipeIngredient` line, in order. `raw` is set by code, never by a model.
- `parsedBy` is `regex`, `model`, or `null` for a line nothing could parse.
- Units come from the existing `normalize_unit` map; unknown units pass through.
- **On every save:** lines whose `raw` text is unchanged keep their entry (including model-parsed ones); changed or new lines get the regex only. No model calls on ordinary edits.

### 4.6 Jobs and review

**Table `intake_jobs`** (from phase 2): `id`, `user_id`, `household_id`, `source` (`siphon | siphon_page | text`), `status`, `source_url`, `payload`, `draft`, `flags`, `recipe_id`, `model`, `tokens`, `cost`, `error`, timestamps.

- `payload` is the original as received, with image data trimmed (the image URL stays). The image lives once: in `draft` while awaiting review, then in the recipe.
- Status: `processing → saved | needs_review | failed`; `needs_review → saved | rejected`. A row stuck in `processing` is a crashed request and is shown as failed with a retry.
- Rejected jobs stay until their importer deletes them.

**Review triggers** for a siphon import (anything else saves directly):
- a duplicate in the household (§4.8)
- missing ingredients or missing steps
- a field over its length cap
- more than about a quarter of ingredient lines unparsed after regex and model

A model parsing a few ingredient lines does not force review. Full-page or pasted-text extraction always does.

**Imports page**
- New page with a count in the navbar, showing the signed-in person's own jobs. Drafts are visible only to their importer, and only the importer can approve.
- Reuses `RecipeForm.svelte`, prefilled from the draft, beside the flags and the source (text or link).
- Actions: approve, edit and approve, reject.

### 4.7 Model use

Two narrow uses, both through one new schema-constrained call added to `services/ai.py`. The existing generation functions are not touched.

| Use | Input | Output | Reviewed |
|---|---|---|---|
| Ingredient-line fallback (phase 3) | Only the lines the regex could not handle | Parses, index-aligned with the input | Only if a trigger fires |
| Extraction (phase 4) | Page text sent by the siphon, or pasted text | A full schema.org recipe | Always |

- **Model setting:** intake has its own, separate from recipe generation. Owner's candidates are GPT-6 Luna and a suitable cheaper Gemma 4 model; the owner confirms both are on OpenRouter. At build time, run each candidate that supports structured output over the eval set and take the cheapest that reaches the 95% target. Record the choice and date beside the setting.
- A second "stronger" model, and a re-run action in the inbox, wait until the eval set shows the first one failing.
- **Failing pages:** when extraction finds nothing, or lacks ingredients or steps, the siphon offers a button to send the page text to the catalog. It is not automatic. The heuristic fallback is frozen: no further work, no rewrite.

### 4.8 Duplicates

- **The importer's own recipe with the same name is not a flag.** The `on_duplicate` setting decides (§4.3): overwrite by default, or skip when the user has turned updating off in the siphon. Decided by the owner on 2026-10-04; this replaces the earlier "exact-name match stays as a weaker flag".
- A normalized source-URL match elsewhere in the household (another member's recipe, or the importer's own recipe under a different name) is a flag: the import goes to review with a link to the existing recipe. When the URL match is the same recipe the name match found, `on_duplicate` decides instead.
- File upload keeps today's `skip | update | create` behavior.

## 5. Guardrails

**Prompt injection**
1. The model has no tools. Content in, JSON out. Fetching and saving happen in code.
2. Structured output against a JSON schema, validated with Pydantic (`extra="forbid"`, length and count caps), with `max_tokens` set.
3. Untrusted content is delimited and described as data in the system message. Defense in depth only.
4. Ingredient fallback: code attaches `raw`; a count mismatch discards the result.
5. Extraction: every URL in the output must appear in the source, and each ingredient line and step must closely match a span of the source text. Misses are flags; the result is reviewed regardless.
6. Stored recipe text remains untrusted for any later model feature.

**Fetching (SSRF), phase 0 and its own change**
- One shared safe-fetch helper replaces `_fetch_and_encode_image`'s client: http/https only; resolve and block private, loopback, link-local and metadata ranges for IPv4 and IPv6; connect to the address that was checked; no unchecked redirects; timeout; size cap; image content-type allowlist; async.
- A Proxmox firewall rule denying the container outbound access to LAN ranges is a worthwhile backstop.

**Cost and privacy** (all three)
- A credit limit on the OpenRouter key, held server-side only.
- A per-user hourly limit on model-using intake, at the existing `AI_RATE_LIMIT_PER_HOUR`. Key it on the user: current limits key on remote address with no forwarded-header handling, so behind the reverse proxy the household likely shares one bucket.
- An OpenRouter data policy that excludes providers who retain or train on requests.
- Model, tokens and cost logged on each job.

**Rendering**
- Svelte escapes by default; no `{@html}` on recipe content; only http(s) links rendered. Keep the existing `sanitize_html` on name and description.

## 6. Cloudflare portability

The option to run on Cloudflare later is kept by avoiding blockers, not by building for two targets:
- no long-lived in-process worker (processing is in-request);
- no dependence on local disk;
- only SQL that SQLite and D1 share.

No second job runner until there is a second platform.

## 7. Phases

| Phase | What ships | Repos | Model |
|---|---|---|---|
| 0 | Safe-fetch fix. API tokens and settings UI. Intake and token-check routes. CSRF skip for token requests. Siphon pointed at the new routes. Direct import works and behaves like today's upload. | both | no |
| 1 | Shared cleanup module on every write path. Parsed ingredients stored. Eval set. Backfill with report (§9). | catalog | no |
| 2 | `intake_jobs`, review triggers, household URL duplicates, Imports page, `needs_review` in the siphon. | both | no |
| 3 | Ingredient-line fallback. Intake model setting, per-user limit, cost logging. Eval run to choose the model. | catalog | yes |
| 4 | Siphon "send page" button, paste-text form, extraction with grounding checks. | both | yes |

Phases 0 to 2 need no model, so problem (a) is mostly solved before any model cost or injection surface exists. Each phase is usable on its own.

### 7.1 Work order: cloud where possible, local where it changes what comes next

The phases above describe what ships. This is the order the work is done in. Most of it runs in Claude Code cloud sessions. Cloud sessions see only what is in the GitHub repo and cannot reach the LAN, the real database, the real-recipe eval set, or a browser with the extension loaded.

**Before starting:** commit this doc into `recipe-catalog` (for example under `docs/requirements/`), since a cloud session cannot read this folder.

Cloud steps (C) are one pull request each, one repo per session, tests passing with the model mocked. Local steps (L) need the LAN, the real database, the OpenRouter key, or a browser. Local work is pulled forward only where its result changes the cloud work that follows; that gives four local checkpoints.

| Order | Step | Where | Work | Phase |
|---|---|---|---|---|
| 0 | **L0** (not needed: the payload question was settled from the siphon's code, and L1b sent real payloads) | local, manual | Download one recipe as JSON from the siphon and keep it. It settles the payload-key question in §11 before C1 and becomes the test payload for L1a | 0 |
| 1 | C1 (done) | cloud, catalog | Safe-fetch helper; API tokens and settings UI; intake and token-check routes; CSRF skip for token requests | 0 |
| 1 | C2 (done) | cloud, siphon | Point at the new routes; token check. Runs in parallel with C1 | 0 |
| 2 | **L1a** (done) | local, Claude Code | After C1 only: deploy the C1 branch (`scripts/proxmox/update-app.sh --branch <name>` in the container), create a token, POST the L0 file to the intake route, confirm the recipe saved. Checks the token, the CSRF skip, and the reverse proxy | 0 |
| 3 | **L1b** (done) | local, manual | After C2: load the new siphon build in the browser, enter the token, import a recipe from a live page | 0 |
| 4 | C3 | cloud, catalog | Shared cleanup module on every write path; parsed ingredients; in-repo test lines; eval harness that reads a git-ignored folder; backfill script with dry-run report | 1 |
| 5 | **L2** | local | Build the eval set (catalog export, the 12 failing pages as text); run the harness on the regex parser; run the backfill dry-run report | 1 |
| 6 | C3b | cloud, catalog | Parser fixes from L2, if the numbers or the report call for them | 1 |
| 7 | **L2b** | local | Re-run the harness; when satisfied, back up and apply the backfill | 1 |
| 8 | C4 | cloud, catalog | `intake_jobs`, review triggers, household URL duplicates, Imports page | 2 |
| 9 | C5 | cloud, siphon | `needs_review` display is already in C2; remaining work is limited to any Imports page links from phase 2 | 2 |
| 10 | C6 | cloud, catalog | Schema-constrained model call; intake model setting; per-user limit; cost logging; ingredient-line fallback | 3 |
| 11 | **L3** | local | Deploy; exercise the Imports page with real imports, including a duplicate and a flagged one; set the OpenRouter credit limit and data policy; run the candidate models over the eval set; set the intake model | 2, 3 |
| 12 | C7 | cloud, catalog | Paste-text form; extraction with grounding checks | 4 |
| 13 | C8 | cloud, siphon | "Send page" button | 4 |
| 14 | **L4** | local | Send the failing pages through extraction end to end; adjust prompts and grounding thresholds | 4 |
| any time | L5 | local | Optional: Proxmox firewall rule blocking the container's outbound access to LAN ranges | none |

The siphon steps are written against the contract in §4.3, so they do not wait on a deployed catalog.

**Why each early checkpoint earns its place**
- **L1a and L1b:** prove the contract everything else sits on, against the real setup: the token, the CSRF skip, the reverse proxy, and the siphon's actual payload. A mismatch found here is one small fix; found after C8 it touches four pull requests. L1a needs only C1, so it does not wait for the siphon work. A local Claude Code session can run L1a given SSH access to the container; deploying changes the live service, so it asks first. L1b is about five minutes by hand, because loading an extension and clicking its popup is not something to automate.
- **L2 after C3:** the parser rules are meant to settle against real recipes. The "more than a quarter unparsed" review trigger (C4) and the list of lines sent to a model (C6) both depend on what the parser really misses. The backfill report is the same data seen another way.
- **L3 after C6:** the model has to be chosen before extraction is written (C7), because prompts and schema handling are tuned to the model in use. Review-page testing rides along on the same deploy.
- **L4 last:** nothing follows it.

Steps 8 to 10 run back to back in the cloud with no local stop, since nothing real is needed between them.

## 8. Eval set

- **In the repo:** hand-written ingredient lines covering each pattern, as ordinary tests.
- **Outside git (ignored folder):** an export of the owner's catalog, plus the siphon's 12 failing pages saved as text. Real recipes are other people's text and stay out of the repo.
- One test compares output with hand-checked expectations and reports the two target numbers. Run it whenever the parser, a prompt, or the model changes.

**Built (C3).** In-repo lines: `backend/tests/test_ingredient_parser.py`. Harness: `backend/app/services/intake_eval.py`, run with `backend/scripts/intake_eval.py`; the folder is `backend/eval-data/` (git-ignored) or `INTAKE_EVAL_DIR`. For L2, from `backend/`:

1. Put a catalog export in `eval-data/inputs/`: the Export page's complete backup (`complete_backup_<date>.json`) or the recipes export in JSON. Image data is dropped from the cases; the collections export has no recipe content and is skipped. Save the 12 failing pages as text in `eval-data/pages/` for phase 4; this harness does not read them.
2. `uv run python scripts/intake_eval.py draft --sample 40` writes cases for a repeatable random sample of 40 recipes to `eval-data/cases/`, prefilled with the current output. About 40 recipes (~400 lines) is enough to measure line accuracy within a few percent; a larger `--sample` keeps the earlier picks and adds more (`--seed` changes the draw). Without `--sample` it drafts every recipe.
3. `uv run python scripts/intake_eval.py originals` writes each case's source record, with image data omitted, to `eval-data/originals/` under the same file name as the case, for side-by-side comparison.
4. Hand-check each case: correct `expected`, mark junk lines `"ignore": true`, set `"checked": true`.
5. `uv run python scripts/intake_eval.py run` prints the two numbers and every mismatch. `uv run pytest tests/test_intake_eval.py -s -k eval_set` does the same as a test (`INTAKE_EVAL_STRICT=1` makes it fail below target).

"Needs no edits" is measured as: yield, times and every ingredient line match the hand-checked case.

## 9. Backfill

A one-off script at the end of phase 1, deterministic only.

1. Dry run produces a report: per recipe, the yield and time changes and how many ingredient lines parsed; plus every line that did not.
2. The owner reviews the report. Nothing is written before approval.
3. On approval the script backs up the database and applies everything in one run, with an option to exclude listed recipes.

Model parsing of leftover lines in old recipes waits until shopping lists use parsed ingredients.

**Built (C3).** `backend/scripts/backfill_cleanup.py` (logic in `app/services/recipe_backfill.py`). From `backend/`, so `.env` is read:

- `uv run python scripts/backfill_cleanup.py` is the dry run. It writes `backfill-report-<timestamp>.md` (git-ignored) and changes nothing.
- `--exclude 12,40` or `--exclude-file ids.txt` leaves recipes out; `--include-deleted` also cleans the trash.
- `--apply` first copies the SQLite file to `recipes.db.bak-<timestamp>` with SQLite's backup API, then writes every change in one transaction. Stop the app before applying. Applied recipes keep `updated_at` and `is_modified`.
- Running it again after applying reports nothing to change.

## 10. Deferred and parked

**Deferred, designed when reached**
- **Photos and YouTube.** Known constraints: photo storage must work on Cloudflare too; iPhone photos arrive as HEIC; recipes span several images; these may need background processing; transcript fetching is unofficial and fragile; neither can be grounded against source text, so both are always reviewed.
- **Phone import and server-side page fetch.** Would reuse the safe-fetch helper.
- **Shopping lists reading `parsedIngredients`** (problem d): the one planned follow-on.
- **Exposure beyond the LAN.** Revisit rate limits and token handling first.

**Parked ideas, not planned**
- Controlled tag vocabulary; model-suggested dietary labels; fuzzy duplicate matching; scaling and unit conversion; "what can I make."
- Moving images out of the database.
- Updating the old default for the recipe-generation model.
- Porting the backend to Cloudflare Workers + D1.

## 11. To check at build time

- Exact OpenRouter ids, prices, and structured-output support for the candidate models. A lookup on 2026-10-04 returned only a partial model listing that did not include them, so these are unverified here.
- ~~The siphon's real payload keys.~~ Settled: the siphon's code sends `equipment` and `notes` (`src/formatters/recipe-formatter.js`), which the catalog reads. Only its API doc example said `recipeEquipment` and `recipeNotes`, and that doc has been corrected.
- Whether the reverse proxy passes the client address, and whether the app reads it.
- Catalog conventions that apply to all of this are in its `CLAUDE.md` and `AGENTS.md`: household scoping, Alembic rules, the error envelope, structlog style, `uv run`.

## 12. Decision log (2026-10-04)

| Decision | Choice |
|---|---|
| Priority | (a) messy fields, (b) failing pages, (c) new sources, (d) shopping lists later |
| Import path | Direct, token-authenticated API; replaces download-and-upload |
| Storage | schema.org `recipe_data` stays canonical; parsed ingredients are an extra key |
| Users | Owner and household members all import |
| Flagged imports | Wait as a draft on the job row; unflagged save directly |
| Image-fetch SSRF | Fixed as its own change |
| Image storage | Left alone; one copy per import |
| Deployment | Proxmox now; avoid blocking a Cloudflare port |
| Tokens | Personal, hashed, intake-only, revocable, no expiry |
| Processing | Inside the request |
| Cleanup location | The catalog, for every write path |
| Ingredient parsing | Existing regex first; model only for lines it cannot handle |
| Cleanup writes | Yield and times overwritten; ingredient lines verbatim |
| Failing pages | A button in the siphon; heuristics frozen |
| Approval | The importer only |
| Duplicates | Household URL match is a review flag; the importer's own same-name recipe follows `on_duplicate` (overwrite by default, user can switch to skip in the siphon) |
| Model | Separate intake setting; cheapest candidate reaching 95% on the eval set |
| Limits | Key credit limit, per-user hourly limit, no-retention provider policy |
| File upload | Deterministic cleanup, direct save, no review |
| Backfill | Report first, then backup and apply |
| Targets | 95% of ingredient lines; 90% of imports with no edits |
| Scope | Tagging, dietary, fuzzy duplicates and "unlocks" parked |
