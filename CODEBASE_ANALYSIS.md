# Recipe Catalog - Codebase Structure & UI/UX Analysis

## Project Overview
- **Framework**: SvelteKit (TypeScript)
- **Styling**: Tailwind CSS with custom CSS variables for theming
- **State Management**: Svelte stores (auth, collections)
- **API Client**: Custom fetch-based client with bearer token auth

---

## 1. NAVIGATION COMPONENTS

### Main Navigation Component
**File**: `/home/user/recipe-catalog/frontend/src/lib/components/Navbar.svelte`
- Sticky navbar (z-50, top-0)
- Shows logo "🍽️ Recipe Catalog" with link to /dashboard
- Navigation links: Dashboard, Recipes, Export, Settings
- Shows user email and Logout button
- Uses CSS variables for styling: `--color-navbar-bg`, `--color-navbar-text`
- Subscribes to auth store to display user info
- **ISSUE #1**: Navigation bar is NOT appearing on recipe detail pages (/recipes/[id])
- **ISSUE #2**: Navigation bar is NOT appearing on settings page

### Landing Page Navigation
**File**: `/home/user/recipe-catalog/frontend/src/routes/+page.svelte`
- Custom inline navbar for unauthenticated users
- Links: Sign In, Sign Up
- **Has theme toggle button** (🎨/💼 icon) that toggles between 'classic' and 'professional'
- **ISSUE #3**: Theme toggle button ONLY available on landing page, disappears after login

### Navigation Component Usage
- **Navbar.svelte** is imported in:
  - `/recipes/+page.svelte`
  - `/import/+page.svelte`
  - `/export/+page.svelte`
- **NOT imported in**:
  - `/recipes/[id]/+page.svelte` (recipe detail)
  - `/settings/+page.svelte`
  - `/collections/[id]/+page.svelte`
  - These pages have inline navbar or no navbar at all

### Collections Sidebar Navigation
**File**: `/home/user/recipe-catalog/frontend/src/lib/components/CollectionsSidebar.svelte`
- 260px wide sidebar with collections list
- Sections: "Quick Access" (All Recipes, Default collections), "My Collections", "Trash"
- Features:
  - Create new collection button
  - Edit/Delete actions for custom collections
  - Recipe count badges
  - Active state highlighting with left border
  - Full-height sidebar (100vh)
- **ISSUE #4**: No apparent way to add/edit collections from UI despite component existing
- **STATUS**: Component exists but NOT USED in any page layout

---

## 2. ROUTING STRUCTURE & PAGE LAYOUT

### Route Directory Structure
```
/src/routes/
├── +layout.svelte (empty root layout - only <slot />)
├── +page.svelte (landing page, unauthenticated)
├── auth/
│   ├── login/
│   ├── register/
│   ├── forgot-password/
│   ├── reset-password/[token]/
│   └── verify-email/[token]/
├── dashboard/ (authenticated, has Navbar)
├── recipes/
│   ├── +page.svelte (list view, has Navbar)
│   ├── [id]/
│   │   ├── +page.svelte (detail view, NO NAVBAR)
│   │   └── edit/+page.svelte (edit view)
│   ├── new/ (create new)
│   └── trash/
├── collections/[id]/ (detail view, NO NAVBAR)
├── settings/ (NO NAVBAR)
├── import/ (has Navbar)
└── export/ (has Navbar)
```

### Page Component Patterns

#### Pages WITH Navbar
1. **Dashboard** (`/dashboard/+page.svelte`)
   - Custom inline navbar
   - Welcome message, stats cards
   - Quick action buttons
   - Auth guard (redirects to login if not authenticated)

2. **Recipes List** (`/recipes/+page.svelte`)
   - Imports Navbar component
   - Sticky search/sort header
   - Filter sidebar (CollectionsSidebar NOT used here, FilterSidebar is)
   - Grid/List view toggle
   - Uses FilterSidebar component for cuisine/category/source type filters
   - Recipe pagination

3. **Import/Export Pages**
   - Both import Navbar component
   - File upload/download functionality

#### Pages WITHOUT Navbar (ISSUE)
1. **Recipe Detail** (`/recipes/[id]/+page.svelte`)
   - Shows full recipe view
   - Ingredient checklist functionality
   - Export recipe options
   - NO navbar at all

2. **Settings** (`/settings/+page.svelte`)
   - Sidebar navigation (5 sections)
   - NO navbar component
   - Sections: Profile, Preferences, Security, Statistics, Danger Zone

3. **Collections Detail** (`/collections/[id]/+page.svelte`)
   - Shows collection recipes in grid/list
   - NO navbar component

---

## 3. THEME IMPLEMENTATION

### Theme System Architecture

