# Frontend Improvement Tasks - Recipe Catalog
**Date:** 2025-11-26
**Based on:** Frontend Assessment (assess-frontend-2025-11-26.md)
**Target:** Mid-level developer implementation

---

## Overview

This task list addresses the issues identified in the frontend assessment. Tasks are organized by priority and designed for straightforward implementation without overengineering.

**Total Estimated Effort:** ~40-50 hours across all priorities

---

## 🔥 High Priority Tasks (Weeks 1-2)

### Task 1: Replace alert() and confirm() with Modal Components
**Priority:** Critical | **Effort:** 4-6 hours

**Goal:** Remove all native browser dialogs and replace with custom modal components.

**Implementation:**
1. Create `src/lib/components/ConfirmDialog.svelte`:
   - Simple modal with title, message, confirm/cancel buttons
   - Props: `open`, `title`, `message`, `onConfirm`, `onCancel`
   - Use dialog element for accessibility
   - Tailwind styling to match theme

2. Create `src/lib/stores/dialog.ts`:
   ```typescript
   // Simple dialog store
   export const dialog = writable<{
     open: boolean;
     title: string;
     message: string;
     onConfirm: () => void;
   } | null>(null);
   ```

3. Add `<ConfirmDialog>` to `routes/+layout.svelte`

4. Replace all `confirm()` calls (17 files) with:
   ```typescript
   dialog.show({
     title: 'Delete Recipe',
     message: `Are you sure you want to delete "${recipe.name}"?`,
     onConfirm: () => deleteRecipe(recipe.id)
   });
   ```

**Files to update:**
- `routes/recipes/+page.svelte:104`
- `routes/collections/[id]/+page.svelte`
- `lib/components/CollectionsSidebar.svelte:55,67,71`
- Search codebase for all `confirm(` and `alert(` calls

---

### Task 2: Add Toast Notification System
**Priority:** Critical | **Effort:** 3-4 hours

**Goal:** Replace alert() messages with non-blocking toast notifications.

**Implementation:**
1. Create `src/lib/components/Toast.svelte`:
   - Fixed position (top-right or bottom-right)
   - Auto-dismiss after 3-5 seconds
   - Support types: success, error, info, warning
   - Simple fade in/out animation

2. Create `src/lib/stores/toast.ts`:
   ```typescript
   export const toast = {
     success: (message: string) => { /* ... */ },
     error: (message: string) => { /* ... */ },
     info: (message: string) => { /* ... */ }
   };
   ```

3. Add `<Toast>` to `routes/+layout.svelte`

4. Replace error alerts:
   ```typescript
   // Before: alert('Failed to delete recipe');
   // After: toast.error('Failed to delete recipe');
   ```

**Usage Examples:**
- Success: "Recipe deleted successfully"
- Error: "Failed to save recipe. Please try again."
- Info: "Changes saved"

---

### Task 3: Create Logger Utility and Remove Console Logs
**Priority:** Critical | **Effort:** 2-3 hours

**Goal:** Remove production console.log() calls and add proper dev-only logging.

**Implementation:**
1. Create `src/lib/utils/logger.ts`:
   ```typescript
   import { dev } from '$app/environment';

   export const logger = {
     debug: (...args: any[]) => {
       if (dev) console.log('[DEBUG]', ...args);
     },
     error: (...args: any[]) => {
       if (dev) console.error('[ERROR]', ...args);
       // TODO: Add error tracking service in production
     },
     warn: (...args: any[]) => {
       if (dev) console.warn('[WARN]', ...args);
     }
   };
   ```

2. Find and replace in 20+ files:
   ```typescript
   // Before: console.log('Favorite:', recipe);
   // After: logger.debug('Favorite:', recipe);

   // Before: console.error('Failed:', err);
   // After: logger.error('Failed:', err);
   ```

3. Use toast for user-facing errors instead of logging

**Files to update:** Search codebase for `console.log`, `console.error`, `console.warn`

---

### Task 4: Fix Type Safety Issues
**Priority:** Critical | **Effort:** 4-6 hours

**Goal:** Remove `any` types and create proper type definitions.

**Implementation:**
1. Create `src/lib/types/index.ts`:
   ```typescript
   // User types
   export interface User {
     id: string;
     email: string;
     username: string;
     // ... other fields
   }

   // Recipe types (move from api/recipes.ts)
   export interface RecipeData {
     // Schema.org Recipe format
     "@context": "https://schema.org";
     "@type": "Recipe";
     name: string;
     description?: string;
     recipeIngredient?: string[];
     recipeInstructions?: string;
     prepTime?: string;
     cookTime?: string;
     // ... other Schema.org fields
   }

   export interface Recipe {
     id: string;
     name: string;
     recipe_data: RecipeData; // ✓ Typed instead of any
     // ... other fields
   }
   ```

