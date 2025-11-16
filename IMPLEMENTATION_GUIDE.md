# Recipe Catalog - Implementation Guide & File Reference

## COMPLETE FILE PATHS (Absolute)

### Core Configuration
- `/home/user/recipe-catalog/frontend/src/lib/config.ts` - API base URL configuration
- `/home/user/recipe-catalog/frontend/src/app.css` - Theme definitions and CSS variables
- `/home/user/recipe-catalog/frontend/src/app.html` - Root HTML template

### Store Files
- `/home/user/recipe-catalog/frontend/src/lib/stores/auth.ts` - Authentication state management
- `/home/user/recipe-catalog/frontend/src/lib/stores/collections.ts` - Collections state management

### API Client Files
- `/home/user/recipe-catalog/frontend/src/lib/api/client.ts` - HTTP request wrapper with auth
- `/home/user/recipe-catalog/frontend/src/lib/api/users.ts` - User profile, preferences, stats
- `/home/user/recipe-catalog/frontend/src/lib/api/recipes.ts` - Recipe CRUD operations
- `/home/user/recipe-catalog/frontend/src/lib/api/collections.ts` - Collections CRUD operations

### Navigation & Layout Components
- `/home/user/recipe-catalog/frontend/src/lib/components/Navbar.svelte` - Main authenticated navbar
- `/home/user/recipe-catalog/frontend/src/lib/components/CollectionsSidebar.svelte` - Collections sidebar (UNUSED)
- `/home/user/recipe-catalog/frontend/src/lib/components/FilterSidebar.svelte` - Recipe filter sidebar

### Theme Components
- `/home/user/recipe-catalog/frontend/src/lib/components/ThemeSwitcher.svelte` - Theme selection component

### Recipe Components
- `/home/user/recipe-catalog/frontend/src/lib/components/RecipeCard.svelte` - Grid view recipe card
- `/home/user/recipe-catalog/frontend/src/lib/components/RecipeListItem.svelte` - List view recipe item
- `/home/user/recipe-catalog/frontend/src/lib/components/RecipeForm.svelte` - Create/edit recipe form
- `/home/user/recipe-catalog/frontend/src/lib/components/recipe/IngredientsEditor.svelte` - Ingredient editor
- `/home/user/recipe-catalog/frontend/src/lib/components/recipe/InstructionsEditor.svelte` - Instructions editor

### Collection Components
- `/home/user/recipe-catalog/frontend/src/lib/components/CollectionModal.svelte` - Create/edit collection modal

### Settings Components
- `/home/user/recipe-catalog/frontend/src/lib/components/settings/ProfileSection.svelte` - Profile settings
- `/home/user/recipe-catalog/frontend/src/lib/components/settings/PreferencesSection.svelte` - Theme & preferences
- `/home/user/recipe-catalog/frontend/src/lib/components/settings/SecuritySection.svelte` - Security settings
- `/home/user/recipe-catalog/frontend/src/lib/components/settings/StatsSection.svelte` - Statistics display
- `/home/user/recipe-catalog/frontend/src/lib/components/settings/DangerZoneSection.svelte` - Delete account

### Export Components
- `/home/user/recipe-catalog/frontend/src/lib/components/export/ExportCard.svelte` - Export options

