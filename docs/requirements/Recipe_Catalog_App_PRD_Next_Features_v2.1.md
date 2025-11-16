# Recipe Catalog App – Product Requirements Document (Next Feature Set)

**Version:** 2.1 (Next Feature Set)  
**Date:** November 16, 2025  
**Status:** Draft  

**Based On:**

- Recipe_Catalog_App_PRD_v1.1.md  
- IMPLEMENTATION_STATUS.md  
- REMAINING_FEATURES.md  
- additional-features-2025-11-15.md  

---

## 0. Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0 | Nov 16, 2025 | Product Owner | First draft of next-feature PRD: SSO, household tenancy, meal planning, shopping lists, AI helpers, themes, PDF export. |
| 2.1 | Nov 16, 2025 | Product Owner | Updated based on decisions: IdP-first direction, passkeys as future supplement, max household size and one-household-per-user rule, shopping list sections clarified, simple PDF layout. |

---

## 1. Executive Summary

The core Recipe Catalog MVP is production-ready with all v1.1 MVP features implemented, plus several advanced features.

This document defines additional product requirements for the next wave of functionality that has not yet been implemented, with a focus on:

1. **Authentication & Identity**
   - Add identity providers (Google, Microsoft, etc.) to reduce password storage and attack surface.
   - Long-term direction: move toward **passwordless-by-default**, with:
     - Third-party identity providers as the primary method.
     - Future support for **passkeys** as an additional, secure login method for users who don’t want or can’t use IdPs.
   - Email remains used only for authentication and account/security flows, not marketing.

2. **Household / Group Multi-User Tenancy**
   - Families or small groups that share the same recipe catalog, collections, meal plans, and shopping lists.
   - Maximum household size of **10 members** (configurable), with **one household per user**.

3. **Planning & Execution**
   - Meal planning for the week (calendar-style planning).
   - Shopping lists generated from selected recipe ingredients and meal plans.

4. **AI Assistance**
   - AI-generated recipes based on available ingredients.
   - AI-generated menu suggestions based on dietary preferences and constraints.

5. **UI & Accessibility**
   - Additional themes including dark mode and a high-contrast theme.

6. **Export Enhancements**
   - PDF export of recipes and collections, using a simple, readable layout.

Explicitly out of scope for this phase:

- Social / community / social media sharing features (no “social graph,” no social posting).
- Browser extension functionality (handled as a separate project).
- Native mobile apps, offline/PWA, and advanced AI/intelligence still remain future roadmap items unless explicitly required to support the above.

---

## 2. Scope & Goals

### 2.1 In Scope (This Document)

Features which are either not implemented at all or require a new, more detailed spec to move from “future idea” into concrete, buildable requirements:

1. Identity Provider Authentication (SSO)
2. Household / Group Multi-User Tenancy
3. Weekly Meal Planning
4. Shopping Lists
5. AI-Generated Recipes from Ingredients
6. AI-Generated Menu Suggestions from Preferences
7. Additional UI Themes (Dark Mode + High Contrast)
8. PDF Export for Recipes & Collections

### 2.2 Out of Scope (Confirmed)

- Social Media / Social Graph / Community Features
  - No public profiles
  - No followers/friends/likes
  - No sharing directly to social networks
  - No “trending recipes” or public feeds

- Browser Extension
  - Already being handled as a separate project, not included here.

- Existing Auth Flows
  - Email/password auth as implemented will remain for now, but this document adds identity providers on top and establishes the direction of moving toward IdP-first and, later, passkeys.

- Other Future Features
  - Advanced tagging, cooking mode, deep AI/intelligence, etc. are retained as roadmap ideas but not fully specified in this version.

---

## 3. Product Principles (Inherited)

The core product principles from PRD v1.1 remain unchanged and continue to drive these features: Privacy First, Simplicity, Flexibility, Respect, Reliability.

---

## 4. Technical Architecture Updates (High-Level)

Base stack remains:

- **Backend:** FastAPI (Python)
- **Frontend:** SvelteKit
- **DB:** SQLite (D1) with PostgreSQL-ready design
- **Hosting:** Cloudflare Pages + Workers, self-hosted alternative as backup