2. Fix specific files:
   - `components/Navbar.svelte:7`: Change `let user: any` to `let user: User | null`
   - `routes/recipes/+page.svelte:77`: Remove `as any` cast, use proper enum
   - `lib/api/recipes.ts:13`: Type `recipe_data` as `RecipeData`

3. Verify with TypeScript:
   ```bash
   npm run check
   ```

**Success criteria:** Zero `any` types in codebase (excluding tests)

---

### Task 5: Add Loading States to Async Operations
**Priority:** Critical | **Effort:** 3-4 hours

**Goal:** Show loading indicators during async operations.

**Implementation:**
1. Create `src/lib/components/Button.svelte`:
   ```svelte
   <script lang="ts">
     export let loading = false;
     export let disabled = false;
     export let type: 'button' | 'submit' = 'button';
   </script>

   <button
     {type}
     disabled={loading || disabled}
     class={$$props.class}
   >
     {#if loading}
       <span class="spinner"></span>
     {/if}
     <slot />
   </button>
   ```

2. Add loading state to delete operations:
   ```typescript
   let deleting = false;

   async function handleDelete() {
     deleting = true;
     try {
       await deleteRecipe(recipe.id);
       toast.success('Recipe deleted');
     } catch (err) {
       toast.error('Failed to delete recipe');
     } finally {
       deleting = false;
     }
   }
   ```

3. Update these files:
   - `CollectionsSidebar.svelte:72-74` - delete operations
   - `RecipeForm.svelte` - save/submit buttons
   - `recipes/+page.svelte` - delete/favorite actions

4. Add simple CSS spinner:
   ```css
   .spinner {
     display: inline-block;
     width: 1rem;
     height: 1rem;
     border: 2px solid currentColor;
     border-right-color: transparent;
     border-radius: 50%;
     animation: spin 0.6s linear infinite;
   }
   ```

---

### Task 6: Fix localStorage Browser Check
**Priority:** High | **Effort:** 1 hour

**Goal:** Prevent SSR crashes from localStorage usage.

**Implementation:**
1. Find all `localStorage` usage (grep for it)

2. Wrap with browser check:
   ```typescript
   import { browser } from '$app/environment';

   // Before:
   const savedViewMode = localStorage.getItem('recipe-view-mode');

   // After:
   const savedViewMode = browser
     ? localStorage.getItem('recipe-view-mode')
     : null;
   ```

3. Files to fix:
   - `routes/recipes/+page.svelte:143`
   - Any other localStorage calls

**Test:** Run `npm run build` to verify SSR works

---

## 📊 Medium Priority Tasks (Weeks 3-4)

### Task 7: Implement or Remove Favorites Feature
**Priority:** Medium | **Effort:** 6-8 hours (implement) OR 1 hour (remove)

**Option A: Implement (recommended if backend supports it)**
1. Check if backend has favorites endpoint
2. Create `lib/api/favorites.ts`:
   ```typescript
   export async function addFavorite(recipeId: string): Promise<void>
   export async function removeFavorite(recipeId: string): Promise<void>
   export async function getFavorites(): Promise<RecipeSummary[]>
   ```
3. Update `RecipeCard.svelte` to call API on favorite click
4. Add visual feedback (filled/unfilled heart)
5. Update stores if needed

**Option B: Remove (if no backend support)**
1. Remove favorite button from `RecipeCard.svelte`
2. Remove `handleFavoriteRecipe` from `routes/recipes/+page.svelte:116-120`
3. Remove any favorite-related UI

**Decision:** Check with backend team first

---

### Task 8: Replace Emojis with Icon Library
**Priority:** Medium | **Effort:** 4-6 hours

**Goal:** Replace emojis with accessible SVG icons.

**Implementation:**
1. Install icon library:
   ```bash
   npm install lucide-svelte
   ```

2. Create icon mapping:
   - 🍽️ → `UtensilsCrossed`
   - 🕐 → `Clock`
   - 🎨 → `Palette`
   - 💼 → `Briefcase`
   - ⭐ → `Star`

3. Replace in components:
   ```svelte
   <!-- Before -->
   <span>🕐</span>

   <!-- After -->
   <Clock size={16} aria-label="Preparation time" />
   ```