### Page Routes
- `/home/user/recipe-catalog/frontend/src/routes/+layout.svelte` - Root layout (empty)
- `/home/user/recipe-catalog/frontend/src/routes/+page.svelte` - Landing page (unauthenticated)
- `/home/user/recipe-catalog/frontend/src/routes/dashboard/+page.svelte` - Dashboard page
- `/home/user/recipe-catalog/frontend/src/routes/recipes/+page.svelte` - Recipes list page
- `/home/user/recipe-catalog/frontend/src/routes/recipes/[id]/+page.svelte` - Recipe detail page (NO NAVBAR)
- `/home/user/recipe-catalog/frontend/src/routes/recipes/[id]/edit/+page.svelte` - Recipe edit page
- `/home/user/recipe-catalog/frontend/src/routes/recipes/new/+page.svelte` - Create recipe page
- `/home/user/recipe-catalog/frontend/src/routes/recipes/trash/+page.svelte` - Trash page
- `/home/user/recipe-catalog/frontend/src/routes/collections/[id]/+page.svelte` - Collection detail (NO NAVBAR)
- `/home/user/recipe-catalog/frontend/src/routes/settings/+page.svelte` - Settings page (NO NAVBAR)
- `/home/user/recipe-catalog/frontend/src/routes/import/+page.svelte` - Import page
- `/home/user/recipe-catalog/frontend/src/routes/export/+page.svelte` - Export page
- `/home/user/recipe-catalog/frontend/src/routes/auth/login/+page.svelte` - Login page
- `/home/user/recipe-catalog/frontend/src/routes/auth/register/+page.svelte` - Register page

### Issue Documentation
- `/home/user/recipe-catalog/docs/issues/issues to be fixed.md` - UI/UX issues list

---

## COMPONENT RELATIONSHIP DIAGRAM

```
Landing Page (+page.svelte)
├── Custom Navbar
│   ├── Sign In / Sign Up links
│   └── Theme Toggle Button (🎨/💼) ← ONLY HERE
└── Theme Logic (localStorage)

Authenticated Pages
├── Dashboard (/dashboard/+page.svelte)
│   └── Custom inline navbar (NO Navbar import)
│
├── Recipes List (/recipes/+page.svelte)
│   ├── Navbar.svelte ✓
│   ├── FilterSidebar
│   │   └── Hardcoded cuisines & categories
│   ├── RecipeCard (grid)
│   └── RecipeListItem (list)
│
├── Recipe Detail (/recipes/[id]/+page.svelte)
│   ├── NO NAVBAR ✗ (Issue #1)
│   └── No navigation back
│
├── Collections Detail (/collections/[id]/+page.svelte)
│   ├── NO NAVBAR ✗
│   └── RecipeCard (grid)
│
├── Settings (/settings/+page.svelte)
│   ├── NO NAVBAR ✗ (Issue #2)
│   ├── Settings Sidebar (Profile, Preferences, Security, Stats, Danger)
│   ├── ProfileSection
│   ├── PreferencesSection
│   │   └── ThemeSwitcher (saves to DB)
│   ├── SecuritySection
│   ├── StatsSection
│   └── DangerZoneSection (Delete Account not fully implemented)
│
├── Import (/import/+page.svelte)
│   └── Navbar.svelte ✓
│
└── Export (/export/+page.svelte)
    └── Navbar.svelte ✓

Collections Management (HIDDEN)
├── CollectionsSidebar (component exists but NOT USED)
│   ├── Collections store subscription
│   ├── Create button
│   ├── Edit/Delete actions
│   └── CollectionModal
│       ├── Create/Edit form
│       ├── Icon selector (20 emojis)
│       └── Validation
│
└── API Endpoints ✓ (All implemented but inaccessible)
    ├── GET /api/collections/
    ├── POST /api/collections/
    ├── PATCH /api/collections/{id}
    └── DELETE /api/collections/{id}
```

---

## HOW SYSTEMS WORK TOGETHER

### Authentication Flow
1. **Landing Page** (+page.svelte)
   - Unauthenticated user sees custom navbar
   - Signs in/up via Auth pages
   
2. **Auth Store** (stores/auth.ts)
   - Handles login/register/logout
   - Stores token in localStorage
   - Fetches user profile
   - Derives isAuthenticated store

3. **Authenticated Pages**
   - Check auth store on mount
   - Redirect to login if not authenticated
   - Show Navbar component (if included)

### Theme Management Flow

**Path 1: Landing Page (WORKING)**
1. Toggle button calls `toggleTheme()`
2. Saves to localStorage
3. Sets data-theme attribute on document root
4. CSS variables update based on [data-theme] selector