New/updated dependencies:

1. **Identity Providers (IdPs)**
   - OIDC-based providers such as Google, Microsoft, and optionally GitHub.
   - Use standard OAuth 2.0/OIDC flows on backend.
   - Store minimal profile info (subject ID, email, issuer, display name).

2. **Passkeys (Future)**
   - WebAuthn/FIDO2 passkeys are treated as a **future supplementary auth method**:
     - Alternative for users who don’t wish to use external IdPs but still want passwordless login.
     - Accounts are still mapped to a server-side user record, but no secrets (passwords) are stored—only public keys.
   - Out of scope to implement in this phase; captured here to ensure future architecture alignment with the IdP and account model.

3. **AI Provider**
   - External LLM API (e.g., OpenAI / Anthropic, vendor TBD).
   - Scoped for:
     - Recipe generation from ingredients
     - Menu suggestions based on preferences
   - Data minimization: send only what’s necessary (ingredient lists, dietary tags, and user-provided prompts), not the full recipe library unless explicitly required.

4. **PDF Generation**
   - Server-side PDF renderer (e.g., headless browser or dedicated PDF library).
   - Use existing recipe layout as baseline for PDF styling, with a **simple, clean design** for this phase (no complex “cookbook” layouts).

---

## 5. Email Usage Clarification

Email is used for:

- Account verification
- Password reset (while passwords are still supported)
- Account-related messaging (e.g., security notifications)
- Household invitations (see Household feature)

This phase does not introduce any new email-based product features (no digest emails, no marketing campaigns). Email remains strictly for:

- Authentication & security events (verification, resets, account and household invitations)
- Critical account notifications (security alerts, if implemented)

---

## 6. Feature 14 – Identity Provider Authentication (SSO)

### 14.1 User Stories

1. As a new user, I want to sign up and log in with Google or Microsoft so I don’t have to create or manage a separate password for the Recipe Catalog app.
2. As an existing user with an email/password account, I want to link my account to an identity provider and optionally stop using a local password.
3. As a security-conscious user, I want to see which identity provider I’m using and manage/remove linked providers.

### 14.2 Functional Requirements

#### Authentication Options

- Support sign-in / sign-up via:
  - Google (OIDC)
  - Microsoft (OIDC)
  - Optional: GitHub (OIDC) – feature flag / future toggle

- Login/register UI:
  - “Continue with Google”
  - “Continue with Microsoft”
  - “Sign up with email” (existing path, still available but visually deprioritized to signal IdP-first direction)

#### Account Linking & Mapping

- When a user authenticates via IdP:
  - If an account with that email exists and is not yet linked to that IdP:
    - Offer a secure linking path (after verifying user intention, e.g., confirm via password or email confirmation).
  - If an account already has a linked IdP with the same Id and issuer:
    - Log them in immediately.
- A user may link multiple providers to the same account:
  - Example: Google + Microsoft.
- Allow user to:
  - View linked providers in **Settings → Security**.
  - Remove a linked provider (if at least one other login method remains, e.g., another IdP or local password).

#### Email Verification Behavior

- For IdP-based sign-in:
  - Trust email verification if IdP asserts `email_verified=true`.
  - Mark the Recipe Catalog account as verified without separate email verification.
- For email/password users:
  - Keep existing verification flow.

#### Passwordless and IdP-First Direction

- For a user who has only IdPs linked (no password set):
  - Allow account to exist without a local password.
- UI in settings:
  - “Use only identity providers (no separate password)” toggle, with explanation and confirmation.
- For new users who sign up via IdP:
  - Do not require creating a local password by default.
- Long-term direction:
  - Default flow for new users is IdP-based registration.
  - Email/password registration may be disabled or hidden for general users in a future phase, while retaining a path for admin/emergency usage if needed.

#### Passkeys (Future Supplement)

- Passkeys are considered a **supplement** rather than a replacement for IdPs:
  - Provide a fully passwordless option for users who do not wish to use external IdPs.
  - Can be offered as:
    - An additional login method for existing users.
    - A future alternative to email/password for new users, alongside IdPs.