4. Files to update:
   - `Navbar.svelte:53,103`
   - `RecipeCard.svelte:79`
   - Search for emoji usage across codebase

5. Add aria-labels to all icons for accessibility

---

### Task 9: Improve Error Handling Consistency
**Priority:** Medium | **Effort:** 3-4 hours

**Goal:** Consistent error handling patterns across the app.

**Implementation:**
1. Create error handling utility `src/lib/utils/errors.ts`:
   ```typescript
   import { toast } from '$lib/stores/toast';
   import { logger } from './logger';

   export function handleError(error: unknown, userMessage?: string) {
     logger.error(error);
     const message = userMessage || 'An error occurred. Please try again.';
     toast.error(message);
   }
   ```

2. Standardize async error handling:
   ```typescript
   try {
     await someAsyncOperation();
     toast.success('Operation completed');
   } catch (err) {
     handleError(err, 'Failed to complete operation');
   }
   ```

3. Fix silent error swallowing:
   - `Navbar.svelte:21-23` - Don't silently catch preference errors
   - `lib/stores/auth.ts:134` - Log logout errors

4. Replace inline error handling with utility

---

### Task 10: Add Basic Accessibility Improvements
**Priority:** Medium | **Effort:** 4-6 hours

**Goal:** Improve accessibility for screen readers and keyboard users.

**Implementation:**
1. Add ARIA labels to icon buttons:
   ```svelte
   <button aria-label="Delete recipe">
     <Trash2 size={16} />
   </button>
   ```

2. Add form field error announcements:
   ```svelte
   <input
     aria-invalid={!!error}
     aria-describedby={error ? 'error-message' : undefined}
   />
   {#if error}
     <span id="error-message" role="alert">{error}</span>
   {/if}
   ```

3. Add keyboard focus management to modals:
   ```typescript
   // In ConfirmDialog.svelte
   onMount(() => {
     const firstButton = dialog.querySelector('button');
     firstButton?.focus();
   });
   ```

4. Test keyboard navigation:
   - Tab through forms
   - Enter/Escape to confirm/cancel dialogs
   - Arrow keys for lists (if applicable)

**Files to update:**
- All components with icon-only buttons
- All form inputs
- ConfirmDialog component

---

### Task 11: Extract Magic Numbers to Constants
**Priority:** Medium | **Effort:** 2 hours

**Goal:** Make configuration values explicit and maintainable.

**Implementation:**
1. Create `src/lib/constants.ts`:
   ```typescript
   // Pagination
   export const DEFAULT_PAGE_SIZE = 24;
   export const DEFAULT_PAGE = 1;

   // API
   export const REQUEST_TIMEOUT = 30000; // 30s
   export const FETCH_CREDENTIALS = 'include' as const;

   // UI
   export const TOAST_DURATION = 5000; // 5s
   export const DEBOUNCE_DELAY = 300; // 300ms
   ```

2. Replace magic numbers:
   - `routes/recipes/+page.svelte:27` - Use `DEFAULT_PAGE_SIZE`
   - `lib/api/client.ts:204` - Use `FETCH_CREDENTIALS`

3. Document why each constant has its value (comment in constants.ts)

---

## 🔧 Low Priority Tasks (Future)

### Task 12: Improve Component Props Naming
**Priority:** Low | **Effort:** 2 hours

**Goal:** Use consistent camelCase naming for component props.

**Implementation:**
1. Update `RecipeCard.svelte:6-9`:
   ```typescript
   // Before:
   export let onview: ((recipe: RecipeSummary) => void) | undefined;
   export let onedit: ((recipe: RecipeSummary) => void) | undefined;

   // After:
   export let onView: ((recipe: RecipeSummary) => void) | undefined;
   export let onEdit: ((recipe: RecipeSummary) => void) | undefined;
   ```

2. Update all usages of these props

3. Search for other lowercase prop names and fix

---

### Task 13: Clean Up API Client
**Priority:** Low | **Effort:** 1 hour

**Goal:** Simplify and clean up API client code.

**Implementation:**
1. Remove redundant variable in `lib/api/client.ts:8`:
   ```typescript
   // Before:
   const API_URL = API_V1_URL;
   const url = `${API_URL}${endpoint}`;

   // After:
   const url = `${API_V1_URL}${endpoint}`;
   ```

2. No other changes needed - client is well-implemented

---

### Task 14: Simplify Vite Proxy Config
**Priority:** Low | **Effort:** 30 minutes

**Goal:** Clean up proxy configuration.