**Path 2: Settings Preferences (PARTIALLY WORKING)**
1. ThemeSwitcher component dispatches 'change' event
2. PreferencesSection listens and updates `form.theme`
3. `savePreferences()` calls API to save to database
4. Sets data-theme attribute on document root immediately
5. **Works but only accessible in Settings page**

**Path 3: Should Be Accessible (MISSING)**
- Theme toggle should be in Navbar for logged-in users
- Currently only available on landing page
- Settings page has it but hidden in sidebar

### Recipe Management Flow
1. **Recipe List** (/recipes/+page.svelte)
   - Calls searchRecipes() API
   - Displays RecipeCard or RecipeListItem
   - Filters via FilterSidebar (cuisines/categories hardcoded)

2. **Recipe Detail** (/recipes/[id]/+page.svelte)
   - Calls getRecipe() API
   - NO navbar - users stuck on page
   - Can edit or delete

3. **Recipe Create/Edit** (/recipes/new/ or /[id]/edit/)
   - Uses RecipeForm component
   - Includes IngredientsEditor and InstructionsEditor

### Collections Management Flow
**COMPLETE BUT HIDDEN**
1. Collections Store (stores/collections.ts)
   - Loads from API on demand
   - Maintains in-memory cache

2. Collections API (api/collections.ts)
   - CRUD endpoints fully implemented
   - Add/remove recipes to collections

3. CollectionsSidebar Component
   - FULLY FUNCTIONAL
   - Can create, edit, delete collections
   - **NEVER USED IN ANY LAYOUT**

4. CollectionModal Component
   - Form for create/edit
   - Icon picker with 20 emojis
   - **MODAL NEVER OPENED FROM ANY PAGE**

### Filter System
**HARDCODED (NO MANAGEMENT)**
1. FilterSidebar Component
   - Displays 15 cuisines (hardcoded array)
   - Displays 15 categories (hardcoded array)
   - Source type: imported/manual
   - Time presets: 15min, 30min, 1hr, 2hrs

2. Selection
   - User selects from predefined options
   - Emits 'change' event with selections
   - Parent page calls searchRecipes() with filters

3. **PROBLEM**
   - No way to add custom cuisines
   - No way to add custom categories
   - Hardcoded in component, not from API
   - No backend API for management visible in frontend

---

## DATA FLOW EXAMPLES

### Example 1: User Changes Theme in Settings
```
User clicks theme card
  ↓
ThemeSwitcher.svelte dispatches 'change' event with theme ID
  ↓
PreferencesSection listens: handleThemeChange()
  ↓
Updates form.theme
  ↓
Calls savePreferences()
  ↓
updatePreferences() API call → PATCH /api/users/me/preferences
  ↓
Dispatch 'update' event (updates parent state)
  ↓
document.documentElement.setAttribute('data-theme', form.theme)
  ↓
CSS variables update → visual change
```

### Example 2: User Views Recipe (Current - Broken)
```
User clicks recipe card
  ↓
RecipeCard dispatches 'view' event
  ↓
Recipes list page calls goto('/recipes/123')
  ↓
Recipe detail page (NO NAVBAR)
  ↓
User stuck - no way to navigate back
  ↓
Must use browser back button
```

### Example 3: User Wants to Create Collection (Hidden)
```
User needs to create collection
  ↓
No menu item in navbar
  ↓
No sidebar visible
  ↓
CollectionModal never opens
  ↓
CollectionsSidebar never imported/used
  ↓
Collection API inaccessible to users
```

### Example 4: User Wants Custom Cuisine (Impossible)
```
User wants to add "Vietnamese" as custom cuisine
  ↓
FilterSidebar has hardcoded list only
  ↓
No "add" or "edit" option
  ↓
No API endpoint visible in frontend
  ↓
User stuck with 15 predefined options
```

---

## CSS VARIABLE STRUCTURE