- Requirements for passkeys are not part of this implementation phase but are noted to ensure:
  - User entity design supports multiple auth methods (IdP, passkeys).
  - Security and UX flows can extend gracefully to WebAuthn in future work.

#### Admin/Config Controls

- Configurable via environment / settings:
  - Which IdPs are enabled.
  - Redirect URIs and client IDs/secrets.
- Fallback behavior:
  - If a provider is temporarily unavailable, UI shows an error and suggests alternative methods.

### 14.3 Acceptance Criteria

- Users can successfully sign up and log in with Google and Microsoft.
- Existing email/password users can link an IdP without creating a duplicate account.
- Removing an IdP is blocked if it would leave the account with no login methods.
- Email addresses from IdPs are treated as verified when `email_verified=true`.
- New IdP-only users are able to log in without ever setting a password.
- All auth flows work with current REST API and token-based session management.

### 14.4 Non-Functional Requirements

- Use standard OAuth 2.0/OIDC libraries.
- Store only:
  - Issuer
  - Subject (sub)
  - Email
  - Display name (optional)
- Log auth events (success/fail) for security auditing, without logging sensitive tokens.
- Ensure CSRF/redirect protections for OAuth flows.

---

## 7. Feature 15 – Household / Group Multi-User Tenancy

### 15.1 User Stories

1. As a user, I want to share my recipes, collections, meal plans, and shopping lists with my family so we can all contribute and use the same catalog.
2. As the household owner, I want to manage who has access and remove people if needed.
3. As a household member, I want my personal settings (theme, preferences) to remain mine, even though we share recipes and plans.

### 15.2 Functional Requirements

#### Household Concept

- Introduce a Household (or “Shared Library”) entity:
  - A household has:
    - Name
    - Owner (user)
    - Members (users; includes owner)
    - Created/updated timestamps
- Each user belongs to exactly **one household** in this phase:
  - One household per user is the rule.
  - Future enhancement (multiple households per user) is explicitly out of scope.

#### Household Size Limits

- Maximum household size:
  - Default maximum of **10 members** (including the owner).
  - Configurable via environment / settings for future adjustments.
- If an owner tries to invite a new member when the household is at its limit:
  - Show a clear error message and do not send the invitation.

#### Shared vs. Personal Scope

- Shared at household level:
  - Recipes
  - Collections (including Favorites logically scoped to household)
  - Meal plans
  - Shopping lists
- Personal (per-user):
  - UI preferences: theme, default view, sort order, timezone
  - Session state (filters, search history)
  - Email address and authentication methods

#### Household Membership Management

- A logged-in user can:
  - Create a household on first launch (if none assigned).
  - Invite others by email:
    - Invitee receives secure invitation link (via email).
    - When the invitee accepts:
      - If they have an account, they join the household (subject to max size).
      - If they don’t, they are guided through sign-up (SSO or email) then join.
  - View list of household members (name, email, role).
  - Remove a member (owner only).
- Roles:
  - Owner:
    - Can rename household.
    - Manage invitations and member removal.
    - Cannot leave household without transferring or deleting it (and transfer is optional future enhancement).
  - Member:
    - Can create/edit/delete recipes, collections, meal plans, shopping lists.
    - Cannot delete household or remove owner.

#### Data Access Behavior

- When any household member logs in:
  - They see all recipes, collections, meal plans, and shopping lists for their household.
- Actions:
  - Creating/editing/deleting recipes affects the shared catalog.
  - Actions are attributed to the user (audit info, e.g., “Last modified by”).

#### Migration Behavior

- Existing single-user accounts:
  - On first run after release:
    - Auto-create a “Personal Household” (named after the user or an appropriate default).
  - All existing recipes/collections become scoped to that household.

### 15.3 Acceptance Criteria

- A user can successfully invite another user via email and see them join the same household, up to the maximum household size.
- Members see the same recipes, collections, meal plans, and shopping lists.
- Deleting a member:
  - Does not delete recipes or plans.
  - If the removed member later logs in, they are prompted to join or create another household (subject to one-household-per-user rule).
- Personal settings (theme, sort order, etc.) do not change when another member changes theirs.
- Existing users’ data is preserved and accessible in their new “personal household” after migration.