**Implementation:**
1. Update `vite.config.ts:10`:
   ```typescript
   // Before:
   "^/api/.*": {
     target: "http://localhost:8000",
     rewrite: (path) => path,  // No-op
   }

   // After:
   '/api': {
     target: 'http://localhost:8000',
     changeOrigin: true,
   }
   ```

2. Test that API calls still work in development

---

### Task 15: Extract Inline Styles to Classes
**Priority:** Low | **Effort:** 2-3 hours

**Goal:** Reduce repeated inline styles.

**Implementation:**
1. Identify repeated inline styles:
   ```svelte
   <!-- Common pattern -->
   <div style="background: var(--color-navbar-bg); color: var(--color-navbar-text);">
   ```

2. Create utility classes in `app.css`:
   ```css
   .navbar-themed {
     background: var(--color-navbar-bg);
     color: var(--color-navbar-text);
   }
   ```

3. Replace inline styles with classes

**Note:** Only do this for truly repeated patterns. Don't over-engineer.

---

### Task 16: Remove TODOs and Commented Code
**Priority:** Low | **Effort:** 1 hour

**Goal:** Clean up TODO comments.

**Implementation:**
1. Find all TODO comments (grep for "TODO")

2. For each TODO, either:
   - Implement the feature (if simple)
   - Create a GitHub issue (if complex)
   - Remove the comment (if no longer relevant)

3. Remove commented-out code

**Files:**
- `RecipeForm.svelte:169` - Auto-save feature
- `routes/recipes/+page.svelte:119` - Favorites
- Any others found

---

## 📋 Testing Tasks (Ongoing)

### Task 17: Increase Test Coverage
**Priority:** Medium | **Effort:** 16-24 hours (spread over time)

**Goal:** Achieve 60%+ test coverage.

**Strategy:** Write tests as you fix issues, not all at once.

**Priority components to test:**
1. ConfirmDialog and Toast (new components from tasks above)
2. Button component with loading state
3. Auth flows (expand existing tests)
4. RecipeForm validation
5. CollectionsSidebar operations

**For each component test:**
- Render without errors
- User interactions work
- Loading states display correctly
- Error states display correctly
- Accessibility (aria attributes present)

**Example test:**
```typescript
import { render, fireEvent } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import ConfirmDialog from './ConfirmDialog.svelte';

describe('ConfirmDialog', () => {
  it('calls onConfirm when confirm button clicked', async () => {
    let confirmed = false;
    const { getByText } = render(ConfirmDialog, {
      open: true,
      title: 'Test',
      message: 'Are you sure?',
      onConfirm: () => { confirmed = true; }
    });

    await fireEvent.click(getByText('Confirm'));
    expect(confirmed).toBe(true);
  });
});
```

---

## 🎯 Implementation Order (Recommended)

### Week 1
1. Task 1: ConfirmDialog (replaces confirm/alert)
2. Task 2: Toast notifications
3. Task 3: Logger utility
4. Task 6: localStorage fixes

### Week 2
5. Task 4: Type safety fixes
6. Task 5: Loading states
7. Task 11: Extract constants

### Week 3
8. Task 9: Error handling consistency
9. Task 7: Favorites (implement or remove)
10. Task 8: Replace emojis with icons

### Week 4
11. Task 10: Accessibility improvements
12. Task 17: Write tests for new components
13. Lower priority cleanup tasks

---

## 📏 Success Criteria

After completing high-priority tasks, you should have:

- ✅ Zero uses of `alert()` or `confirm()`
- ✅ Zero console.log in production
- ✅ Zero `any` types (excluding test files)
- ✅ All async operations show loading state
- ✅ Toast notifications for user feedback
- ✅ No SSR crashes from localStorage
- ✅ Custom modal dialogs that match app theme
- ✅ Type-safe codebase (passes `npm run check`)

---

## 🛠️ Development Tips

1. **Test as you go:** Run `npm run dev` frequently to verify changes
2. **TypeScript first:** Fix type errors before moving to next task
3. **Small commits:** Commit after each task completion
4. **Keep it simple:** Don't over-engineer solutions
5. **Ask for help:** If a task takes >2x estimated time, ask for guidance

---

## 📚 Resources

- **SvelteKit Docs:** https://kit.svelte.dev/docs
- **TypeScript Handbook:** https://www.typescriptlang.org/docs
- **Lucide Icons:** https://lucide.dev/
- **Vitest:** https://vitest.dev/
- **ARIA Practices:** https://www.w3.org/WAI/ARIA/apg/

---

**Task list created:** 2025-11-26
**Based on assessment:** assess-frontend-2025-11-26.md
**Ready for implementation:** Yes ✓
