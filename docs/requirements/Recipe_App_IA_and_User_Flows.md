# Recipe Catalog App - Information Architecture & User Flows

**Version:** 1.0  
**Date:** November 14, 2025  
**Phase:** Design - Information Architecture

---

## Table of Contents

1. [Site Map](#site-map)
2. [Navigation Structure](#navigation-structure)
3. [User Flows](#user-flows)
4. [Page Inventory](#page-inventory)
5. [Content Hierarchy](#content-hierarchy)
6. [State Diagrams](#state-diagrams)

---

## Site Map

```
Recipe Catalog App
│
├── Public Pages (Unauthenticated)
│   ├── Landing Page
│   ├── Login
│   ├── Register
│   ├── Password Reset
│   ├── Email Verification
│   └── Privacy Policy
│
└── Application (Authenticated)
    │
    ├── Main Dashboard
    │   ├── Recipe Listing (Grid/List View)
    │   │   ├── All Recipes
    │   │   ├── Favorites
    │   │   ├── User Collections
    │   │   └── Trash
    │   │
    │   └── Recipe Detail View
    │       ├── View Mode
    │       ├── Edit Mode
    │       └── Print View
    │
    ├── Recipe Management
    │   ├── Add Recipe (Manual Entry)
    │   ├── Edit Recipe
    │   ├── Import from Extension (API endpoint, no UI page)
    │   └── Duplicate Recipe (opens in Edit Mode)
    │
    ├── Collections
    │   ├── Collections List
    │   ├── Create Collection
    │   ├── Edit Collection
    │   └── View Collection (filtered recipe listing)
    │
    ├── Search & Filter
    │   ├── Search Results
    │   └── Advanced Filters (sidebar/modal)
    │
    ├── Data Export
    │   ├── Export Options Page
    │   └── Export Progress/Download
    │
    └── User Account
        ├── Account Settings
        │   ├── Profile Settings
        │   ├── Application Preferences
        │   └── Privacy & Security
        │
        ├── Statistics Dashboard
        └── Account Deletion
```

---

## Navigation Structure

### Primary Navigation (Always Visible - Authenticated Users)

**Top Navigation Bar:**
```
┌─────────────────────────────────────────────────────────────────┐
│ [Logo] Recipe Catalog    [Search Bar]    [User Menu ▼]          │
└─────────────────────────────────────────────────────────────────┘
```

**Elements:**
1. **Logo/Brand** (left) - Links to main dashboard
2. **Search Bar** (center) - Global search, always accessible
3. **User Menu** (right) - Dropdown with:
   - View Profile
   - Settings
   - Export Data
   - Log Out

### Secondary Navigation (Sidebar or Mobile Drawer)

**Sidebar Navigation:**
```
┌──────────────────┐
│ My Recipes       │
│ ├─ All Recipes   │
│ ├─ Favorites ⭐   │
│ └─ Trash 🗑️      │
│                  │
│ Collections      │
│ ├─ [Collection1] │
│ ├─ [Collection2] │
│ ├─ [Collection3] │
│ └─ + New         │
│                  │
│ Actions          │
│ ├─ + Add Recipe  │
│ └─ 📤 Export     │
└──────────────────┘
```

**Mobile Navigation:**
- Hamburger menu (☰) opens drawer with same structure
- Bottom navigation bar (alternative):
  ```
  ┌───────────────────────────────────────────┐
  │ [Home] [Search] [Add] [Collections] [Menu] │
  └───────────────────────────────────────────┘
  ```

### Breadcrumb Navigation

Used on detail pages for context:
```
Home > Collections > Holiday Recipes > Grandma's Apple Pie
Home > All Recipes > Thai Basil Chicken
Home > Settings > Privacy & Security
```

---

## User Flows

### 1. New User Onboarding Flow

```
┌─────────────┐
│ Land on App │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│ Register    │─────▶│ Verify Email │
│ (Email/Pwd) │      │              │
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ First Login  │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────────┐
                     │ Empty Dashboard  │
                     │ (Welcome Screen) │
                     └──────┬───────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
         ┌─────────────┐        ┌─────────────┐
         │ Install     │        │ Add Recipe  │
         │ Extension   │        │ Manually    │
         └─────────────┘        └─────────────┘
```

**Key Decisions:**
- Show welcome message with clear CTAs
- Guide to installing browser extension
- Option to add first recipe manually
- Brief feature tour (optional, dismissible)

---

### 2. Import Recipe from Extension Flow

```
┌──────────────────┐
│ User on Recipe   │
│ Website          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Click Extension  │
│ Icon in Browser  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐      ┌──────────────┐
│ Extension Parses │      │ User Logged  │
│ Recipe Data      │─────▶│ In?          │
└──────────────────┘      └──────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │ No                      │ Yes
                    ▼                         ▼
            ┌───────────────┐         ┌──────────────┐
            │ Prompt Login  │         │ Send to API  │
            │ in Extension  │         └──────┬───────┘
            └───────┬───────┘                │
                    │                        │
                    └────────────┬───────────┘
                                 ▼
                         ┌───────────────┐
                         │ Recipe Saved  │
                         │ to Database   │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ Show Success  │
                         │ Notification  │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ User Opens    │
                         │ Web App       │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ New Recipe    │
                         │ Appears in    │
                         │ All Recipes   │
                         └───────────────┘
```

**Key Decisions:**
- Extension handles authentication
- API validates and stores data
- Web app shows imported recipe immediately
- Duplicate detection prevents re-importing same URL

---

### 3. Manual Recipe Entry Flow

```
┌─────────────────┐
│ User Clicks     │
│ "+ Add Recipe"  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Recipe Entry    │
│ Form (Blank)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Fills:     │
│ - Name*         │
│ - Ingredients*  │
│ - Instructions* │
│ - Optional data │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Auto-save Draft │◀─────│ Every 30sec  │
│ to localStorage │      └──────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Clicks     │
│ "Save Recipe"   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Validate Form   │─────▶│ Errors?      │
└─────────────────┘      └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │ Yes                   │ No
                    ▼                       ▼
            ┌───────────────┐       ┌──────────────┐
            │ Show Error    │       │ Save to DB   │
            │ Messages      │       └──────┬───────┘
            └───────┬───────┘              │
                    │                      ▼
                    │              ┌──────────────┐
                    │              │ Clear Draft  │
                    │              └──────┬───────┘
                    │                     │
                    │                     ▼
                    │              ┌──────────────┐
                    │              │ Show Success │
                    │              │ Message      │
                    │              └──────┬───────┘
                    │                     │
                    │                     ▼
                    │              ┌──────────────┐
                    └─────────────▶│ Redirect to  │
                                   │ Recipe Detail│
                                   └──────────────┘
```

**Key Decisions:**
- Auto-save prevents data loss
- Clear validation with helpful messages
- Redirect to newly created recipe
- Draft recovery if user navigates away

---

### 4. Search and Filter Flow

```
┌─────────────────┐
│ User Types in   │
│ Search Bar      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Debounce 300ms  │─────▶│ Query API    │
└─────────────────┘      └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ Display      │
                         │ Results      │
                         └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
            ┌───────────────┐       ┌──────────────┐
            │ Results Found │       │ No Results   │
            │ Show Cards    │       │ Show Empty   │
            └───────┬───────┘       │ State with   │
                    │               │ Suggestions  │
                    │               └──────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ User Can:     │
            │ - Apply       │
            │   Filters     │
            │ - Sort        │
            │ - Change View │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ Filters Apply │
            │ Results Update│
            │ in Real-time  │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ User Clicks   │
            │ Recipe Card   │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ Recipe Detail │
            │ View          │
            └───────────────┘
```

**Key Decisions:**
- Search is instant with debouncing
- Filters work with search (AND logic)
- Empty states provide helpful guidance
- State persists during session

---

### 5. Create Collection Flow

```
┌─────────────────┐
│ User Clicks     │
│ "+ New          │
│ Collection"     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Modal/Drawer    │
│ Opens with      │
│ Name Input      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Enters     │
│ Collection Name │
│ (max 50 chars)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ User Clicks     │─────▶│ Validate:    │
│ "Create"        │      │ - Not empty  │
└─────────────────┘      │ - Unique     │
                         │ - <50 chars  │
                         └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │ Invalid               │ Valid
                    ▼                       ▼
            ┌───────────────┐       ┌──────────────┐
            │ Show Error    │       │ Create in DB │
            │ Inline        │       └──────┬───────┘
            └───────┬───────┘              │
                    │                      ▼
                    │              ┌──────────────┐
                    │              │ Add to       │
                    │              │ Sidebar Nav  │
                    │              └──────┬───────┘
                    │                     │
                    │                     ▼
                    │              ┌──────────────┐
                    │              │ Close Modal  │
                    │              └──────┬───────┘
                    │                     │
                    │                     ▼
                    │              ┌──────────────┐
                    │              │ Show Success │
                    │              │ Toast        │
                    │              └──────┬───────┘
                    │                     │
                    │                     ▼
                    └─────────────▶│ Optional:    │
                                   │ Navigate to  │
                                   │ Empty        │
                                   │ Collection   │
                                   └──────────────┘
```

**Key Decisions:**
- Quick creation via modal (no separate page)
- Validation prevents duplicates
- Immediate feedback with toast
- Collection appears in navigation instantly

---

### 6. Add Recipe to Collection Flow

```
┌─────────────────┐
│ User Viewing    │
│ Recipe Detail   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Clicks     │
│ "Add to         │
│ Collection"     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Dropdown/Modal  │
│ Shows:          │
│ - All           │
│   Collections   │
│ - Checkboxes    │
│   (multi-select)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Selects    │
│ Collection(s)   │
│ (checked =      │
│  already in)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Clicks     │
│ "Save" or       │
│ Auto-save       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update DB:      │
│ - Add new       │
│   associations  │
│ - Remove        │
│   unchecked     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Show Success    │
│ Toast:          │
│ "Added to       │
│ [Collection]"   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update UI:      │
│ - Show badges   │
│ - Update counts │
└─────────────────┘

Alternative Quick Add (Favorites):
┌─────────────────┐
│ User Clicks     │
│ ⭐ Star Icon    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Toggle          │
│ Favorites       │
│ (Instant)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Icon Changes    │
│ State (filled/  │
│ outline)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Subtle Toast    │
│ Confirmation    │
└─────────────────┘
```

**Key Decisions:**
- Multi-select allows adding to multiple collections
- Checkboxes show current membership
- Favorites gets special one-click treatment
- Immediate visual feedback

---

### 7. Edit Recipe Flow

```
┌─────────────────┐
│ User Viewing    │
│ Recipe Detail   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Clicks     │
│ "Edit" Button   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load Edit Form  │
│ Pre-populated   │
│ with Current    │
│ Data            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ User Makes      │◀─────│ Auto-save    │
│ Changes         │      │ Every 30sec  │
└────────┬────────┘      └──────────────┘
         │
         │
         ▼
┌─────────────────┐
│ User Clicks:    │
│ - "Save"        │
│ - "Cancel"      │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Cancel? │
    └────┬────┘
         │
    ┌────┴────────────┐
    │ Yes             │ No (Save)
    ▼                 ▼
┌───────────┐   ┌─────────────┐
│ Unsaved?  │   │ Validate    │
└─────┬─────┘   │ Changes     │
      │         └──────┬──────┘
  ┌───┴───┐            │
  │Yes│No │      ┌─────┴─────┐
  ▼   ▼   │      │           │
┌─────┐ ┌─┴──┐   │Valid    Invalid
│Warn │ │Back│   ▼           ▼
│User │ │to  │ ┌────┐    ┌────────┐
└─┬───┘ │View│ │Save│    │Show    │
  │     └────┘ │to  │    │Errors  │
  │            │DB  │    └───┬────┘
  ▼            └─┬──┘        │
┌────┐           │           │
│Back│           ▼           │
│to  │    ┌──────────┐       │
│View│◀───│Update    │       │
└────┘    │lastMod   │       │
          │Timestamp │       │
          └─────┬────┘       │
                │            │
                ▼            │
          ┌──────────┐       │
          │Redirect  │       │
          │to Detail │       │
          │View      │       │
          └─────┬────┘       │
                │            │
                ▼            │
          ┌──────────┐       │
          │Show      │       │
          │Success   │       │
          │Toast     │       │
          └──────────┘       │
                             │
                ◀────────────┘
```

**Key Decisions:**
- Pre-populate all fields from existing data
- Auto-save prevents data loss
- Warn on cancel if unsaved changes
- Source URL read-only for imported recipes
- Update lastModified timestamp

---

### 8. Delete Recipe Flow

```
┌─────────────────┐
│ User Clicks     │
│ "Delete" on     │
│ Recipe          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Confirmation    │
│ Modal Shows:    │
│ - Recipe Name   │
│ - Thumbnail     │
│ - Warning       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Chooses:   │
│ - "Cancel"      │
│ - "Delete"      │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Delete? │
    └────┬────┘
         │
    ┌────┴────┐
    │ No │Yes │
    ▼    ▼    │
  ┌────┐ ┌────┴──────┐
  │Keep│ │Soft Delete│
  │It  │ │Recipe     │
  └────┘ └────┬──────┘
              │
              ▼
       ┌──────────────┐
       │ Move to      │
       │ "Trash"      │
       │ Folder       │
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │ Remove from  │
       │ All          │
       │ Collections  │
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │ Set 30-day   │
       │ Auto-purge   │
       │ Timer        │
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │ Show Success │
       │ Toast:       │
       │ "Moved to    │
       │ Trash"       │
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │ Redirect or  │
       │ Update List  │
       │ View         │
       └──────────────┘
```

**Recovery Flow:**
```
┌─────────────────┐
│ User Navigates  │
│ to Trash Folder │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Shows Deleted   │
│ Recipes with    │
│ Days Until      │
│ Permanent       │
│ Deletion        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Clicks     │
│ "Restore"       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Move Back to    │
│ "All Recipes"   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Show Success    │
│ Toast           │
└─────────────────┘
```

**Key Decisions:**
- Always confirm deletion
- Soft delete with 30-day recovery
- Trash folder accessible from navigation
- Clear communication about permanent deletion

---

### 9. Export Data Flow

```
┌─────────────────┐
│ User Clicks     │
│ "Export Data"   │
│ in Menu         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Export Options  │
│ Page Shows:     │
│ - Format Choice │
│ - Scope Choice  │
│ - Options       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Selects:   │
│ 1. Format:      │
│    - JSON       │
│    - Markdown   │
│    - Text       │
│ 2. Scope:       │
│    - All        │
│    - Collection │
│    - Selection  │
│ 3. Options:     │
│    - Images Y/N │
│    - Metadata   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Clicks     │
│ "Generate       │
│ Export"         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Show Progress   │
│ Indicator       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Generate Export │─────▶│ Small Set?   │
│                 │      │ (<50 recipes)│
└─────────────────┘      └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │ Yes                   │ No
                    ▼                       ▼
            ┌───────────────┐       ┌──────────────┐
            │ Client-side   │       │ Server-side  │
            │ Generation    │       │ Background   │
            └───────┬───────┘       │ Job          │
                    │               └──────┬───────┘
                    │                      │
                    └──────────┬───────────┘
                               ▼
                        ┌──────────────┐
                        │ File Ready   │
                        │ for Download │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ Show         │
                        │ "Download"   │
                        │ Button       │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ User Clicks  │
                        │ Download     │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ File         │
                        │ Downloads    │
                        │ to Device    │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ Show Success │
                        │ Message      │
                        └──────────────┘
```

**Key Decisions:**
- Clear options before generation
- Progress indicator for long operations
- Background job for large exports
- Rate limiting (5 exports/hour)
- Files are temporary (not stored on server)

---

### 10. Settings Management Flow

```
┌─────────────────┐
│ User Clicks     │
│ "Settings" in   │
│ User Menu       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Settings Page   │
│ with Tabs:      │
│ - Profile       │
│ - Preferences   │
│ - Privacy       │
│ - Data          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Modifies   │
│ Settings        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Auto-save or    │
│ "Save" Button?  │
└────────┬────────┘
         │
    ┌────┴────────────┐
    │                 │
    ▼                 ▼
┌───────────┐   ┌─────────────┐
│Auto-save  │   │Manual Save  │
│(Instant)  │   │(On Submit)  │
└─────┬─────┘   └──────┬──────┘
      │                │
      └────────┬───────┘
               ▼
        ┌──────────────┐
        │ Validate     │
        │ Changes      │
        └──────┬───────┘
               │
          ┌────┴────┐
          │ Valid?  │
          └────┬────┘
               │
    ┌──────────┴──────────┐
    │ No                  │ Yes
    ▼                     ▼
┌───────────┐      ┌──────────────┐
│Show Error │      │Save to DB    │
│Messages   │      └──────┬───────┘
└─────┬─────┘             │
      │                   ▼
      │            ┌──────────────┐
      │            │Special       │
      │            │Actions?      │
      │            └──────┬───────┘
      │                   │
      │       ┌───────────┴────────────┐
      │       ▼                        ▼
      │ ┌──────────┐           ┌──────────────┐
      │ │Email     │           │Password      │
      │ │Changed?  │           │Changed?      │
      │ └────┬─────┘           └──────┬───────┘
      │      │                        │
      │      ▼                        ▼
      │ ┌──────────┐           ┌──────────────┐
      │ │Send      │           │Logout All    │
      │ │Verify    │           │Other Sessions│
      │ │Email     │           └──────┬───────┘
      │ └────┬─────┘                  │
      │      │                        │
      │      └────────┬───────────────┘
      │               ▼
      │        ┌──────────────┐
      └───────▶│Show Success  │
               │Toast         │
               └──────────────┘
```

**Account Deletion Sub-flow:**
```
┌─────────────────┐
│ User Clicks     │
│ "Delete         │
│ Account"        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Warning Modal:  │
│ - Data will be  │
│   deleted       │
│ - Offer export  │
│ - 24hr grace    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Must Type  │
│ "DELETE" to     │
│ Confirm         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Typed           │─────▶│ Matches?     │
│ Correctly?      │      └──────┬───────┘
└─────────────────┘             │
                      ┌─────────┴─────────┐
                      │ No                │ Yes
                      ▼                   ▼
              ┌───────────────┐    ┌──────────────┐
              │ Disable       │    │ Mark Account │
              │ Delete Button │    │ for Deletion │
              └───────────────┘    └──────┬───────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │ Log Out User │
                                   └──────┬───────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │ Show Message:│
                                   │ "Account will│
                                   │ be deleted in│
                                   │ 24 hours"    │
                                   └──────────────┘
```

**Key Decisions:**
- Group settings logically by category
- Auto-save for preferences, manual save for sensitive
- Email change requires verification
- Password change logs out other sessions
- Account deletion has strong safeguards

---

## Page Inventory

### Detailed Page Breakdown

#### 1. Landing Page (Unauthenticated)
**Purpose:** Introduce app and convert visitors to users

**Key Elements:**
- Hero section with value proposition
- Feature highlights (3-4 key features)
- Screenshots/mockups of app
- Privacy commitment statement
- CTA buttons: "Get Started" / "Sign Up"
- Link to login for existing users
- Footer with privacy policy link

**User Actions:**
- Navigate to registration
- Navigate to login
- Learn about features
- View privacy policy

---

#### 2. Registration Page
**Purpose:** Create new user account

**Key Elements:**
- Email input field
- Password input field (with strength indicator)
- Password confirmation field
- Privacy policy checkbox (required)
- "Create Account" button
- Link to login page
- Clear password requirements displayed

**User Actions:**
- Enter credentials
- Submit registration
- Navigate to login

**Success:** Email verification sent, redirect to verification waiting page

---

#### 3. Login Page
**Purpose:** Authenticate existing users

**Key Elements:**
- Email input field
- Password input field
- "Remember me" checkbox
- "Login" button
- "Forgot password?" link
- Link to registration page

**User Actions:**
- Enter credentials
- Submit login
- Navigate to password reset
- Navigate to registration

**Success:** Redirect to dashboard

---

#### 4. Main Dashboard / Recipe Listing
**Purpose:** Central hub for browsing recipes

**Key Elements:**
- Search bar (prominent)
- View toggle (grid/list)
- Sort dropdown
- Filter sidebar/panel
- Recipe cards/rows
- Pagination controls
- Active filter chips (removable)
- Empty state (for new users or no results)

**User Actions:**
- Search recipes
- Apply/remove filters
- Change sort order
- Toggle view mode
- Navigate to recipe detail
- Quick actions (edit, delete) on cards
- Add new recipe
- Navigate to collections

**States:**
- Loading (skeleton cards)
- Populated (recipe cards)
- Empty (no recipes yet)
- No results (search/filter returned nothing)

---

#### 5. Recipe Detail View
**Purpose:** Display full recipe information

**Key Elements:**
- Hero image (with zoom)
- Recipe title
- Source attribution (with link)
- Metadata section (times, yield, etc.)
- Ingredients list (with checkboxes)
- Instructions (numbered steps)
- Notes section
- Nutrition info (collapsible)
- Tags/keywords
- Action buttons:
  - Edit
  - Delete
  - Duplicate
  - Add to Collection
  - Favorite toggle
  - Print
  - Share (future)

**User Actions:**
- Read recipe
- Check off ingredients
- Navigate to edit mode
- Delete recipe
- Add to collections
- Toggle favorite
- Print recipe
- View source website

**States:**
- Loading
- Displayed
- Print mode

---

#### 6. Recipe Edit/Create Form
**Purpose:** Add or modify recipe data

**Key Elements:**
**Required Section:**
- Recipe name input
- Ingredients list (dynamic add/remove)
- Instructions list (dynamic add/remove/reorder)

**Optional Section:**
- Description textarea
- Image upload (with preview)
- Time inputs (prep, cook, total)
- Yield input
- Category dropdown
- Cuisine dropdown
- Keywords input
- Equipment list
- Notes textarea
- Nutrition fields (expandable)

**Form Controls:**
- Auto-save indicator
- Save button
- Cancel button
- Validation error messages

**User Actions:**
- Fill in recipe data
- Add/remove ingredient rows
- Add/remove/reorder instruction steps
- Upload images
- Save recipe
- Cancel (with unsaved warning)

**States:**
- New recipe (blank form)
- Edit recipe (pre-populated)
- Saving
- Validation errors
- Auto-saving

---

#### 7. Collections Management
**Purpose:** Organize recipes into groups

**Key Elements:**
**Collections List View:**
- List of user collections
- Collection names
- Recipe count per collection
- Default collections (All, Favorites, Trash)
- "New Collection" button
- Edit/Delete actions per collection

**Collection Detail View:**
- Collection name (editable inline)
- Recipe count
- Filtered recipe listing (same as dashboard)
- "Add Recipe" button
- Remove recipes from collection

**Create/Edit Collection Modal:**
- Name input field
- Save/Cancel buttons

**User Actions:**
- Create new collection
- Rename collection
- Delete collection
- View recipes in collection
- Add recipes to collection
- Remove recipes from collection

**States:**
- Empty collection
- Populated collection

---

#### 8. Search Results
**Purpose:** Display filtered recipe results

**Key Elements:**
- Search query display
- Result count
- Filtered recipe cards/list
- Applied filters (chips)
- Sort options
- No results state

**User Actions:**
- Same as dashboard
- Clear search
- Modify search
- Remove filters

---

#### 9. Export Data Page
**Purpose:** Allow users to download their data

**Key Elements:**
**Format Selection:**
- Radio buttons: JSON / Markdown / Text

**Scope Selection:**
- Radio buttons: All / Collection / Selection / Favorites
- Collection dropdown (if collection selected)
- Recipe multi-select (if selection chosen)
- Date range inputs (optional filter)

**Options:**
- Include images checkbox
- Include metadata checkbox
- Single/multiple files toggle (for markdown/text)

**Generation:**
- "Generate Export" button
- Progress indicator
- Download button (when ready)
- Estimated file size

**User Actions:**
- Select format
- Select scope
- Configure options
- Generate export
- Download file

**States:**
- Configuring
- Generating
- Ready to download
- Downloaded

---

#### 10. User Settings
**Purpose:** Manage account and preferences

**Tabs/Sections:**

**Profile:**
- Email (with change option)
- Display name
- Password change
- Time zone

**Preferences:**
- Default view (grid/list)
- Default sort order
- Recipes per page
- Theme (future)

**Privacy & Security:**
- Active sessions list
- Privacy policy link
- Data export link
- Account deletion

**Statistics:**
- Total recipes
- Import vs manual breakdown
- Collections count
- Account age
- Storage used (future)

**User Actions:**
- Update profile info
- Change password
- Set preferences
- View/revoke sessions
- Export data
- Delete account

---

#### 11. Trash Folder
**Purpose:** Recover deleted recipes

**Key Elements:**
- List of soft-deleted recipes
- Days until permanent deletion
- "Restore" button per recipe
- "Permanently Delete" button per recipe
- "Empty Trash" button (bulk delete)

**User Actions:**
- Restore recipe
- Permanently delete recipe
- Empty entire trash
- Search deleted recipes

---

## Content Hierarchy

### Recipe Card (Grid View) - Priority Order
1. **Primary:** Recipe image (largest, most prominent)
2. **Secondary:** Recipe name (clear, readable)
3. **Tertiary:** 
   - Time indicator
   - Cuisine badge
   - Source type badge
4. **Quaternary:**
   - Collection badges (small)
   - Favorite indicator
5. **Actions:** (on hover/focus)
   - View
   - Edit
   - Delete

### Recipe Detail Page - Priority Order
1. **Primary:**
   - Recipe name (H1)
   - Hero image
2. **Secondary:**
   - Source attribution
   - Action buttons (Edit, Delete, etc.)
3. **Tertiary:**
   - Metadata (times, yield, categories)
   - Ingredients list
4. **Quaternary:**
   - Instructions
   - Notes
   - Nutrition (collapsible)
   - Tags

### Navigation - Priority Order
1. **Primary:** Search (always visible, center)
2. **Secondary:** 
   - Logo/Home
   - User menu
3. **Tertiary:**
   - Collections sidebar
   - Main actions (Add Recipe)

---

## State Diagrams

### Recipe State Machine

```
┌─────────────┐
│   Created   │◀──────────────┐
└──────┬──────┘               │
       │                      │
       │ Import/Manual        │ Restore
       ▼                      │
┌─────────────┐               │
│   Active    │               │
│  (Normal)   │               │
└──────┬──────┘               │
       │                      │
       │ Edit                 │
       ▼                      │
┌─────────────┐               │
│  Modified   │               │
│ (has edits) │               │
└──────┬──────┘               │
       │                      │
       │ Soft Delete          │
       ▼                      │
┌─────────────┐               │
│   Deleted   │───────────────┘
│ (In Trash)  │
└──────┬──────┘
       │
       │ 30 days elapsed
       │ or manual purge
       ▼
┌─────────────┐
│ Permanently │
│  Deleted    │
│  (Purged)   │
└─────────────┘
```

### User Session State

```
┌──────────────┐
│ Unauthenticated│
└───────┬────────┘
        │
        │ Login/Register
        ▼
┌──────────────┐
│Authenticated │
│  (Active)    │
└───────┬──────┘
        │
   ┌────┴────┐
   │         │
   ▼         ▼
┌─────┐  ┌─────┐
│Idle │  │Using│
└──┬──┘  └──┬──┘
   │        │
   │ 30min  │ Logout
   │ timeout│ or Session
   │        │ expires
   └────┬───┴──┐
        ▼      │
   ┌─────────┐ │
   │ Expired │◀┘
   └────┬────┘
        │
        │ Re-login
        ▼
   ┌──────────────┐
   │Authenticated │
   └──────────────┘
```

### Collection Membership State

```
Recipe + Collection Relationship:

┌─────────────┐
│ Not in      │
│ Collection  │
└──────┬──────┘
       │
       │ Add to Collection
       ▼
┌─────────────┐
│    In       │
│ Collection  │
└──────┬──────┘
       │
       │ Remove from Collection
       ▼
┌─────────────┐
│ Not in      │
│ Collection  │
└─────────────┘

Note: A recipe can be in multiple collections simultaneously
Each relationship is independent
```

---

## Mobile-Specific Considerations

### Mobile Navigation Pattern
**Approach:** Hybrid (Drawer + Bottom Nav)

**Bottom Navigation Bar (Primary):**
```
┌─────────────────────────────────────┐
│ [Home] [Search] [+] [Collections] [☰]│
└─────────────────────────────────────┘
```
- Home: Dashboard/recipe listing
- Search: Focus search input
- +: Quick add recipe
- Collections: Collections list
- Menu: User menu drawer

**Hamburger Drawer (Secondary):**
- User profile
- Settings
- Export data
- Logout

### Mobile Gestures
- **Swipe right on recipe card:** Add to favorites
- **Swipe left on recipe card:** Delete
- **Pull to refresh:** Reload recipe list
- **Long press on recipe card:** Quick actions menu

### Mobile-Specific UI Adaptations
1. **Recipe Cards:** Full width on mobile (1 column)
2. **Filters:** Slide-up drawer instead of sidebar
3. **Search:** Expands to full-width when focused
4. **Recipe Detail:** Ingredients and instructions in separate tabs
5. **Forms:** Single column, larger touch targets

---

## Responsive Breakpoints

```
Mobile (Portrait):  320px - 767px
Mobile (Landscape): 768px - 1023px
Tablet:             1024px - 1279px
Desktop:            1280px+
```

### Layout Changes by Breakpoint

**Mobile (320-767px):**
- Single column recipe grid
- Bottom navigation
- Drawer for filters
- Stacked form inputs
- Full-width search bar

**Tablet (768-1279px):**
- 2-3 column recipe grid
- Side navigation sidebar
- Filter panel (collapsible)
- Two-column forms (some fields)
- Search in header

**Desktop (1280px+):**
- 3-4 column recipe grid
- Persistent sidebar
- Always-visible filters (sidebar)
- Multi-column forms
- Full header with all elements

---

## Accessibility Considerations

### Keyboard Navigation
- All interactive elements are keyboard accessible
- Logical tab order throughout
- Skip to main content link
- Esc key closes modals
- Arrow keys navigate between recipe cards (grid)

### Screen Reader Support
- ARIA labels on all icons and icon-only buttons
- ARIA live regions for dynamic content (search results, toasts)
- Semantic HTML (headings, landmarks, lists)
- Form labels properly associated with inputs
- Image alt text for recipe photos

### Focus Management
- Clear focus indicators (visible outline)
- Focus trapping in modals
- Focus restoration when closing modals
- Focus on first input when opening forms

### Color & Contrast
- WCAG AA minimum (4.5:1 for text)
- Don't rely on color alone for information
- High contrast mode support
- User preference for reduced motion

---

## Next Steps

With Information Architecture complete, we should proceed to:

1. **Wireframes** - Low-fidelity layouts for each page
2. **Component Library** - Reusable UI components
3. **Design System** - Colors, typography, spacing
4. **High-Fidelity Mockups** - Visual design application
5. **Prototype** - Interactive clickable prototype

**Recommendation:** Move to wireframes next, focusing on:
- Main dashboard
- Recipe detail view
- Recipe create/edit form
- Collections interface
- Mobile responsive layouts

Would you like me to create wireframes for these key screens?

---

**End of Document**