### 15.4 Non-Functional Requirements

- Household membership enforcement must be done at the API level to prevent data leakage.
- All queries for recipes, collections, plans, and lists must be filtered by household_id.
- Ensure performance remains acceptable for households with:
  - 5–10 members
  - 1,000+ recipes

---

## 8. Feature 16 – Weekly Meal Planning

### 16.1 User Stories

1. As a user, I want to plan my meals for the week by assigning recipes to specific days so I know what I’ll cook and when.
2. As a household, we want to share the same meal plan so everyone can see what’s planned.
3. As a user, I want the meal plan to drive shopping list generation.

### 16.2 Functional Requirements

#### Meal Plan Representation

- Meal plan is organized by week (Monday–Sunday or locale-specific).
- Basic granularity:
  - Day
  - Meal type: Breakfast / Lunch / Dinner / Other
- Each planned meal includes:
  - Reference to a recipe
  - Day & meal type
  - Optional notes (e.g., “guests coming,” “double batch”)
  - Number of servings (optional; interacts with scaling)

#### UI – Calendar View

- Weekly calendar-like grid:
  - Columns = days
  - Rows = meal types
- For each cell:
  - Display recipe name(s) scheduled
  - Support multiple recipes in one cell (e.g., main + side)
- Interaction:
  - Add a recipe to a cell via:
    - “Add meal” button → search/select recipe
    - From recipe detail: “Add to meal plan” → day & meal type picker
  - Edit/delete planned meals
  - Drag & drop (future enhancement, not required in this phase)

#### Household Sharing

- Meal plans are per household, not per user.
- Any member can:
  - Add, move, or remove planned meals.
- Changes apply immediately and are visible to all household members.

#### Integration with Shopping Lists

- From meal plan:
  - “Generate shopping list for this week” (see Feature 17).
  - Optional:
    - Include/exclude certain days/meal types in the generation dialog.

### 16.3 Acceptance Criteria

- A user can create a weekly meal plan and assign recipes to days/meals.
- Multiple users in the same household see the same plan and can modify it.
- A user can generate a shopping list from the weekly plan.
- No recipes are duplicated or lost when editing or moving planned meals.
- Meal planning UI works on both desktop and mobile.

### 16.4 Non-Functional Requirements

- Meal plans should load in under 1 second for typical week views.
- Handle at least 52 weeks of historical/future plans without significant UI slow-down.

---

## 9. Feature 17 – Shopping Lists

### 17.1 User Stories

1. As a user, I want to create a shopping list from a recipe’s ingredients so I know exactly what to buy.
2. As a household, we want shared shopping lists so anyone can use them at the store.
3. As a user, I want to aggregate ingredients from multiple recipes or an entire meal plan into a single list.

### 17.2 Functional Requirements

#### List Creation

- From recipe detail:
  - “Add ingredients to new shopping list”
  - “Add ingredients to existing shopping list”
  - Allow the user to select which ingredients to include (checkbox list).
- From meal plan:
  - “Generate shopping list for selected days/meal types”
  - Multi-select days/meal types and optionally recipes.
- From shopping list screen:
  - Create list manually and add ad-hoc items.

#### List Structure

- A shopping list belongs to a household.
- Each list has:
  - Name (e.g., “This Week’s Groceries”, “Party on Saturday”)
  - Optional description
  - Created/updated timestamps
- Each list item has:
  - Name (ingredient / item)
  - Quantity (text field; may be aggregated, e.g., “3 cups”)
  - Checked (boolean)
  - Optional note (brand, store, substitution)
  - Optional category/section

#### Store Sections / Categories

- “Store sections” refer to typical areas/aisles in a grocery store (e.g., Produce, Dairy, Meat, Bakery, Frozen, Pantry, Household, Other).
- Implementation:
  - Pre-populate a small **default list of sections** (e.g., Produce, Dairy, Meat, Bakery, Frozen, Pantry, Household).
  - Allow the section/category field for each item to be:
    - Chosen from the default list, **or**
    - A custom free-text value.
- The UI may optionally group items visually by section, but basic grouping (e.g., sorted by section name) is sufficient for this phase.