### Root Defines (apply to all themes)
```css
:root {
  --color-success, --color-error, --color-warning, --color-info
  --shadow-sm, --shadow-md, --shadow-lg, --shadow-xl
  --font-sans, --font-display
  --space-xs to --space-3xl
  --radius-sm, --radius-md, --radius-lg, --radius-xl, --radius-full
  --transition-fast, --transition-base, --transition-slow
}
```

### Theme-Specific (one per theme)
```css
[data-theme="classic"] {
  --primary-50 to --primary-900
  --accent-50 to --accent-900
  --neutral-white, --neutral-50 to --neutral-900
  --text-900, --text-600, --text-500
  
  /* Semantic colors that depend on theme */
  --color-navbar-bg: var(--primary-500)
  --color-navbar-text: var(--neutral-white)
  --color-sidebar-bg: var(--neutral-50)
  --color-sidebar-active-bg: var(--accent-100)
  --color-sidebar-active-text: var(--accent-800)
  --color-btn-primary-bg: var(--accent-500)
  --color-btn-primary-text: var(--neutral-white)
  --color-btn-secondary-bg: var(--neutral-100)
  --color-btn-secondary-text: var(--primary-500)
}

[data-theme="professional"] {
  /* Same structure, different colors */
}
```

### How Components Use Them
```svelte
<nav style="background: var(--color-navbar-bg); color: var(--color-navbar-text);">
<div style="color: var(--text-900);">
<button class="btn btn-primary"> <!-- Uses CSS variable in Tailwind -->
```

---

## IDENTIFIED ISSUES & FIX LOCATIONS

| Issue | Location | Fix |
|-------|----------|-----|
| No navbar on recipe detail | `/recipes/[id]/+page.svelte` | Import Navbar, add to template |
| No navbar on settings | `/settings/+page.svelte` | Import Navbar, add to template |
| No navbar on collection detail | `/collections/[id]/+page.svelte` | Import Navbar, add to template |
| Navbar text inconsistent | Check CSS variable usage | Ensure both use same variables |
| Theme toggle missing after login | N/A (by design in navbar) | Add theme button to Navbar component |
| Collections hidden | CollectionsSidebar not used | Integrate into layout or create new UI |
| Delete Account not working | `/settings/+page.svelte` | Verify DangerZoneSection implementation |
| Hardcoded cuisines/categories | `/FilterSidebar.svelte` | Fetch from API or allow custom entry |

---

## KEY INSIGHTS FOR FIXING UI/UX

1. **Copy-Paste Navbar Pattern**
   - Most authenticated pages don't use Navbar component
   - Dashboard creates custom inline navbar
   - Should be consistent - use Navbar.svelte everywhere

2. **CollectionsSidebar Is Complete But Hidden**
   - Component is fully functional
   - Store is set up and working
   - API calls work
   - Just needs to be used in a layout
   - Options:
     a. Create a two-column layout for recipes (FilterSidebar on left, CollectionsSidebar above/below)
     b. Add collections list to sidebar in main layout
     c. Add collections menu to Navbar

3. **Theme System Is Properly Designed**
   - CSS variables correctly set up for both themes
   - localStorage persistence works
   - Database persistence works
   - Only missing: theme button in logged-in navbar

4. **Cuisines/Categories Are Hardcoded**
   - Not in database (as far as visible in frontend)
   - Need backend API to fetch available options
   - Or allow free-text entry with suggestions
   - Currently fixed set of 15 each

5. **Settings Page Is Well-Structured**
   - Sidebar navigation pattern good
   - All sections have proper components
   - Delete account just needs implementation verification

---

## RECOMMENDED FIX PRIORITY

**HIGH PRIORITY (Breaks Navigation)**
1. Add Navbar to recipe detail page
2. Add Navbar to settings page
3. Add Navbar to collection detail page

**MEDIUM PRIORITY (UX Consistency)**
4. Add theme toggle to Navbar component
5. Integrate collections sidebar somewhere accessible
6. Verify/implement delete account functionality

**LOW PRIORITY (Data Management)**
7. Add custom cuisine management
8. Add custom category management
9. Synchronize default view preference

