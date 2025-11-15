# Recipe Catalog App - Wireframes

**Version:** 1.0  
**Date:** November 14, 2025  
**Phase:** Design - Wireframes

---

## Table of Contents

1. [Wireframe Conventions](#wireframe-conventions)
2. [Main Dashboard / Recipe Listing](#main-dashboard--recipe-listing)
3. [Recipe Detail View](#recipe-detail-view)
4. [Recipe Create/Edit Form](#recipe-createedit-form)
5. [Collections Interface](#collections-interface)
6. [Import Recipes (JSON Upload)](#import-recipes-json-upload)
7. [Mobile Layouts](#mobile-layouts)
8. [Component Library](#component-library)

---

## Wireframe Conventions

```
[Button]              - Clickable button
(•) Radio            - Radio button
[x] Checkbox         - Checkbox (checked)
[ ] Checkbox         - Checkbox (unchecked)
[Dropdown ▼]         - Dropdown menu
[============]       - Text input field
[============]       - Search input
┌──────────┐
│  Image   │         - Image placeholder
└──────────┘
━━━━━━━━━━━━         - Separator/divider
[Icon]               - Icon button
```

---

## Main Dashboard / Recipe Listing

### Desktop Layout (1280px+)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  [Logo] Recipe Catalog          [==================Search==================]  [User Menu ▼] │
└────────────────────────────────────────────────────────────────────────────┘
┌──────────────┬────────────────────────────────────────────────────────────┐
│              │  My Recipes (247)                     [Grid ⊞] [List ≡]     │
│ MY RECIPES   │                                                             │
│ ├─ All (247) │  Sort: [Recently Added ▼]    Filters Active: [Italian ✕]  │
│ ├─ Favorites │                               [Under 30 min ✕] [Clear All] │
│ │   (34) ⭐   │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ └─ Trash (3) │                                                             │
│              │  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐              │
│ COLLECTIONS  │  │ ┌───┐ │  │ ┌───┐ │  │ ┌───┐ │  │ ┌───┐ │              │
│ ├─ Holiday   │  │ │IMG│ │  │ │IMG│ │  │ │IMG│ │  │ │IMG│ │              │
│ │   (23)     │  │ └───┘ │  │ └───┘ │  │ └───┘ │  │ └───┘ │              │
│ ├─ Quick     │  │       │  │       │  │       │  │       │              │
│ │   Meals    │  │Recipe │  │Recipe │  │Recipe │  │Recipe │              │
│ │   (45)     │  │Name   │  │Name   │  │Name   │  │Name   │              │
│ ├─ Desserts  │  │       │  │       │  │       │  │       │              │
│ │   (18)     │  │Italian│  │Thai   │  │Mexican│  │French │              │
│ └─ + New     │  │🕐 30min│  │🕐 45min│  │🕐 20min│  │🕐 1hr │              │
│              │  │[⭐][✎]│  │[⭐][✎]│  │[⭐][✎]│  │[⭐][✎]│              │
│ ━━━━━━━━━━━━ │  └───────┘  └───────┘  └───────┘  └───────┘              │
│              │                                                             │
│ FILTERS      │  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐              │
│              │  │ ┌───┐ │  │ ┌───┐ │  │ ┌───┐ │  │ ┌───┐ │              │
│ Cuisine      │  │ │IMG│ │  │ │IMG│ │  │ │IMG│ │  │ │IMG│ │              │
│ [x] Italian  │  │ └───┘ │  │ └───┘ │  │ └───┘ │  │ └───┘ │              │
│     (34)     │  │       │  │       │  │       │  │       │              │
│ [ ] Thai (28)│  │Recipe │  │Recipe │  │Recipe │  │Recipe │              │
│ [ ] Mexican  │  │Name   │  │Name   │  │Name   │  │Name   │              │
│     (19)     │  │       │  │       │  │       │  │       │              │
│              │  │Chinese│  │Indian │  │America│  │Japanes│              │
│ Time         │  │🕐 25min│  │🕐 50min│  │🕐 15min│  │🕐 35min│              │
│ [x] < 30 min │  │[⭐][✎]│  │[⭐][✎]│  │[⭐][✎]│  │[⭐][✎]│              │
│     (89)     │  └───────┘  └───────┘  └───────┘  └───────┘              │
│ [ ] 30-60min │                                                             │
│     (112)    │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│              │  Showing 1-24 of 34 recipes  [1] 2 3 4 [Next →]           │
│ Category     │                                                             │
│ [ ] Breakfast│                                                             │
│ [ ] Dinner   │                                                             │
│ [ ] Dessert  │                                                             │
│              │                                                             │
│ ━━━━━━━━━━━━ │                                                             │
│              │                                                             │
│ ACTIONS      │                                                             │
│ [+ Add       │                                                             │
│   Recipe]    │                                                             │
│              │                                                             │
│ [📤 Upload   │                                                             │
│   JSON]      │                                                             │
│              │                                                             │
│ [📤 Export   │                                                             │
│   Data]      │                                                             │
└──────────────┴────────────────────────────────────────────────────────────┘
```

### List View Variant

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Sort: [Recently Added ▼]                           [Grid ⊞] [List ≡]     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  ┌────┐  Thai Basil Chicken                    🕐 45min  Thai   [⭐][✎][🗑] │
│  │IMG │  Quick weeknight dinner with authentic flavors                     │
│  └────┘  Imported from thaitable.com                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  ┌────┐  Grandma's Apple Pie                   🕐 2hr    American [⭐][✎][🗑]│
│  │IMG │  Family recipe passed down three generations                       │
│  └────┘  Personal Recipe                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  ┌────┐  Quick Pasta Carbonara                 🕐 20min  Italian  [⭐][✎][🗑]│
│  │IMG │  Authentic Roman recipe, simple and delicious                      │
│  └────┘  Imported from seriouseats.com                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Empty State (New User)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                              🍳                                             │
│                                                                             │
│                   Your Recipe Collection Awaits                            │
│                                                                             │
│            Start building your personal recipe library today               │
│                                                                             │
│                                                                             │
│                    [+ Add Recipe Manually]                                 │
│                                                                             │
│                    [📤 Upload JSON Files]                                  │
│                                                                             │
│                    [🔌 Install Browser Extension]                          │
│                                                                             │
│                                                                             │
│                          ━━━ OR ━━━                                       │
│                                                                             │
│                    Watch our quick tutorial  ▶️                            │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Recipe Detail View

### Desktop Layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Recipes                                        [User Menu ▼]    │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │                         HERO IMAGE                                 │   │
│  │                      (1200px x 600px)                              │   │
│  │                                                                     │   │
│  │                         [🔍 View Full Size]                         │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  Thai Basil Chicken (Pad Krapow Gai)                              [⭐]     │
│  ═══════════════════════════════════════════                               │
│                                                                             │
│  Source: thaitable.com ↗                            [Edit] [Duplicate]     │
│  Published: March 15, 2024                          [Delete] [Print]       │
│  Imported • Last modified: Nov 10, 2025             [Add to Collection ▼]  │
│                                                                             │
│  Quick weeknight dinner with authentic Thai flavors. This popular street   │
│  food dish comes together in under an hour.                                │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐           │
│  │   Prep Time  │   Cook Time  │  Total Time  │     Yield    │           │
│  │    15 min    │    30 min    │    45 min    │  4 servings  │           │
│  └──────────────┴──────────────┴──────────────┴──────────────┘           │
│                                                                             │
│  Cuisine: Thai        Category: Main Dish       Collections: [Quick Meals] │
│                                                                [Asian]     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  ┌─────────────────────────────┬─────────────────────────────────────┐   │
│  │  INGREDIENTS                │  INSTRUCTIONS                        │   │
│  │                             │                                      │   │
│  │  [ ] 1 lb chicken breast,   │  1. Heat oil in wok over high heat  │   │
│  │      cut into bite-sized    │                                      │   │
│  │      pieces                 │  2. Add garlic and chilies, stir-   │   │
│  │                             │     fry for 30 seconds until        │   │
│  │  [ ] 3 tbsp vegetable oil   │     fragrant                        │   │
│  │                             │                                      │   │
│  │  [ ] 4 cloves garlic,       │  3. Add chicken and cook until      │   │
│  │      minced                 │     no longer pink, about 5-7       │   │
│  │                             │     minutes                          │   │
│  │  [ ] 2-3 Thai bird chilies, │                                      │   │
│  │      sliced                 │  4. Add green beans and stir-fry    │   │
│  │                             │     for 2-3 minutes until tender-   │   │
│  │  [ ] 1 cup Thai basil       │     crisp                           │   │
│  │      leaves                 │                                      │   │
│  │                             │  5. Add sauce mixture (soy sauce,   │   │
│  │  [ ] 2 tbsp soy sauce       │     fish sauce, oyster sauce,       │   │
│  │                             │     sugar) and stir to combine      │   │
│  │  [ ] 1 tbsp fish sauce      │                                      │   │
│  │                             │  6. Add Thai basil leaves and       │   │
│  │  [ ] 1 tbsp oyster sauce    │     toss until just wilted          │   │
│  │                             │                                      │   │
│  │  [ ] 1 tsp sugar            │  7. Serve immediately over          │   │
│  │                             │     jasmine rice with fried egg     │   │
│  │  [ ] 8 oz green beans       │                                      │   │
│  │                             │  [Show Less ▲]                      │   │
│  │  Serve with:                │                                      │   │
│  │  [ ] Jasmine rice           │                                      │   │
│  │  [ ] Fried egg (optional)   │                                      │   │
│  │                             │                                      │   │
│  │  [Show More ▼]              │                                      │   │
│  └─────────────────────────────┴─────────────────────────────────────┘   │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  NOTES & TIPS                                                   [Expand ▼] │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ • For authentic flavor, use Thai holy basil if available           │   │
│  │ • Adjust number of chilies based on your heat preference           │   │
│  │ • The dish should be slightly sweet, salty, and spicy              │   │
│  │ • High heat is essential for proper wok hei (breath of the wok)    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NUTRITION INFORMATION                                          [Expand ▼] │
│                                                                             │
│  EQUIPMENT                                                      [Expand ▼] │
│                                                                             │
│  TAGS                                                                       │
│  [Thai] [Spicy] [Quick] [Weeknight] [Stir-fry] [Basil]                    │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Recipe Detail (375px)

```
┌─────────────────────────────┐
│ ← Thai Basil Chicken    [⋮] │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │                         │ │
│ │      HERO IMAGE         │ │
│ │                         │ │
│ │     [🔍 Enlarge]        │ │
│ └─────────────────────────┘ │
│                             │
│ Thai Basil Chicken          │
│ (Pad Krapow Gai)       [⭐] │
│ ──────────────────────────  │
│                             │
│ Source: thaitable.com ↗     │
│ Imported • Modified         │
│                             │
│ Quick weeknight dinner with │
│ authentic Thai flavors...   │
│                             │
│ ┌────┬────┬────┬─────┐     │
│ │Prep│Cook│Total│Yield│     │
│ │15m │30m │45m │4    │     │
│ └────┴────┴────┴─────┘     │
│                             │
│ [Quick Meals] [Asian]       │
│                             │
│ ──────────────────────────  │
│                             │
│ [Ingredients] [Instructions]│
│ ═══════════                 │
│                             │
│ [ ] 1 lb chicken breast,    │
│     cut into pieces         │
│                             │
│ [ ] 3 tbsp vegetable oil    │
│                             │
│ [ ] 4 cloves garlic,        │
│     minced                  │
│                             │
│ [ ] 2-3 Thai bird chilies   │
│                             │
│ [ ] 1 cup Thai basil        │
│                             │
│ [ ] 2 tbsp soy sauce        │
│                             │
│ [Show 5 more ingredients ▼] │
│                             │
│ ──────────────────────────  │
│                             │
│ Notes & Tips        [View ▼]│
│ Nutrition          [View ▼]│
│ Equipment          [View ▼]│
│                             │
│ ──────────────────────────  │
│                             │
│ [Edit] [Add to Collection]  │
│ [Share] [Print] [Delete]    │
│                             │
└─────────────────────────────┘
```

---

## Recipe Create/Edit Form

### Desktop Layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Recipes                          Auto-saved 3 seconds ago ✓     │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Add New Recipe                                       [Save] [Cancel]      │
│  ═══════════════                                                            │
│                                                                             │
│  BASIC INFORMATION                                                          │
│  ━━━━━━━━━━━━━━━━━━                                                        │
│                                                                             │
│  Recipe Name *                                                              │
│  [================================================================]         │
│                                                                             │
│  Description                                                                │
│  [================================================================]         │
│  [================================================================]         │
│  [================================================================]         │
│                                                                             │
│  Recipe Photo                                                               │
│  ┌──────────────────────────────────────┐                                  │
│  │  Drag & Drop Image Here              │                                  │
│  │  or [Browse Files]                   │   ┌────────────┐                │
│  │                                      │   │  Preview   │                │
│  │  Supported: JPG, PNG, WebP          │   │            │                │
│  │  Max size: 5MB                      │   │   IMAGE    │                │
│  └──────────────────────────────────────┘   │            │                │
│                                              └────────────┘                │
│                                              [Remove]                       │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  RECIPE DETAILS                                                             │
│  ━━━━━━━━━━━━━━━                                                           │
│                                                                             │
│  ┌────────────────┬────────────────┬────────────────┬──────────────────┐  │
│  │ Prep Time      │ Cook Time      │ Total Time     │ Yield/Servings   │  │
│  │ [____] min     │ [____] min     │ [____] min     │ [____________]   │  │
│  └────────────────┴────────────────┴────────────────┴──────────────────┘  │
│                                                                             │
│  ┌──────────────────────┬──────────────────────┬──────────────────────┐   │
│  │ Category             │ Cuisine              │ Tags                 │   │
│  │ [Breakfast      ▼]   │ [Italian        ▼]   │ [________________]   │   │
│  └──────────────────────┴──────────────────────┴──────────────────────┘   │
│                                                                             │
│  Source URL (optional)                                                      │
│  [================================================================]         │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  INGREDIENTS *                                                              │
│  ━━━━━━━━━━━━━                                                             │
│                                                                             │
│  1. [===============================================================] [🗑] │
│  2. [===============================================================] [🗑] │
│  3. [===============================================================] [🗑] │
│  4. [===============================================================] [🗑] │
│  5. [===============================================================] [🗑] │
│                                                                             │
│  [+ Add Ingredient]                                                         │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  INSTRUCTIONS *                                                             │
│  ━━━━━━━━━━━━━━                                                            │
│                                                                             │
│  Step 1                                              [↑] [↓] [🗑]           │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ [B] [I] [•]                                                        │   │
│  │                                                                     │   │
│  │ Heat oil in a large skillet over medium-high heat...              │   │
│  │                                                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Step 2                                              [↑] [↓] [🗑]           │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ [B] [I] [•]                                                        │   │
│  │                                                                     │   │
│  │ Add garlic and cook until fragrant, about 30 seconds...           │   │
│  │                                                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Step 3                                              [↑] [↓] [🗑]           │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ [B] [I] [•]                                                        │   │
│  │                                                                     │   │
│  │                                                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [+ Add Step]                                                               │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  ADDITIONAL INFORMATION (Optional)                          [Expand All ▼] │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                           │
│                                                                             │
│  Notes & Tips                                                   [Expand ▼] │
│                                                                             │
│  Equipment Needed                                               [Expand ▼] │
│                                                                             │
│  Nutrition Information                                          [Expand ▼] │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  COLLECTIONS                                                                │
│  ━━━━━━━━━━━                                                               │
│                                                                             │
│  Add this recipe to collections:                                           │
│  [ ] Holiday Recipes                                                        │
│  [x] Quick Meals                                                            │
│  [ ] Desserts                                                               │
│  [ ] Asian Cuisine                                                          │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│                                          [Save Recipe] [Save as Draft]     │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Recipe Form (375px)

```
┌─────────────────────────────┐
│ ← Add Recipe       [Save ✓] │
├─────────────────────────────┤
│                             │
│ Recipe Name *               │
│ [═════════════════════════] │
│                             │
│ Description                 │
│ [═════════════════════════] │
│ [═════════════════════════] │
│                             │
│ Add Photo                   │
│ ┌─────────────────────────┐ │
│ │   Drag & Drop           │ │
│ │   or [Browse]           │ │
│ │   Max 5MB               │ │
│ └─────────────────────────┘ │
│                             │
│ ──────────────────────────  │
│                             │
│ Prep Time                   │
│ [═══] min                   │
│                             │
│ Cook Time                   │
│ [═══] min                   │
│                             │
│ Total Time                  │
│ [═══] min                   │
│                             │
│ Servings                    │
│ [═════════════════════════] │
│                             │
│ Category                    │
│ [Main Dish            ▼]    │
│                             │
│ Cuisine                     │
│ [Thai                 ▼]    │
│                             │
│ ──────────────────────────  │
│                             │
│ INGREDIENTS *               │
│                             │
│ 1. [═══════════════════] [×]│
│ 2. [═══════════════════] [×]│
│ 3. [═══════════════════] [×]│
│                             │
│ [+ Add Ingredient]          │
│                             │
│ ──────────────────────────  │
│                             │
│ INSTRUCTIONS *              │
│                             │
│ Step 1            [↑][↓][×] │
│ ┌─────────────────────────┐ │
│ │                         │ │
│ │ Heat oil in large pan.. │ │
│ │                         │ │
│ └─────────────────────────┘ │
│                             │
│ [+ Add Step]                │
│                             │
│ ──────────────────────────  │
│                             │
│ [More Options ▼]            │
│  • Notes & Tips             │
│  • Equipment                │
│  • Nutrition                │
│  • Collections              │
│                             │
│ ──────────────────────────  │
│                             │
│ [Save Recipe]               │
│                             │
└─────────────────────────────┘
```

---

## Collections Interface

### Collections Management Page

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Collections                                              [User Menu ▼]    │
└────────────────────────────────────────────────────────────────────────────┘
┌──────────────┬────────────────────────────────────────────────────────────┐
│              │                                                             │
│ MY RECIPES   │  My Collections                               [+ New]      │
│ ├─ All (247) │  ═══════════════                                            │
│ ├─ Favorites │                                                             │
│ │   (34) ⭐   │  Organize your recipes into custom collections             │
│ └─ Trash (3) │                                                             │
│              │  ┌──────────────────────────────────────────────────────┐  │
│ COLLECTIONS  │  │  DEFAULT COLLECTIONS                                 │  │
│ ├─ Holiday   │  │  ━━━━━━━━━━━━━━━━━━━                                │  │
│ │   (23)     │  │                                                      │  │
│ ├─ Quick     │  │  ┌─────────────────┐  ┌─────────────────┐           │  │
│ │   Meals    │  │  │ ⭐ Favorites     │  │ All Recipes     │           │  │
│ │   (45)     │  │  │                 │  │                 │           │  │
│ ├─ Desserts  │  │  │ 34 recipes      │  │ 247 recipes     │           │  │
│ │   (18)     │  │  │                 │  │                 │           │  │
│ └─ + New     │  │  │ [View →]        │  │ [View →]        │           │  │
│              │  │  └─────────────────┘  └─────────────────┘           │  │
│              │  └──────────────────────────────────────────────────────┘  │
│              │                                                             │
│              │  ┌──────────────────────────────────────────────────────┐  │
│              │  │  YOUR COLLECTIONS                                    │  │
│              │  │  ━━━━━━━━━━━━━━━━                                   │  │
│              │  │                                                      │  │
│              │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│              │  │  │ 🎄 Holiday  │  │ ⚡ Quick    │  │ 🍰 Desserts │ │  │
│              │  │  │   Recipes   │  │    Meals    │  │             │ │  │
│              │  │  │             │  │             │  │             │ │  │
│              │  │  │ 23 recipes  │  │ 45 recipes  │  │ 18 recipes  │ │  │
│              │  │  │             │  │             │  │             │ │  │
│              │  │  │ [Edit][×]   │  │ [Edit][×]   │  │ [Edit][×]   │ │  │
│              │  │  │ [View →]    │  │ [View →]    │  │ [View →]    │ │  │
│              │  │  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│              │  │                                                      │  │
│              │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│              │  │  │ 🌏 Asian    │  │ 🍕 Italian  │  │ 🎂 Baking   │ │  │
│              │  │  │   Cuisine   │  │   Classics  │  │   Projects  │ │  │
│              │  │  │             │  │             │  │             │ │  │
│              │  │  │ 31 recipes  │  │ 19 recipes  │  │ 12 recipes  │ │  │
│              │  │  │             │  │             │  │             │ │  │
│              │  │  │ [Edit][×]   │  │ [Edit][×]   │  │ [Edit][×]   │ │  │
│              │  │  │ [View →]    │  │ [View →]    │  │ [View →]    │ │  │
│              │  │  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│              │  │                                                      │  │
│              │  └──────────────────────────────────────────────────────┘  │
│              │                                                             │
└──────────────┴────────────────────────────────────────────────────────────┘
```

### Create Collection Modal

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                   ┌────────────────────────────────┐                       │
│                   │  Create New Collection         │                       │
│                   │  ══════════════════════        │                       │
│                   │                                │                       │
│                   │  Collection Name *             │                       │
│                   │  [═══════════════════════════] │                       │
│                   │  Max 50 characters             │                       │
│                   │                                │                       │
│                   │  Icon (optional)               │                       │
│                   │  🍕 🍰 🥗 🍜 🌮 🍔 🍱 🎄 ⚡    │                       │
│                   │  [Select emoji...]             │                       │
│                   │                                │                       │
│                   │  ━━━━━━━━━━━━━━━━━━━━━━━━━━  │                       │
│                   │                                │                       │
│                   │        [Cancel] [Create]       │                       │
│                   │                                │                       │
│                   └────────────────────────────────┘                       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Add to Collection Dropdown (on Recipe Detail)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Thai Basil Chicken                                               [⭐]     │
│  ═══════════════════                                                        │
│                                                                             │
│  Source: thaitable.com ↗                    [Edit] [Duplicate] [Delete]    │
│                                             [Print] [Add to Collection ▼]  │
│                                                      │                      │
│                                                      ▼                      │
│                                    ┌──────────────────────────────┐        │
│                                    │ Select Collections           │        │
│                                    │ ═══════════════════          │        │
│                                    │                              │        │
│                                    │ [x] Quick Meals              │        │
│                                    │ [x] Asian Cuisine            │        │
│                                    │ [ ] Holiday Recipes          │        │
│                                    │ [ ] Desserts                 │        │
│                                    │ [ ] Italian Classics         │        │
│                                    │                              │        │
│                                    │ ━━━━━━━━━━━━━━━━━━━━━━━━━  │        │
│                                    │                              │        │
│                                    │ [+ Create New Collection]    │        │
│                                    │                              │        │
│                                    │        [Done]                │        │
│                                    │                              │        │
│                                    └──────────────────────────────┘        │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Import Recipes (JSON Upload)

### JSON Upload Page

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Recipes                                        [User Menu ▼]    │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Import Recipes                                                             │
│  ═══════════════                                                            │
│                                                                             │
│  Upload one or more JSON files to import recipes into your collection.     │
│  Accepted formats: Single recipe JSON or recipe collection JSON.           │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  UPLOAD FILES                                                               │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │                          📤                                         │   │
│  │                                                                     │   │
│  │              Drag & Drop JSON Files Here                           │   │
│  │                                                                     │   │
│  │                        or                                          │   │
│  │                                                                     │   │
│  │                   [Browse Files]                                   │   │
│  │                                                                     │   │
│  │               Supported: .json files only                          │   │
│  │               Multiple files accepted                              │   │
│  │               Max 10MB per file                                    │   │
│  │                                                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  IMPORT OPTIONS                                                             │
│                                                                             │
│  Duplicate Handling:                                                        │
│  (•) Skip duplicates (based on source URL)                                 │
│  ( ) Update existing recipes                                               │
│  ( ) Import as new (create duplicates)                                     │
│                                                                             │
│  [ ] Add imported recipes to collection: [Select Collection ▼]             │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  EXAMPLE JSON FORMAT                                            [Expand ▼] │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ Single Recipe:                                                     │   │
│  │ {                                                                  │   │
│  │   "name": "Chocolate Chip Cookies",                               │   │
│  │   "description": "Classic homemade cookies",                      │   │
│  │   "recipeIngredient": ["2 cups flour", "1 cup sugar", ...],      │   │
│  │   "recipeInstructions": [...],                                    │   │
│  │   "url": "https://example.com/recipe",                            │   │
│  │   ...                                                             │   │
│  │ }                                                                  │   │
│  │                                                                     │   │
│  │ Recipe Collection:                                                 │   │
│  │ {                                                                  │   │
│  │   "recipes": [                                                     │   │
│  │     { "name": "Recipe 1", ... },                                  │   │
│  │     { "name": "Recipe 2", ... }                                   │   │
│  │   ]                                                                │   │
│  │ }                                                                  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Upload in Progress

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Importing Recipes...                                                       │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 📄 my_recipes_export.json                                  [✓]     │   │
│  │ ████████████████████████████████████████████████ 100%             │   │
│  │ 45 recipes processed • 43 imported • 2 skipped (duplicates)       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 📄 holiday_recipes.json                                    [⟳]     │   │
│  │ ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 45%                 │   │
│  │ Processing recipe 12 of 27...                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 📄 desserts.json                                           [📋]    │   │
│  │ Queued...                                                          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  Total Progress: 57 of 95 recipes (60%)                                    │
│  ████████████████████████████░░░░░░░░░░░░░░░░░░░░                         │
│                                                                             │
│  [Cancel Import]                                                            │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Import Complete

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Import Complete! ✓                                                         │
│  ═══════════════════                                                        │
│                                                                             │
│  Successfully imported 88 recipes from 3 files                              │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ✓ my_recipes_export.json                                          │   │
│  │    43 imported • 2 skipped (duplicates)                            │   │
│  │                                                                     │   │
│  │  ✓ holiday_recipes.json                                            │   │
│  │    27 imported                                                     │   │
│  │                                                                     │   │
│  │  ✓ desserts.json                                                   │   │
│  │    18 imported                                                     │   │
│  │                                                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ⚠ 2 recipes were skipped because they already exist in your collection    │
│  [View Skipped Recipes]                                                     │
│                                                                             │
│  All imported recipes have been added to your collection.                  │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  [View All Recipes] [Import More Files] [Done]                             │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Import Error State

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Import Errors ⚠                                                            │
│  ═════════════                                                              │
│                                                                             │
│  Some files could not be imported                                          │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ ✓ my_recipes_export.json                                           │   │
│  │   43 recipes imported successfully                                 │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ ✗ invalid_file.json                                                │   │
│  │   Error: Invalid JSON format                                       │   │
│  │   The file is not valid JSON. Please check the file format.       │   │
│  │   [Download Error Log]                                             │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ ⚠ partial_recipes.json                                             │   │
│  │   12 of 15 recipes imported                                        │   │
│  │   3 recipes skipped due to missing required fields                │   │
│  │   [View Details]                                                   │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                             │
│  55 recipes imported • 3 skipped • 1 file failed                           │
│                                                                             │
│  [Try Again] [View Imported Recipes] [Done]                                │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Quick Upload in Sidebar (Alternative)

```
┌──────────────┐
│ ACTIONS      │
│              │
│ [+ Add       │
│   Recipe]    │
│              │
│ [📤 Upload   │────┐
│   JSON]      │    │
└──────────────┘    │
                    ▼
      ┌──────────────────────────┐
      │ Upload JSON Files        │
      │ ═══════════════          │
      │                          │
      │ ┌──────────────────────┐ │
      │ │  📤 Drop files here  │ │
      │ │  or [Browse]         │ │
      │ └──────────────────────┘ │
      │                          │
      │ Options:                 │
      │ (•) Skip duplicates      │
      │ ( ) Update existing      │
      │                          │
      │ [ ] Add to collection:   │
      │     [Select...      ▼]   │
      │                          │
      │ [Cancel] [Upload]        │
      │                          │
      └──────────────────────────┘
```

---

## Mobile Layouts

### Mobile Dashboard (375px)

```
┌─────────────────────────────┐
│ ☰  Recipe Catalog      [👤] │
├─────────────────────────────┤
│ [🔍 Search recipes...]      │
├─────────────────────────────┤
│                             │
│ My Recipes (247)            │
│                             │
│ [Grid ⊞] [List ≡]           │
│ Sort: [Recent ▼]            │
│                             │
│ Filters: [Italian ✕]        │
│         [<30min ✕]          │
│ [Clear All]                 │
│                             │
│ ──────────────────────────  │
│                             │
│ ┌─────────────────────────┐ │
│ │ ┌─────────────────────┐ │ │
│ │ │                     │ │ │
│ │ │   RECIPE IMAGE      │ │ │
│ │ │                     │ │ │
│ │ └─────────────────────┘ │ │
│ │ Thai Basil Chicken      │ │
│ │ Thai • 45min       [⭐] │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ ┌─────────────────────┐ │ │
│ │ │                     │ │ │
│ │ │   RECIPE IMAGE      │ │ │
│ │ │                     │ │ │
│ │ └─────────────────────┘ │ │
│ │ Pasta Carbonara         │ │
│ │ Italian • 20min    [⭐] │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ ┌─────────────────────┐ │ │
│ │ │                     │ │ │
│ │ │   RECIPE IMAGE      │ │ │
│ │ │                     │ │ │
│ │ └─────────────────────┘ │ │
│ │ Chocolate Chip Cookies  │ │
│ │ American • 30min   [⭐] │ │
│ └─────────────────────────┘ │
│                             │
│ ──────────────────────────  │
│ Page 1 of 11 [Next →]       │
│                             │
├─────────────────────────────┤
│[🏠][🔍][➕][📚][☰]           │
│Home Search Add  Colls Menu  │
└─────────────────────────────┘
```

### Mobile Navigation Drawer

```
┌─────────────────────────────┐
│ ☰                           │
├─────────────────────────────┤
│                             │
│ [👤] John Doe               │
│     john@example.com        │
│                             │
│ ──────────────────────────  │
│                             │
│ MY RECIPES                  │
│ ├─ All Recipes      (247)   │
│ ├─ ⭐ Favorites      (34)   │
│ └─ 🗑️ Trash          (3)   │
│                             │
│ COLLECTIONS                 │
│ ├─ 🎄 Holiday       (23)    │
│ ├─ ⚡ Quick Meals   (45)    │
│ ├─ 🍰 Desserts      (18)    │
│ ├─ 🌏 Asian         (31)    │
│ └─ + New Collection         │
│                             │
│ ──────────────────────────  │
│                             │
│ [📤 Upload JSON]            │
│ [📥 Export Data]            │
│                             │
│ ──────────────────────────  │
│                             │
│ [⚙️ Settings]                │
│ [📋 Privacy Policy]         │
│ [🚪 Log Out]                │
│                             │
└─────────────────────────────┘
```

### Mobile Filter Drawer (Slide-up)

```
┌─────────────────────────────┐
│                             │
│         [Filters]           │
│     ════════════            │
│                             │
│ ┌─────────────────────────┐ │
│ │                         │ │
│ │ CUISINE                 │ │
│ │ [x] Italian      (34)   │ │
│ │ [ ] Thai         (28)   │ │
│ │ [ ] Mexican      (19)   │ │
│ │ [ ] Chinese      (15)   │ │
│ │ [Show More ▼]           │ │
│ │                         │ │
│ │ ──────────────────────  │ │
│ │                         │ │
│ │ TIME                    │ │
│ │ [x] Under 30 min (89)   │ │
│ │ [ ] 30-60 min   (112)   │ │
│ │ [ ] 1-2 hours    (38)   │ │
│ │ [ ] Over 2 hours  (8)   │ │
│ │                         │ │
│ │ ──────────────────────  │ │
│ │                         │ │
│ │ CATEGORY                │ │
│ │ [ ] Breakfast    (42)   │ │
│ │ [ ] Lunch        (68)   │ │
│ │ [ ] Dinner      (103)   │ │
│ │ [ ] Dessert      (34)   │ │
│ │                         │ │
│ │ ──────────────────────  │ │
│ │                         │ │
│ │ SOURCE                  │ │
│ │ [ ] Imported    (215)   │ │
│ │ [ ] Manual       (32)   │ │
│ │                         │ │
│ │ ──────────────────────  │ │
│ │                         │ │
│ │ COLLECTIONS             │ │
│ │ [ ] Holiday      (23)   │ │
│ │ [ ] Quick Meals  (45)   │ │
│ │ [ ] Desserts     (18)   │ │
│ │                         │ │
│ └─────────────────────────┘ │
│                             │
│ [Clear All] [Apply Filters] │
│                             │
└─────────────────────────────┘
```

### Mobile Recipe Add/Edit (Simplified)

```
┌─────────────────────────────┐
│ ← New Recipe      [Save ✓]  │
├─────────────────────────────┤
│                             │
│ BASICS                      │
│                             │
│ Recipe Name *               │
│ [═════════════════════════] │
│                             │
│ ──────────────────────────  │
│                             │
│ Photo                       │
│ ┌─────────────────────────┐ │
│ │      📸 Add Photo       │ │
│ │   Tap to upload         │ │
│ └─────────────────────────┘ │
│                             │
│ ──────────────────────────  │
│                             │
│ [Expand: Times & Details ▼] │
│ [Expand: Ingredients ▼]     │
│ [Expand: Instructions ▼]    │
│ [Expand: More Options ▼]    │
│                             │
│ ──────────────────────────  │
│                             │
│ [Save Recipe]               │
│                             │
└─────────────────────────────┘
```

---

## Component Library

### Buttons

```
Primary Button:        [Save Recipe]
Secondary Button:      [Cancel]
Destructive Button:    [Delete]
Icon Button:           [⭐] [✎] [🗑]
Link Button:           [View Details →]

States:
Normal:    [Button]
Hover:     [Button] (with shadow/highlight)
Active:    [Button] (pressed state)
Disabled:  [Button] (grayed out)
Loading:   [⟳ Saving...]
```

### Form Elements

```
Text Input:
Label
[═══════════════════════════════]
Helper text or error message

Text Area:
Label
[═══════════════════════════════]
[═══════════════════════════════]
[═══════════════════════════════]

Dropdown:
Label
[Selected Option           ▼]
  ├─ Option 1
  ├─ Option 2
  └─ Option 3

Checkbox:
[x] Checked
[ ] Unchecked

Radio Button:
(•) Selected
( ) Unselected

Toggle Switch:
[ON  ●──]
[──●  OFF]
```

### Cards

```
Recipe Card (Grid):
┌───────────────┐
│ ┌───────────┐ │
│ │   IMAGE   │ │
│ └───────────┘ │
│               │
│ Recipe Name   │
│               │
│ Cuisine Tag   │
│ 🕐 30min [⭐] │
│ [✎] [🗑]      │
└───────────────┘

Recipe Row (List):
┌──────────────────────────────────┐
│ ┌────┐ Recipe Name         [⭐]  │
│ │IMG │ Description...      [✎]  │
│ └────┘ Cuisine • 30min     [🗑]  │
└──────────────────────────────────┘

Collection Card:
┌───────────────┐
│ 🎄 Holiday    │
│    Recipes    │
│               │
│  23 recipes   │
│               │
│ [Edit] [×]    │
│ [View →]      │
└───────────────┘
```

### Navigation Elements

```
Breadcrumb:
Home > Collections > Holiday > Recipe Name

Tabs:
[Ingredients] [Instructions]
 ═══════════

Pagination:
← Previous  [1] 2 3 ... 10  Next →

Filter Chips:
[Italian ✕] [Under 30 min ✕] [Clear All]
```

### Feedback Elements

```
Toast Notification:
┌────────────────────────────┐
│ ✓ Recipe saved!       [×]  │
└────────────────────────────┘

Alert Box:
┌────────────────────────────┐
│ ⚠ Warning                  │
│ This action cannot be      │
│ undone.                    │
│        [Cancel] [Continue] │
└────────────────────────────┘

Progress Bar:
████████████████░░░░░░░░ 65%

Loading Spinner:
    ⟳ Loading...

Skeleton Loading:
┌───────────────┐
│ ▓▓▓▓▓▓▓▓▓▓▓▓ │
│               │
│ ▓▓▓▓▓▓▓       │
│ ▓▓▓▓          │
└───────────────┘
```

### Empty States

```
No Recipes:
┌────────────────────────────┐
│           🍳               │
│                            │
│  No recipes yet            │
│  Start by adding your      │
│  first recipe              │
│                            │
│    [+ Add Recipe]          │
└────────────────────────────┘

No Search Results:
┌────────────────────────────┐
│           🔍               │
│                            │
│  No recipes found          │
│  Try different keywords    │
│                            │
│    [Clear Search]          │
└────────────────────────────┘

Empty Collection:
┌────────────────────────────┐
│           📚               │
│                            │
│  This collection is empty  │
│  Add recipes to get        │
│  started                   │
│                            │
│  [Browse All Recipes]      │
└────────────────────────────┘
```

---

## Responsive Behavior Summary

### Breakpoint Adaptations

**Mobile (320-767px):**
- Single column layouts
- Bottom navigation
- Drawers for filters/navigation
- Stacked forms
- Simplified headers

**Tablet (768-1279px):**
- 2-3 column grids
- Sidebar navigation (collapsible)
- Side panel filters
- Some multi-column forms

**Desktop (1280px+):**
- 3-4 column grids
- Persistent sidebar
- Always-visible filters
- Multi-column forms
- Full header

### Touch Targets (Mobile)
- Minimum 44x44px for all interactive elements
- Adequate spacing between clickable elements
- Swipe gestures for quick actions

### Typography Scaling
- Mobile: Base 16px
- Tablet: Base 16px
- Desktop: Base 16px
- Headers scale proportionally

---

## Next Steps

With wireframes complete, the next phase should be:

1. **Design System** - Define visual style (colors, typography, spacing)
2. **High-Fidelity Mockups** - Apply design system to wireframes
3. **Interactive Prototype** - Create clickable prototype for user testing
4. **Developer Handoff** - Component specifications and assets

Would you like me to proceed with creating the Design System next?

---

**End of Document**