#### Ingredient Aggregation

- When adding ingredients from multiple recipes:
  - Attempt to normalize obvious duplicates (e.g., “1 cup sugar” + “2 cups sugar” → “3 cups sugar”) when units match.
  - If not trivial to aggregate, group similar items visually and leave quantities as separate notes.
- Provide a manual “Merge items” feature:
  - User can select multiple items and merge into one.

#### Interaction & UX

- Mobile-friendly list view with large tap targets.
- Items can be:
  - Checked/unchecked
  - Edited inline
- Lists can be:
  - Renamed
  - Duplicated
  - Archived (for historical reference)
  - Deleted (with confirmation)

#### Household Sharing

- All household members:
  - See the same list, updated in near real-time.
  - Can check off items and those changes appear for others.

### 17.3 Acceptance Criteria

- A user can create a list from a recipe and see ingredient items for that recipe.
- A user can generate a list from a meal plan covering multiple recipes.
- Checking items off updates the list for all household members.
- Ingredient aggregation works for simple cases (same ingredient name & unit).
- Users can add custom items not tied to recipes.
- Store sections are available via a simple default list, but users can also enter custom section names.

### 17.4 Non-Functional Requirements

- Lists must remain usable even with 100+ items.
- Changes to list items propagate quickly (e.g., via polling or light real-time update; real-time tech decision TBD).

---

## 10. Feature 18 – AI-Generated Recipes from Ingredients

### 10.1 User Stories

1. As a user, I want to enter a list of ingredients I have on hand and receive a suggested recipe so I can cook without shopping.
2. As a user, I want to review and edit AI-generated recipes before adding them to my collection.

### 10.2 Functional Requirements

#### Input Form

- Accessible from:
  - Main navigation (“AI Cook from Pantry”)
  - Recipe listing/search (button or CTA)
- Input fields:
  - List of ingredients (free text and/or tokenized inputs)
  - Optional constraints:
    - Cuisine preferences
    - Time limit
    - Dietary preferences (vegetarian, vegan, etc.)
    - Equipment constraints (e.g., “no oven”)

#### AI Generation

- Call an external LLM service with a carefully crafted prompt including:
  - Ingredient list
  - Optional constraints
  - Request a structured output that matches internal recipe JSON fields (name, ingredients, instructions, etc.), aligned with current schema.

#### Review & Save

- Show an editable preview of the recipe:
  - Name, description
  - Ingredients
  - Instructions
  - Optional: tags, category, cuisine
- The user can:
  - Edit any field
  - Save as a manual recipe (origin = “AI-assisted – manual review”)
  - Discard result
- Mark AI-generated recipes clearly in the UI (e.g., badge “AI-assisted”).

#### Safety & Disclaimers

- Show a food-safety disclaimer:
  - “AI-generated recipes may contain errors. Please use your judgment and follow safe food-handling practices.”
- Do not claim AI recipes have been tested.

### 10.3 Acceptance Criteria

- User can input ingredients and get a recipe suggestion within an acceptable time (e.g., <10 seconds).
- The generated recipe is shown in an editable form.
- User can save the AI recipe and see it alongside other recipes in their catalog.
- AI-generated recipes are clearly labeled as such.

### 10.4 Non-Functional Requirements

- Data minimization: send only necessary data to the AI provider.
- Handle AI provider failures gracefully (fallback message, no crash).
- Rate limit AI features to prevent abuse and control costs.

---

## 11. Feature 19 – AI-Generated Menu Suggestions

### 11.1 User Stories

1. As a user, I want menu suggestions for a given time window (e.g., “next week”) that respect my dietary preferences.
2. As a user, I want to either:
   - Use my existing recipes, or  
   - Ask AI to suggest menus even if my catalog is small.

### 11.2 Functional Requirements

#### Input & Preferences

- Menu suggestions wizard:
  - Time range (e.g., single day, weekend, week)
  - Meals per day (breakfast/lunch/dinner)
  - Dietary preferences:
    - Vegetarian, vegan, pescatarian
    - Gluten-free, dairy-free, etc.
  - Optional goals:
    - Minimize prep time
    - Focus on pantry items