#### CSS Variables
**File**: `/home/user/recipe-catalog/frontend/src/app.css`
- Two complete theme palettes: `classic` and `professional`
- Applied via `[data-theme="theme-name"]` selector
- Shared semantic colors (success, error, warning, info)

#### Theme Definitions

**Theme 1: Classic Minimal (Charcoal + Saffron)**
- Primary: #3D4451 (Charcoal)
- Accent: #F59E0B (Saffron)
- Navbar: Charcoal with white text

**Theme 2: Professional Warm (Navy + Apricot)**
- Primary: #1E3A5F (Navy)
- Accent: #F97316 (Apricot)
- Navbar: Navy with white text

#### Semantic CSS Variables
```css
--primary-50 to --primary-900 (color scales)
--accent-50 to --accent-900 (accent scales)
--neutral-white, --neutral-50 to --neutral-900
--text-900, --text-600, --text-500
--color-navbar-bg, --color-navbar-text
--color-sidebar-bg, --color-sidebar-active-bg
--color-btn-primary-bg, --color-btn-secondary-bg
--shadow-sm, --shadow-md, --shadow-lg, --shadow-xl
--radius-sm, --radius-md, --radius-lg, --radius-xl, --radius-full
--transition-fast, --transition-base, --transition-slow
```

### Theme Toggle Locations

1. **Landing Page** (`/routes/+page.svelte`) ✓ WORKING
   - Button in navbar: `{theme === 'classic' ? '🎨' : '💼'}`
   - Toggles between classic and professional
   - Uses localStorage: `localStorage.getItem('theme')`
   - Sets: `document.documentElement.setAttribute('data-theme', theme)`
   - **ISSUE #3**: NOT available after login

2. **Settings Page - Preferences Section** ✓ WORKING (Component exists)
   - **File**: `/lib/components/settings/PreferencesSection.svelte`
   - Uses ThemeSwitcher component
   - Saves to backend via `updatePreferences()`
   - Applies theme immediately to DOM
   - Default view, sort, recipes per page options
   - Email notifications toggle
   - **STATUS**: Theme switcher component exists and saves to DB

3. **ThemeSwitcher Component**
   - **File**: `/lib/components/ThemeSwitcher.svelte`
   - Displays both themes with color previews
   - Dispatches 'change' event with selected theme
   - Sets: `document.documentElement.setAttribute('data-theme', themeId)`
   - **STATUS**: Component exists but only integrated into Settings page

### Theme Persistence
- **localStorage**: Used on landing page (key: `theme`)
- **Database**: UserPreferences table has `theme` field
- **On load**: Settings page applies theme from preferences on mount
- **On save**: PreferencesSection applies theme immediately

### Current Theme Issues
- **ISSUE #3**: Theme toggle removed after login (only available on landing page)
- **Workaround**: Must go to Settings > Preferences to change theme (if implemented in navbar)

---

## 4. COMPONENT STRUCTURE

### Settings Page Components
**File**: `/home/user/recipe-catalog/frontend/src/routes/settings/+page.svelte`

Layout: Two-column (250px sidebar + main content)
Active section: State variable `activeSection`

#### Settings Sections

1. **ProfileSection** (`/lib/components/settings/ProfileSection.svelte`)
   - Email field
   - Display name field
   - Save button
   - Success message feedback
   - Uses `updateProfile()` API

2. **PreferencesSection** (`/lib/components/settings/PreferencesSection.svelte`)
   - **ThemeSwitcher component** (displays both themes)
   - Default View dropdown (grid/list)
   - Default Sort dropdown (recently_added, alphabetical, time_asc, time_desc)
   - Recipes Per Page input (12-100, step 12)
   - Timezone input
   - Email notifications checkbox
   - Uses `updatePreferences()` API

3. **SecuritySection** (`/lib/components/settings/SecuritySection.svelte`)
   - Status: Component exists but content not shown in read

4. **StatsSection** (`/lib/components/settings/StatsSection.svelte`)
   - 6-column grid display:
     - Total Recipes (📖)
     - Collections (📚)
     - Recipes Imported (📥)
     - Manual Entry (✍️)
     - This Month (📅)
     - Member Since [year] (👤)
   - Read-only display

5. **DangerZoneSection** (`/lib/components/settings/DangerZoneSection.svelte`)
   - **ISSUE #8**: Delete Account button exists but not implemented
   - Dispatches 'delete' event on click
   - Settings page handles it: `handleDeleteAccount()` → `auth.logout()` → redirect to login

### Dashboard Components
**File**: `/home/user/recipe-catalog/frontend/src/routes/dashboard/+page.svelte`
- Stats cards (0 recipes, 0 favorites, 1 collection)
- Quick Actions (4 buttons):
  - Add Recipe
  - Browse Recipes
  - Import from Extension
  - Export Data