- Preferences can also be stored at user level (e.g., “default dietary profile”) in settings, but can be overridden per suggestion.

#### Suggestion Modes

- Catalog-first mode:
  - Use the user/household’s existing recipes as primary candidates.
  - AI (or deterministic logic) suggests combinations of recipes that fit preferences.
- AI-only mode:
  - Instead of drawing only from stored recipes, AI can propose menu ideas, each:
    - Optionally backed by an AI-generated recipe (Feature 18), or
    - Suggesting recipe categories/ideas without full recipe detail.

#### Integration with Meal Plan

- User can:
  - Accept suggested menu (full or partial).
  - Apply selected suggestions directly to the weekly meal plan (Feature 16), populating days and meal types.

### 11.3 Acceptance Criteria

- User can get menu suggestions that respect dietary filters.
- User can choose between catalog-first or AI-only suggestions.
- User can apply suggestions to the meal plan with minimal clicks.
- Menu suggestions are clearly labeled as AI suggestions and are editable.

### 11.4 Non-Functional Requirements

- Same AI safety, rate limiting, and privacy constraints as Feature 18.
- Ensure that suggestions are generated in a reasonable time (<10–15 seconds).

---

## 12. Feature 20 – Additional UI Themes (Dark Mode & High-Contrast)

### 12.1 User Stories

1. As a user, I want a dark mode to reduce eye strain, especially at night.
2. As a user with visual sensitivity, I want a high-contrast theme that’s easier to read.
3. As a user, I want the app to remember my theme preference across devices.

### 12.2 Functional Requirements

#### Theme Options

- Extend existing theming system with:
  - Light (existing)
  - Dark
  - High-contrast (WCAG AA / AAA friendly)
  - System default (follow OS/browser preference) – optional

#### Selection & Persistence

- Theme selection UI in settings (and optional quick toggle in header).
- Theme preference:
  - Stored in user preferences in DB.
  - Also cached in localStorage for quicker load.
- On first load (before auth):
  - Use system theme or last known local preference.
- After login:
  - Use stored user preference, overriding local default.

#### Accessibility

- High-contrast theme must:
  - Meet or exceed WCAG AA contrast ratios.
  - Maintain clear focus indicators for keyboard navigation.
- Ensure no information is conveyed by color alone (icons/labels as needed).

### 12.3 Acceptance Criteria

- Users can switch between light, dark, and high-contrast themes.
- Theme persists across sessions and devices for logged-in users.
- High-contrast theme passes automated color contrast checks on key UI components.
- No visual regressions (text remains readable, key UI elements visible).

---

## 13. Feature 21 – PDF Export for Recipes & Collections

### 13.1 User Stories

1. As a user, I want to export a single recipe as a nicely formatted PDF so I can print or share it offline.
2. As a user, I want to export a collection (e.g., “Holiday Dinner”) as a multi-recipe PDF “mini cookbook.”

### 13.2 Functional Requirements

#### Export Options

- From recipe detail view:
  - “Export as PDF”
- From collections view:
  - “Export collection as PDF”
  - Options:
    - All recipes in collection
    - Selected recipes within collection
- From export page (existing export UX):
  - Add “PDF” as another format option, where applicable.

#### PDF Layout – Simple for This Phase

- For single recipe:
  - Title, hero image (if available)
  - Basic metadata (time, yield, cuisine, category)
  - Ingredients (simple list, optionally with checkboxes)
  - Instructions (numbered)
  - Notes and nutrition (if available)
  - Source attribution as in web view.
- For multi-recipe (collection):
  - Simple cover page:
    - Collection name, optional description, date
  - Optional table of contents
  - Recipes printed sequentially with page breaks.
- Layout is intentionally simple and focused on readability:
  - No complex cookbook styling, advanced typography, or custom templates in this phase.
  - Future enhancement may introduce richer layouts and custom branding options.

#### Export Generation

- PDF generation is server-side to ensure consistent layout.
- Multi-recipe exports produce a single PDF file for this phase.

#### Limits & Performance

- Set reasonable limits to avoid timeouts:
  - Up to N recipes per PDF (e.g., 50).
  - Up to M pages (soft limit; show warning if exceeded).
- Show progress indication for longer exports.

### 13.3 Acceptance Criteria

- User can export any single recipe as a PDF and download it.
- User can export an entire collection as a PDF with a simple cover and optional TOC.
- PDF preserves key information (no missing ingredients/instructions).
- Source attribution appears in the PDF.
- Large exports fail gracefully with a clear error and suggestions (e.g., export smaller collections).

---

## 14. Data Model Additions (High-Level)

New or updated entities (exact schema deferred to technical design):

1. households
   - id, name, owner_user_id, created_at, updated_at

2. household_members
   - id, household_id, user_id, role (owner/member), joined_at

3. meal_plans
   - id, household_id, week_start_date, created_by_user_id, created_at

4. planned_meals
   - id, meal_plan_id, recipe_id, day_of_week, meal_type, servings, notes

5. shopping_lists
   - id, household_id, name, description, status (active/archived), created_by_user_id, created_at, updated_at

6. shopping_list_items
   - id, list_id, item_name, quantity, unit (optional), category, notes, checked, created_at, updated_at

7. identity_providers
   - id, user_id, provider_name, provider_subject, email_at_provider, created_at, last_used_at

8. (Optional later) ai_logs for auditability of AI usage.

---

## 15. Privacy, Security & Risk Updates

- **SSO/IdP:**
  - Reduces attack surface for password storage.
  - Risk: configuration errors or token misuse → mitigated via standard libraries and minimal data retention.

- **Passkeys (Future):**
  - Provide a secure, phishing-resistant alternative to passwords for users who prefer not to use IdPs.
  - Risk: UX complexity and device availability → mitigated by keeping IdPs as the primary, simple path and introducing passkeys as an advanced option later.

- **AI Features:**
  - Risk of data leakage to AI providers:
    - Mitigation: data minimization, do not send full recipe library by default, document provider in privacy policy.
  - Risk of unsafe or incorrect recipes:
    - Mitigation: disclaimers, require manual review before saving.

- **Household Multi-Tenancy:**
  - Risk of cross-tenant data exposure if filtering is incorrect:
    - Mitigation: enforce household scoping on all queries; add tests to verify isolation.

- **PDF Export:**
  - Risk of heavier compute use and potential abuse:
    - Mitigation: limits per export, rate limiting on export endpoints.

Email remains limited to:

- Auth & security flows  
- Household invitations  

No marketing or tracking emails.

---

## 16. Success Metrics (This Phase)

Measure success of this feature set with:

- **Authentication**
  - % of new signups using IdPs vs password.
  - Reduction in password-related support issues.

- **Household Usage**
  - % of users in multi-user households.
  - Average household size (should cluster below or at the 10-member limit).

- **Planning & Lists**
  - % of active households with at least one meal plan per month.
  - Average number of shopping lists created per household.

- **AI Usage**
  - Number of AI recipe generations per active user per month.
  - Number of AI menu suggestions applied to meal plans.

- **UI & Export**
  - % of users using dark mode or high-contrast theme.
  - Number of PDF exports per month.

---

## 17. Dependencies & Open Questions

### 17.1 Dependencies

- Identity providers (Google, Microsoft) accounts and configuration.
- AI provider selection, legal/privacy review, and API keys.
- PDF rendering stack (headless browser vs. library).
- Existing backend & frontend codebase (FastAPI, SvelteKit).

### 17.2 Open Questions (Remaining)

1. **Passkey Implementation Timeline**
   - When and how to introduce passkeys as a supplementary auth method:
     - New-user flows vs. advanced settings.
     - Device support, recovery, and account recovery strategies.

2. **Household Admin UX**
   - Do we need explicit ownership transfer flows in this phase, or can we defer them?

3. **AI Provider**
   - Which vendor(s) will we use?
   - Any special data residency or compliance requirements?

4. **Real-Time Updates**
   - For shared shopping lists and meal plans, do we introduce WebSocket/real-time mechanisms now, or rely on periodic polling for this phase?

5. **Export Limits**
   - Exact values for maximum recipes/pages per PDF, based on early load testing.