- Getting Started checklist
- Custom inline navbar

### Recipes List Components

1. **RecipeCard** (`/lib/components/RecipeCard.svelte`)
   - Image display (base64 or URL)
   - Title, description
   - Badges: cuisine, category
   - Time display (🕐)
   - Action buttons (view, edit, delete, favorite)
   - Grid layout (280px minimum)

2. **RecipeListItem** (`/lib/components/RecipeListItem.svelte`)
   - Thumbnail (80x80px)
   - Title, description
   - Metadata inline (cuisine, category, time, source)
   - Action buttons (hover-reveal)
   - List layout (flexbox row)

3. **FilterSidebar** (`/lib/components/FilterSidebar.svelte`)
   - 280px wide sidebar
   - Filter sections:
     - Cuisines (15 predefined options)
     - Categories (15 predefined options)
     - Source Type (imported/manual)
     - Time Presets (under 15min, 30min, 1hr, 2hrs)
   - Emits 'change' event on filter update
   - **ISSUE #13**: Cuisines and categories are hardcoded, no way to add/edit
   - **STATUS**: These are hardcoded lists in component, not managed anywhere

### Recipe Components

1. **RecipeForm** (`/lib/components/recipe/RecipeForm.svelte`)
   - Create/edit recipe form
   - Location: Used in `/recipes/new/+page.svelte` and `/recipes/[id]/edit/+page.svelte`

2. **IngredientsEditor** (`/lib/components/recipe/IngredientsEditor.svelte`)
   - Ingredient list management

3. **InstructionsEditor** (`/lib/components/recipe/InstructionsEditor.svelte`)
   - Instructions list management

### Collection Components

1. **CollectionModal** (`/lib/components/CollectionModal.svelte`)
   - Create/Edit collection modal
   - Fields: name (required), description, icon selector
   - 20 emoji icons to choose from
   - Form validation
   - **STATUS**: Component exists, form works, but modal never opened

2. **CollectionsSidebar** (`/lib/components/CollectionsSidebar.svelte`)
   - Full-height sidebar with collections
   - Create/edit/delete actions
   - **STATUS**: Component exists but NOT USED in any layout
   - **ISSUE #4**: Collections management UI hidden/unavailable

### Export Components
**File**: `/lib/components/export/ExportCard.svelte`
- Display format options
- Export functionality

---

## 5. COLLECTIONS, CUISINES & CATEGORIES MANAGEMENT

### Collections Management

#### API Layer
**File**: `/home/user/recipe-catalog/frontend/src/lib/api/collections.ts`

Endpoints:
- `GET /api/collections/` - List all collections
- `GET /api/collections/{id}` - Get single collection
- `POST /api/collections/` - Create collection
- `PATCH /api/collections/{id}` - Update collection
- `DELETE /api/collections/{id}` - Delete collection
- `POST /api/collections/{id}/recipes` - Add recipes to collection
- `DELETE /api/collections/{id}/recipes` - Remove recipes from collection
- `GET /api/collections/{id}/recipes` - Get collection recipes

**Data Model**:
```typescript
interface Collection {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  is_default: boolean;
  icon?: string;
  created_at: string;
  updated_at: string;
}
```

#### Collections Store
**File**: `/home/user/recipe-catalog/frontend/src/lib/stores/collections.ts`

State:
```typescript
{
  collections: CollectionWithCount[]
  loading: boolean
  loaded: boolean
  error: string | null
}
```

Methods:
- `load()` - Fetch collections from API
- `add(collection)` - Add to store
- `updateCollection(id, updates)` - Update in store
- `remove(id)` - Delete from store
- `clear()` - Clear all

#### Collections Sidebar Component
**File**: `/home/user/recipe-catalog/frontend/src/lib/components/CollectionsSidebar.svelte`
- Loads collections on mount
- Displays in two sections: "Quick Access" (default) and "My Collections" (custom)
- Edit/Delete buttons appear on hover
- Opens CollectionModal for create/edit
- Calls API: createCollection, updateCollection, deleteCollection
- Updates store on success
- **CURRENT STATUS**: Component fully functional but NEVER USED in any page layout
- **ISSUE #4**: No way to access this UI from any page

#### CollectionModal Component
**File**: `/home/user/recipe-catalog/frontend/src/lib/components/CollectionModal.svelte`
- Modal form for create/edit
- Fields: name (required, max 50), description, icon selector (20 emojis)
- Validation: name required and length
- Dispatches 'submit' or 'cancel' events
- **CURRENT STATUS**: Works perfectly but modal is never opened

### Collections Detail Page
**File**: `/home/user/recipe-catalog/frontend/src/routes/collections/[id]/+page.svelte`
- Shows single collection with its recipes
- Grid/List view toggle
- Recipe cards/list items
- NO navbar
- NO way to access collections management from this page

### Cuisines Management
**File**: `/home/user/recipe-catalog/frontend/src/lib/components/FilterSidebar.svelte`

**Hardcoded Cuisines** (15 options):
```javascript
'Italian', 'Mexican', 'Chinese', 'Japanese', 'Indian', 'Thai',
'French', 'Greek', 'Spanish', 'Mediterranean', 'American',
'Korean', 'Vietnamese', 'Middle Eastern', 'Other'
```

**ISSUE #13**: These are hardcoded in the component
- No backend API for managing cuisines
- No way for users to add/edit cuisines
- No admin interface
- Cuisines appear in:
  - Recipe model: `cuisine?: string` field
  - API: Recipe interfaces include `cuisine` field
  - FilterSidebar: Hardcoded list

### Categories Management
**File**: `/home/user/recipe-catalog/frontend/src/lib/components/FilterSidebar.svelte`

**Hardcoded Categories** (15 options):
```javascript
'Breakfast', 'Lunch', 'Dinner', 'Appetizer', 'Main Course',
'Side Dish', 'Dessert', 'Snack', 'Beverage', 'Salad', 'Soup',
'Pasta', 'Bread', 'Sauce', 'Other'
```

**ISSUE #13**: Same as cuisines - hardcoded, no management UI
- Categories appear in:
  - Recipe model: `category?: string` field
  - API: Recipe interfaces include `category` field
  - FilterSidebar: Hardcoded list
  - RecipeCard/RecipeListItem: Display categories as badges

---

## SUMMARY OF UI/UX ISSUES (from issues document)

### Critical Issues

1. **Missing Navbar on Recipe Detail Page** (/recipes/[id])
   - Location: `/recipes/[id]/+page.svelte` has no Navbar import
   - Affect: Users can't navigate away easily

2. **Missing Navbar on Settings Page** (/settings)
   - Location: `/settings/+page.svelte` has no Navbar import
   - Affect: Users can't navigate away

3. **Navbar Text Color Inconsistency**
   - Dashboard uses custom inline navbar
   - Recipes page uses Navbar component
   - Possible CSS variable mismatch

4. **Theme Toggle Only on Landing Page**
   - Removed after login
   - Settings page has theme switcher but not accessible from navbar
   - Inconsistent UX

5. **Hidden Collections Management**
   - CollectionsSidebar and CollectionModal components exist but never used
   - No way to create/edit/delete collections from UI
   - Collections API fully functional but inaccessible

6. **Delete Account Button Not Implemented**
   - DangerZoneSection has button
   - Settings page handles deletion (calls API, logs out)
   - May just need styling/visibility fix

7. **Hardcoded Cuisines & Categories**
   - FilterSidebar has 15 hardcoded options for each
   - No way to add/edit/delete custom values
   - No backend API for management
   - Not mentioned if backend supports dynamic cuisines/categories

---

## KEY FILES SUMMARY

### Store Files
- `/lib/stores/auth.ts` - Authentication state, login, register, logout
- `/lib/stores/collections.ts` - Collections management

### API Files
- `/lib/api/client.ts` - API request wrapper
- `/lib/api/auth.ts` - Not found, auth logic in store
- `/lib/api/recipes.ts` - Recipe CRUD endpoints
- `/lib/api/collections.ts` - Collections CRUD endpoints
- `/lib/api/users.ts` - User profile, preferences, stats

### Component Files (40 total)
- **Navigation**: Navbar.svelte, CollectionsSidebar.svelte
- **Layout**: FilterSidebar.svelte
- **Recipe**: RecipeCard.svelte, RecipeListItem.svelte, RecipeForm.svelte, IngredientsEditor.svelte, InstructionsEditor.svelte
- **Collections**: CollectionModal.svelte
- **Settings**: ProfileSection.svelte, PreferencesSection.svelte, SecuritySection.svelte, StatsSection.svelte, DangerZoneSection.svelte, ThemeSwitcher.svelte
- **Export**: ExportCard.svelte

### Page Files (15 total)
- Authentication: login, register, forgot-password, reset-password, verify-email
- Main app: dashboard, recipes (list/detail/edit/new), collections, settings, import, export, trash

---

## CSS & STYLING NOTES

- **Tailwind + Custom CSS**: Hybrid approach
- **CSS Variables**: Extensive use of theme variables
- **Responsive**: Mobile-first design with media queries
- **Components**: Most use scoped styles with <style> blocks
- **Colors**: All theme-aware via CSS variables
- **Transitions**: Consistent use of --transition-fast, --transition-base, --transition-slow
- **Layout patterns**: Flexbox and CSS Grid used extensively
