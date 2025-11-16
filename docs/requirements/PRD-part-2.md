# Recipe Catalog App - Product Requirements Document (Part 2)

**Version:** 2.0
**Date:** November 16, 2025
**Status:** Draft
**Previous Document:** Recipe_Catalog_App_PRD_v1.1.md

---

## Executive Summary

This document outlines the second phase of development for the Recipe Catalog App, building upon the successfully implemented MVP features. Based on comprehensive codebase analysis, **95% of MVP features are complete and production-ready**. This PRD consolidates:

1. **Outstanding MVP items** requiring completion
2. **Original roadmap features** from v1.1 PRD (Phases 2-6)
3. **New user-requested features** for enhanced functionality

The features are reorganized into a practical, prioritized roadmap that balances user value, technical feasibility, and logical build order.

### Current State Assessment

**MVP Implementation Status (as of November 16, 2025):**

✅ **Fully Implemented (11/13 features):**
- User Authentication & Accounts (needs SMTP configuration)
- Manual Recipe Entry
- Recipe Display
- Recipe Listing & Dashboard
- Recipe Editing
- User Collections/Folders
- Search Functionality
- Filtering
- Data Export (JSON/Markdown/Text)
- Recipe Management (delete, duplicate, trash)
- User Settings & Profile
- Privacy & Source Attribution

⚠️ **Partially Implemented (1 feature):**
- Recipe Import from Browser Extension (backend API ready, extension not built)

❌ **Not Yet Implemented:**
- All Phase 2-6 features from original PRD
- New user-requested features

---

## Product Principles for Phase 2+

Building on the original principles, we add:

1. **User-Centric Innovation**: Prioritize features users explicitly request
2. **Progressive Enhancement**: Add complexity gradually without breaking simplicity
3. **Multi-User Value**: Support both individual and collaborative cooking experiences
4. **Intelligent Assistance**: Leverage AI to reduce friction and inspire creativity
5. **Accessibility First**: Ensure all users can access and benefit from features

---

## Prioritized Feature Roadmap

### Phase 1: MVP Completion & Polish (Q1 2026)
**Timeline:** 2-4 weeks
**Focus:** Complete outstanding MVP items and production readiness

### Phase 2: Essential Enhancements (Q1-Q2 2026)
**Timeline:** 8-12 weeks
**Focus:** User-requested features that significantly improve core experience

### Phase 3: Collaborative & Planning Features (Q2-Q3 2026)
**Timeline:** 12-16 weeks
**Focus:** Multi-user support, meal planning, shopping lists

### Phase 4: AI-Powered Intelligence (Q3-Q4 2026)
**Timeline:** 16-20 weeks
**Focus:** AI recipe generation, smart suggestions, enhanced search

### Phase 5: Advanced Organization & Sharing (Q4 2026 - Q1 2027)
**Timeline:** 12-16 weeks
**Focus:** Advanced tagging, sharing, export enhancements

### Phase 6: Mobile & Integrations (Q1-Q2 2027)
**Timeline:** 16-24 weeks
**Focus:** Native apps, browser extensions, third-party integrations

---

## Phase 1: MVP Completion & Polish

**Goal:** Achieve 100% MVP feature completion and production readiness

### 1.1 Browser Extension Development

**User Story:** As a user, I want to easily import recipes from any website using a browser extension.

**Priority:** HIGH (Core MVP feature)

**Functional Requirements:**

**Extension Core:**
- Chrome Extension (primary)
- Firefox Add-on (secondary)
- Edge Extension (uses Chrome codebase)
- Safari Extension (future consideration)

**Recipe Detection:**
- Automatically detect Schema.org Recipe markup on websites
- Detect Open Graph recipe metadata
- Manual selection mode for non-standard sites
- Preview recipe data before import

**Import Workflow:**
- One-click import button appears on recipe websites
- Preview modal shows extracted recipe data
- User can edit fields before importing
- Select collection(s) during import
- Handle duplicate detection (skip, update, or create new)

**Technical Implementation:**
- Manifest V3 for Chrome/Edge
- Content script for page analysis
- Background service worker for API communication
- Popup UI for manual import and settings
- JWT token storage for authentication
- API integration with existing `/api/import/recipes/json` endpoint

**Extension Features:**
- Badge showing number of recipes on page
- Context menu "Import Recipe" option
- Bulk import for recipe listing pages
- Import history and stats
- Settings: default collection, duplicate handling

**Acceptance Criteria:**
- Successfully detects recipes on 95% of major recipe websites
- Import completes in under 3 seconds
- Handles authentication seamlessly
- Works offline (queues imports for later sync)
- Clear error messages for failed imports
- Extension passes Chrome/Firefox web store review

**Technical Considerations:**
- Use existing backend API (already implemented)
- Implement OAuth2 or JWT authentication flow
- Handle CORS properly
- Implement retry logic for failed imports
- Store user preferences in extension storage

---

### 1.2 Email Service Configuration

**User Story:** As a user, I want to receive email notifications for account verification and password resets.

**Priority:** HIGH (Production requirement)

**Functional Requirements:**

**Email Templates:**
- Account verification email with token link
- Password reset email with secure token link
- Welcome email after verification (optional)
- Account deletion confirmation (optional)

**SMTP Configuration:**
- Configure production SMTP service (SendGrid, AWS SES, or Mailgun)
- Set up sender domain and authentication
- Implement email template rendering system
- Add email queue for reliability

**Email Types:**
- Verification email (required)
- Password reset email (required)
- Security notifications (optional)
- Account activity alerts (optional, opt-in)

**Technical Implementation:**
- Backend: `backend/app/core/email.py` (already has structure)
- Use FastAPI BackgroundTasks for sending
- Template engine: Jinja2 for HTML emails
- Plain text fallback for all emails
- Unsubscribe mechanism for optional emails

**Acceptance Criteria:**
- Verification emails delivered within 30 seconds
- Password reset emails delivered within 30 seconds
- Email templates are mobile-responsive
- All emails include plain text version
- Bounce and complaint handling implemented
- Complies with CAN-SPAM Act

---

### 1.3 Production Deployment Checklist

**Priority:** HIGH

**Requirements:**

**Infrastructure:**
- Set up production Cloudflare Workers/Pages
- Configure Cloudflare D1 production database
- Set up database backups (daily)
- Configure CDN caching rules
- Set up monitoring and alerting

**Security:**
- Enable HTTPS only
- Configure CORS properly
- Set up rate limiting
- Enable security headers (CSP, HSTS, etc.)
- Implement request validation
- Set up WAF rules

**Performance:**
- Enable caching where appropriate
- Optimize database queries
- Set up CDN for static assets
- Implement lazy loading for images
- Database indexing review

**Monitoring:**
- Error tracking (Sentry or similar)
- Performance monitoring (New Relic or similar)
- Uptime monitoring
- Database performance monitoring
- Log aggregation

**Documentation:**
- API documentation (Swagger/OpenAPI)
- Deployment guide
- Environment variable documentation
- Backup and recovery procedures

---

## Phase 2: Essential Enhancements

**Goal:** Implement high-value user-requested features that enhance the core experience

### 2.1 Enhanced Themes & Accessibility

**User Story:** As a user, I want to customize my visual experience and ensure the app is accessible.

**Priority:** HIGH (User-requested, accessibility is critical)

**Functional Requirements:**

**Theme Options:**
1. **Classic Theme** (already implemented)
   - Charcoal #3D4451 + Saffron #F59E0B

2. **Professional Theme** (already implemented)
   - Navy #1E3A5F + Apricot #F97316

3. **Dark Mode** (NEW)
   - Deep charcoal/black background
   - Reduced eye strain for night cooking
   - Warm accent colors
   - OLED-friendly true blacks option

4. **High Contrast Theme** (NEW - Accessibility)
   - WCAG AAA compliant contrast ratios
   - Larger text by default
   - Bold visual boundaries
   - Reduced visual complexity
   - Optimized for low vision users

5. **System Theme** (NEW)
   - Follows OS light/dark preference
   - Auto-switches based on time
   - User can override system preference

**Theme Features:**
- Theme preview before applying
- Per-user preference saved to database
- Instant theme switching without reload
- Consistent theming across all pages
- Theme-aware images and icons
- Print styles independent of theme

**Accessibility Enhancements:**
- WCAG 2.1 Level AA compliance (minimum)
- Full keyboard navigation support
- Screen reader optimized (ARIA labels)
- Focus indicators clearly visible
- Skip navigation links
- Heading hierarchy properly structured
- Alt text for all images
- Sufficient color contrast in all themes
- Resizable text up to 200% without breaking layout
- No flashing or auto-playing animations

**Technical Implementation:**
- CSS custom properties for theming
- Theme service in frontend (`src/lib/stores/theme.ts`)
- User preference storage in database
- System preference detection via `prefers-color-scheme`
- Theme-specific CSS files or variables
- Accessibility audit with Lighthouse
- Screen reader testing

**Acceptance Criteria:**
- All themes pass WCAG AA contrast requirements
- High contrast theme passes WCAG AAA
- Theme persists across sessions
- System theme auto-detects and applies correctly
- All interactive elements keyboard accessible
- Screen reader announces all important changes
- Lighthouse accessibility score 95+

---

### 2.2 Recipe Export to PDF

**User Story:** As a user, I want to export recipes as beautifully formatted PDFs for printing or sharing.

**Priority:** MEDIUM (User-requested, high value for sharing)

**Functional Requirements:**

**Export Options:**

1. **Single Recipe PDF**
   - Export individual recipe to PDF
   - Professional layout and formatting
   - Includes recipe image
   - All metadata (times, yield, etc.)
   - Ingredients and instructions formatted clearly
   - Source attribution

2. **Collection as PDF Cookbook**
   - Export entire collection as multi-recipe PDF
   - Table of contents with page numbers
   - Collection cover page
   - Index by cuisine/category
   - Section dividers between recipes

3. **Multiple Selected Recipes**
   - Multi-select recipes from list
   - Export as single PDF document
   - Optional: organize by category

**PDF Formatting Options:**
- **Layout:** Portrait or Landscape
- **Size:** Letter (8.5x11), A4, or Recipe Card (4x6)
- **Style:** Modern, Classic, Minimal
- **Include/Exclude:**
  - Recipe images
  - Nutrition information
  - Notes and tips
  - Source attribution
  - Personal modifications

**PDF Features:**
- High-quality image rendering
- Page breaks between recipes
- Headers/footers with page numbers
- Hyperlinked table of contents
- Bookmarks for navigation
- Print-optimized formatting
- Proper margin spacing

**Technical Implementation:**

**Option 1: Server-Side Generation (Recommended)**
- Backend library: ReportLab (Python) or WeasyPrint
- Generate PDFs on backend
- Return downloadable file
- Cache generated PDFs (24-hour expiry)
- Background job for large collections

**Option 2: Client-Side Generation**
- Frontend library: jsPDF or pdfmake
- Generate in browser
- No server load
- Privacy-friendly (no data sent to server)
- Slower for large documents

**API Endpoints:**
- `GET /api/recipes/{id}/export/pdf` - Single recipe
- `POST /api/export/pdf` - Multiple recipes (IDs in body)
- `GET /api/collections/{id}/export/pdf` - Collection as cookbook

**Acceptance Criteria:**
- PDF exports look professional and print-ready
- Images are high quality but file size optimized
- PDFs under 10MB for single recipe
- Cookbook generation completes within 30 seconds for 50 recipes
- PDFs are searchable (text layer included)
- Links to sources are clickable
- Mobile users can generate and download PDFs
- Print directly from PDF without quality loss

---

### 2.3 Advanced Recipe Search Enhancements

**User Story:** As a user, I want to find recipes based on ingredients I have and my dietary needs.

**Priority:** MEDIUM

**Functional Requirements:**

**Ingredient-Based Search:**
- "What can I make with..." search mode
- Enter ingredients user has available
- Find recipes that match all or most ingredients
- Show recipes by "ingredient match percentage"
- Highlight missing ingredients
- Filter by "exact match only" or "partial match"

**Dietary Restriction Filters:**
- Vegetarian
- Vegan
- Gluten-free
- Dairy-free
- Nut-free
- Low-carb / Keto
- Paleo
- Whole30
- Custom dietary tags

**Allergen Detection:**
- Flag common allergens in ingredients
- Allergen filter/warning system
- User allergen profile (saved preferences)
- Clear allergen indicators on recipes

**Nutrition-Based Search:**
- Search by calorie range
- High protein recipes
- Low carb recipes
- Low fat recipes
- Search by specific nutrient values

**Search Improvements:**
- Fuzzy/typo-tolerant search
- Search suggestions as user types
- Search history (last 20 searches)
- Saved searches for quick access
- Similar recipes based on current recipe

**Technical Implementation:**

**Backend:**
- Ingredient parsing and normalization
- Build ingredient vocabulary/database
- Implement dietary tag extraction from ingredients
- Allergen keyword detection
- Enhanced search algorithm with relevance scoring

**Database Changes:**
- Add `dietary_tags` JSON field to recipes
- Add `allergens` JSON field
- Add `ingredients_normalized` for better search
- Create search index for ingredients
- Add user dietary preferences to UserPreferences

**Frontend:**
- Advanced search modal/page
- Ingredient input with autocomplete
- Dietary filter checkboxes
- Nutrition range sliders
- Search results with match indicators

**Acceptance Criteria:**
- Ingredient search returns relevant recipes
- Dietary filters work accurately
- Search handles misspellings gracefully
- Results load within 500ms
- Match percentage calculation is accurate
- Allergen warnings are reliable
- Mobile-friendly search interface

---

### 2.4 Recipe Image Upload Enhancement

**User Story:** As a user, I want to upload recipe photos from my device, not just URLs.

**Priority:** MEDIUM

**Functional Requirements:**

**Image Upload:**
- File upload from device (drag-drop or file picker)
- Support JPG, PNG, WebP, HEIC formats
- Multiple images per recipe (gallery)
- Reorder images (set primary image)
- Crop/resize before upload
- Image preview before saving

**Image Processing:**
- Client-side compression before upload
- Auto-resize to optimal web dimensions (1200px max width)
- Convert HEIC to JPG automatically
- Quality optimization (85% JPEG quality)
- Generate thumbnails for list view
- Base64 encoding for database storage

**Image Management:**
- Edit recipe to add/remove images
- Replace existing images
- Delete individual images from gallery
- Set featured/primary image
- Image metadata (upload date, size)

**User Experience:**
- Drag-and-drop image upload
- Visual upload progress indicator
- Image size warnings (>5MB)
- Instant preview after upload
- Clear error messages for unsupported formats
- Mobile camera integration

**Technical Implementation:**

**Frontend:**
- File input with drag-drop zone
- Image compression library: browser-image-compression
- Canvas API for client-side processing
- Preview component before upload
- Multi-image gallery component

**Backend:**
- Receive base64 encoded image data
- Validate image format and size
- Store in recipe JSON `image` array
- Size limit: 5MB per image, 20MB total per recipe

**Database:**
- Images stored as base64 in recipe JSON
- Alternative: Migrate to Cloudflare R2 for object storage (future)

**Acceptance Criteria:**
- Upload completes within 5 seconds for 5MB image
- Compressed images are 80-90% smaller with minimal quality loss
- Multiple images display in gallery format
- Drag-drop works on desktop
- Mobile camera integration works on iOS and Android browsers
- HEIC images automatically convert
- Upload progress shows clearly

---

## Phase 3: Collaborative & Planning Features

**Goal:** Enable meal planning, shopping lists, and multi-user collaboration

### 3.1 Shopping List Generator

**User Story:** As a user, I want to create shopping lists from recipes so I can easily buy ingredients.

**Priority:** HIGH (User-requested, high value)

**Functional Requirements:**

**Shopping List Creation:**
- Add ingredients from single recipe to shopping list
- Add ingredients from multiple recipes
- Add ingredients from meal plan
- Manually add custom items to list
- Create multiple shopping lists (e.g., "Thanksgiving", "Weekly Groceries")

**Ingredient Consolidation:**
- Automatically combine duplicate ingredients
- Smart quantity aggregation (2 cups + 1 cup = 3 cups)
- Unit conversion (tablespoons to cups, etc.)
- Handle fraction math (1/2 + 1/4 = 3/4)
- Ingredient parsing and normalization

**Shopping List Organization:**
- Auto-organize by grocery store sections/aisles:
  - Produce
  - Meat & Seafood
  - Dairy & Eggs
  - Bakery
  - Pantry/Dry Goods
  - Frozen
  - Beverages
  - Condiments & Sauces
  - Spices & Seasonings
- Manual reordering within sections
- Custom section creation

**List Management:**
- Check off items as purchased
- Add notes to items (e.g., "organic", "brand preference")
- Mark items as "already have" (skip purchasing)
- Remove items from list
- Clear completed items
- Share list with household members

**Shopping List Interface:**
- Mobile-optimized (primary use case)
- Large touch targets for checkboxes
- Clear visual distinction for checked items
- Show recipe source for each ingredient
- Search/filter items in list
- Quantity quick edit

**Data Model:**

```
ShoppingList:
  - id
  - user_id
  - household_id (for multi-user)
  - name
  - created_at
  - updated_at

ShoppingListItem:
  - id
  - shopping_list_id
  - ingredient_name
  - quantity
  - unit
  - recipe_id (source recipe)
  - category (grocery section)
  - is_checked
  - notes
  - order_index
```

**Technical Implementation:**

**Backend:**
- New API routes: `/api/shopping-lists/`
- Ingredient parsing library (e.g., ingredient-parser)
- Unit conversion logic
- Quantity aggregation algorithm
- Categorization logic (keyword-based initially)

**Frontend:**
- Shopping list creation modal
- Add from recipe button
- Drag-drop list organization
- Mobile-first UI design
- Offline support with sync

**Acceptance Criteria:**
- Successfully parse and combine ingredients from multiple recipes
- Unit conversions are accurate
- List categorization is 80%+ accurate
- Check/uncheck is instant (optimistic UI)
- Works offline and syncs when online
- Supports 500+ items per list
- Mobile interface is thumb-friendly
- Share list generates unique link

---

### 3.2 Meal Planning Calendar

**User Story:** As a user, I want to plan my meals for the week so I can organize my cooking and shopping.

**Priority:** HIGH (User-requested, high value)

**Functional Requirements:**

**Calendar Interface:**
- Weekly calendar view (default)
- Monthly calendar view
- Daily detail view
- Drag-and-drop recipes onto calendar
- Multiple meals per day (breakfast, lunch, dinner, snacks)

**Meal Planning Features:**
- Assign recipes to specific date/meal slot
- Copy week's plan to another week
- Recurring meals (e.g., "Taco Tuesday")
- Meal plan templates (save and reuse)
- Notes per day (e.g., "Birthday dinner")

**Recipe Integration:**
- Quick add from recipe collection
- Search recipes while planning
- Recipe preview in calendar
- Adjust servings for meal plan
- Mark meals as "cooked" or "skipped"

**Shopping List Integration:**
- Generate shopping list from week's meal plan
- Auto-consolidate all ingredients
- Select specific days to include
- Exclude already-cooked meals

**Calendar Features:**
- Color-coding by meal type or cuisine
- Print weekly meal plan
- Export to iCal format
- Share meal plan with household
- Mobile and desktop views

**Meal Plan Stats:**
- Nutritional summary for week
- Total cooking time estimate
- Cuisine variety indicator
- Budget estimate (future: ingredient pricing)

**Data Model:**

```
MealPlan:
  - id
  - user_id
  - household_id (for multi-user)
  - name
  - start_date
  - end_date

MealPlanEntry:
  - id
  - meal_plan_id
  - recipe_id
  - date
  - meal_type (breakfast, lunch, dinner, snack)
  - servings
  - notes
  - is_completed
  - completed_at
```

**Technical Implementation:**

**Backend:**
- New API routes: `/api/meal-plans/`
- Calendar logic for date ranges
- iCal export generation
- Nutritional aggregation across recipes

**Frontend:**
- Calendar component (FullCalendar.js or custom)
- Drag-drop library (dnd-kit)
- Recipe search/filter in planning mode
- Mobile-responsive calendar
- Print-friendly weekly view

**Acceptance Criteria:**
- Drag-drop recipes to calendar smoothly
- Calendar loads quickly with 100+ planned meals
- Shopping list generation includes all ingredients
- iCal export works with Google Calendar/Apple Calendar
- Mobile calendar is easy to navigate
- Meal plan persists across devices
- Print view is clean and readable
- Can plan meals up to 3 months in advance

---

### 3.3 Multi-User Tenancy (Household Sharing)

**User Story:** As a user, I want to share my recipe collection and meal plans with my family or household.

**Priority:** HIGH (User-requested, enables collaboration)

**Functional Requirements:**

**Household Concept:**
- User can create a household
- Invite members via email
- Accept/decline household invitations
- Leave household
- Remove members (by household owner)
- One user can be in multiple households

**Shared Resources:**
- **Recipe Collection**: All household members see shared recipes
- **Collections**: Shared collections visible to all members
- **Categories/Cuisines**: Shared custom categories and cuisines
- **Meal Plans**: Share weekly meal plans
- **Shopping Lists**: Collaborate on shopping lists

**Permission Levels:**
1. **Owner**: Full control, can add/remove members, delete household
2. **Admin**: Can manage recipes and collections
3. **Member**: Can view and use recipes, contribute to lists
4. **Viewer**: Read-only access

**Personal vs. Household:**
- User can toggle "Personal" vs. "Household" when creating recipes
- Personal recipes only visible to creator
- Household recipes visible to all members
- Collections can be personal or shared

**Household Features:**
- Household name and description
- Household settings page
- Member management interface
- Activity feed (who added what recipe)
- Recipe attribution (show who added recipe to household)

**Data Model:**

```
Household:
  - id
  - name
  - description
  - created_by (user_id)
  - created_at

HouseholdMember:
  - id
  - household_id
  - user_id
  - role (owner, admin, member, viewer)
  - joined_at
  - invited_by

HouseholdInvitation:
  - id
  - household_id
  - email
  - invited_by
  - token
  - status (pending, accepted, declined)
  - expires_at

Recipe:
  - household_id (nullable, null = personal)

Collection:
  - household_id (nullable, null = personal)
```

**Technical Implementation:**

**Backend:**
- New API routes: `/api/households/`
- Permission checking middleware
- Invitation email system
- Cascade permissions for recipes/collections
- Query filters for household vs. personal

**Frontend:**
- Household creation wizard
- Invite member modal
- Member management page
- Personal/Household toggle in recipe form
- Filter recipes by personal/household
- Household switcher (if user is in multiple)

**Acceptance Criteria:**
- User can create household and invite members
- Invitations sent via email with accept link
- Household recipes visible to all members
- Personal recipes remain private
- Permissions enforce correctly (member cannot delete owner's recipes)
- User can easily switch between personal and household views
- Leaving household does not delete personal recipes
- Activity log shows recent household changes
- Household supports up to 20 members

**Privacy Considerations:**
- Personal data (email, preferences) remains private
- Only shared recipes are visible to household
- User can opt out of sharing specific recipes
- Clear indication of what's shared vs. personal
- Leaving household revokes access immediately

---

## Phase 4: AI-Powered Intelligence

**Goal:** Leverage AI to create, suggest, and enhance recipes intelligently

### 4.1 AI Recipe Generation from Available Ingredients

**User Story:** As a user, I want AI to generate recipe ideas based on ingredients I have available.

**Priority:** HIGH (User-requested, innovative feature)

**Functional Requirements:**

**Ingredient Input:**
- Enter ingredients user has on hand
- Autocomplete from known ingredients
- Specify quantities (optional)
- Indicate ingredient preferences or restrictions

**AI Recipe Generation:**
- Generate 3-5 recipe suggestions based on ingredients
- Use existing recipe patterns from user's collection
- Prioritize recipes matching user's cuisine preferences
- Consider cooking time preferences
- Account for dietary restrictions
- Generate complete recipe with:
  - Name
  - Description
  - Ingredient list (with quantities)
  - Step-by-step instructions
  - Estimated cooking time
  - Difficulty level

**Recipe Refinement:**
- User can request variations
- Adjust serving size
- Request simpler/more complex versions
- Substitute specific ingredients
- Change cuisine style

**Save Generated Recipes:**
- Save AI-generated recipe to collection
- Edit before saving
- Mark as "AI-Generated" for tracking
- Provide feedback (thumbs up/down)
- Improve future suggestions based on feedback

**Generation Modes:**
- **Quick Meal**: Under 30 minutes
- **Gourmet**: More complex, impressive dishes
- **Healthy**: Focus on nutrition
- **Comfort Food**: Hearty, traditional dishes
- **Experimental**: Creative, unique combinations

**Technical Implementation:**

**AI Model Options:**

**Option 1: OpenAI GPT-4 API** (Recommended for MVP)
- Use GPT-4 for recipe generation
- Structured output with JSON mode
- Cost-effective with prompt caching
- Reliable and high-quality output

**Option 2: Anthropic Claude API**
- Alternative to OpenAI
- Good for detailed instructions
- Potentially better safety/alignment

**Option 3: Open-Source LLM (Future)**
- Deploy Llama 3 or Mixtral
- Host on-premise or cloud GPU
- Lower per-request cost at scale
- More control and privacy

**Implementation Architecture:**
- Backend service: `/api/ai/generate-recipe`
- Prompt engineering for recipe generation
- Structured output parsing
- Rate limiting per user (5 generations per day free tier)
- Optional: Streaming response for real-time generation

**Prompt Structure:**
```
Generate a recipe using these ingredients: {ingredients_list}

Requirements:
- Cuisine preference: {user_cuisine_preferences}
- Cooking time: {max_cooking_time}
- Dietary restrictions: {restrictions}
- Difficulty: {difficulty_level}
- Servings: {servings}

Format as JSON with fields:
- name
- description
- recipeIngredient (array)
- recipeInstructions (array)
- prepTime, cookTime, totalTime
- recipeYield
- recipeCuisine
- recipeCategory
```

**Data Model:**

```
AIRecipeGeneration:
  - id
  - user_id
  - input_ingredients (JSON)
  - parameters (JSON - preferences, restrictions)
  - generated_recipe_id (if saved)
  - feedback (thumbs_up, thumbs_down, null)
  - created_at
```

**Acceptance Criteria:**
- AI generates reasonable, cookable recipes
- Ingredients in generated recipe are realistic
- Instructions are clear and follow logical order
- Generation completes within 10 seconds
- User can save generated recipes
- Cost per generation under $0.10
- Generated recipes are unique (not copied from web)
- Handles unusual ingredient combinations gracefully
- Provides disclaimer about AI-generated content

---

### 4.2 AI Menu Suggestions Based on Dietary Preferences

**User Story:** As a user, I want AI to suggest weekly menu plans based on my dietary preferences and goals.

**Priority:** MEDIUM (User-requested, enhances meal planning)

**Functional Requirements:**

**User Preference Input:**
- Dietary restrictions (vegetarian, vegan, gluten-free, etc.)
- Calorie goals (if tracking nutrition)
- Cuisine preferences (Italian, Mexican, Asian, etc.)
- Cooking time availability (quick weeknight meals vs. weekend cooking)
- Household size (servings needed)
- Budget considerations (basic, moderate, premium ingredients)
- Ingredient dislikes/allergies

**Menu Generation:**
- Generate 7-day meal plan
- Breakfast, lunch, dinner, and optional snacks
- Balance variety (different cuisines throughout week)
- Nutritional balance across week
- Reuse ingredients across recipes (reduce waste)
- Include recipe details for each meal

**Menu Customization:**
- Regenerate specific days
- Swap out individual meals
- Adjust serving sizes
- Request variations (more protein, less carbs, etc.)
- Lock certain meals (keep, regenerate others)

**Shopping List Integration:**
- Auto-generate shopping list from menu
- Consolidate ingredients across week
- Organize by grocery sections
- Highlight staple vs. fresh ingredients

**Smart Suggestions:**
- Suggest leftover repurposing
- Batch cooking recommendations (cook once, eat multiple times)
- Meal prep tips
- Seasonal ingredient focus
- Use recipes from user's collection when possible

**Technical Implementation:**

**AI Model:**
- Use GPT-4 or Claude for menu planning
- Multi-turn conversation for refinement
- Consider user's existing recipes in suggestions

**Menu Planning Logic:**
- Analyze user's recipe collection
- Extract dietary patterns
- Use AI to:
  - Select recipes from collection
  - Generate new recipes to fill gaps
  - Balance nutrition across week
  - Minimize ingredient overlap/waste

**API Endpoints:**
- `POST /api/ai/generate-menu` - Generate menu
- `POST /api/ai/regenerate-day/{day}` - Regenerate specific day
- `POST /api/ai/swap-meal/{meal_id}` - Swap individual meal

**Prompt Structure:**
```
Generate a 7-day meal plan for a user with:
- Dietary preferences: {dietary_info}
- Household size: {servings}
- Cooking time availability: {time_preferences}
- Cuisine preferences: {cuisines}
- Budget: {budget_level}

Requirements:
- Variety: Different cuisines each day
- Nutrition: Balanced macros across week
- Efficiency: Reuse ingredients to reduce waste
- Time: Balance quick meals and weekend cooking

Use these existing recipes when possible:
{user_recipes_summary}

Output format: JSON array of 7 days with breakfast/lunch/dinner
```

**Data Model:**

```
AIMenuSuggestion:
  - id
  - user_id
  - preferences (JSON)
  - generated_menu (JSON - 7 days of meals)
  - meal_plan_id (if user accepts and saves)
  - feedback_rating (1-5 stars)
  - created_at
```

**Acceptance Criteria:**
- Menu generation completes within 20 seconds
- Menus are varied (no meal repeats within week)
- Nutritional balance is reasonable
- Ingredient reuse is efficient
- Shopping list is accurate
- User can refine menu without full regeneration
- Cost per menu generation under $0.20
- Menu respects all dietary restrictions
- Incorporates user's favorite recipes when relevant

---

### 4.3 Smart Recipe Enhancements

**User Story:** As a user, I want AI to help improve and enhance my recipes automatically.

**Priority:** LOW (Nice-to-have, enhances quality)

**Functional Requirements:**

**Auto-Categorization:**
- Detect cuisine type from ingredients/name
- Suggest recipe categories
- Extract dietary tags automatically
- Identify allergens from ingredient list

**Ingredient Substitution Suggestions:**
- Suggest substitutes for hard-to-find ingredients
- Dietary-specific substitutions (vegan, gluten-free)
- Budget-friendly alternatives
- Seasonal substitutions

**Recipe Enhancement:**
- Suggest missing steps in instructions
- Recommend complementary side dishes
- Wine/beverage pairing suggestions
- Cooking technique tips
- Equipment recommendations

**Nutrition Calculation:**
- Auto-calculate nutrition from ingredients
- Use USDA nutrition database
- Estimate if exact amounts not specified

**Duplicate Detection:**
- Find similar recipes in collection
- Suggest merging duplicates
- Highlight differences between similar recipes

**Recipe Normalization:**
- Standardize ingredient formatting
- Convert units to consistent system
- Fix grammar/spelling in instructions
- Extract cook times from text

**Technical Implementation:**
- Use GPT-4 for text analysis
- USDA FoodData Central API for nutrition
- Recipe similarity algorithm (embeddings)
- Background processing for large collections

**Acceptance Criteria:**
- Auto-categorization is 85%+ accurate
- Substitution suggestions are reasonable
- Nutrition calculations within 10% of actual
- Duplicate detection finds obvious duplicates
- User can accept/reject all suggestions
- Processing completes in under 5 seconds per recipe

---

## Phase 5: Advanced Organization & Sharing

**Goal:** Enhanced organization, sharing capabilities, and export improvements

### 5.1 Advanced Tagging System

**User Story:** As a user, I want to tag recipes with custom labels for better organization.

**Priority:** LOW

**Functional Requirements:**

**Tag Creation:**
- Create unlimited custom tags
- Tag names with emoji support
- Color coding for tags
- Tag categories/groups

**Tag Management:**
- Rename tags (applies to all tagged recipes)
- Merge duplicate tags
- Delete tags (with confirmation)
- Tag usage statistics

**Tag Application:**
- Add multiple tags to recipe
- Quick tag suggestions based on recipe
- Tag autocomplete while typing
- Recently used tags

**Tag-Based Features:**
- Filter recipes by tags (AND/OR logic)
- Tag cloud visualization
- Most-used tags widget
- Smart tag suggestions (AI-powered)

**Technical Implementation:**
- Many-to-many relationship (RecipeTags table)
- Tag suggestions via GPT-4
- Frontend tag input component

---

### 5.2 Recipe Sharing & Public Profiles

**User Story:** As a user, I want to share individual recipes or my entire collection with others.

**Priority:** MEDIUM

**Functional Requirements:**

**Share Individual Recipe:**
- Generate unique shareable link
- Recipe displayed in read-only view
- Includes source attribution
- Option to disable sharing
- Track view count (optional)

**Public Recipe Profile:**
- Opt-in public profile page
- Showcase selected recipes
- Custom profile URL (username-based)
- Bio and photo
- Social media links

**Collection Sharing:**
- Share entire collection via link
- Share specific collection
- Password-protected sharing (optional)
- Expiring share links

**Recipe Cards for Social Media:**
- Generate beautiful recipe card images
- Optimized for Instagram, Facebook, Pinterest
- Include recipe name, image, key info
- Custom branding/watermark

**Copy to Collection:**
- Other users can copy shared recipe to their collection
- Attribution to original creator maintained
- Original recipe source preserved

**Privacy Controls:**
- Granular sharing settings per recipe
- Public, unlisted, or private
- Disable copying (view-only)
- Revoke shared links

**Technical Implementation:**
- Public recipe view endpoint (no auth required)
- Social sharing metadata (OpenGraph, Twitter Cards)
- Image generation for recipe cards (Puppeteer or Canvas)
- Anonymous view tracking

---

### 5.3 Smart Lists & Recipe Insights

**User Story:** As a user, I want automatic organization based on my cooking behavior.

**Priority:** LOW

**Functional Requirements:**

**Smart Lists (Auto-Generated):**
- Recently Viewed (last 20)
- Frequently Cooked (by view count)
- Not Yet Tried
- Added This Week/Month
- Long Cooking Time (>2 hours)
- Quick Meals (<30 min)
- High-Rated (if ratings implemented)

**Cooking Insights:**
- Most-cooked cuisines
- Average cooking time
- Favorite categories
- Seasonal cooking trends
- Collection growth over time

**Recommendations:**
- "You might like" based on cooking history
- Trending recipes in user's style
- Seasonal recipe suggestions
- "Cook this tonight" daily suggestion

**Technical Implementation:**
- View tracking (existing: last_viewed_at)
- Aggregation queries for insights
- Simple recommendation algorithm
- Dashboard widgets for insights

---

## Phase 6: Mobile & Integrations

**Goal:** Native mobile apps, browser extension enhancements, and third-party integrations

### 6.1 Progressive Web App (PWA) Enhancement

**User Story:** As a user, I want to install the app on my phone and use it offline.

**Priority:** HIGH (Lower effort than native apps)

**Functional Requirements:**

**PWA Features:**
- Install prompt on mobile browsers
- Works offline with cached recipes
- Background sync for changes
- Push notifications (optional, opt-in)
- Home screen icon
- Full-screen mode

**Offline Functionality:**
- View cached recipes offline
- Search cached recipes
- Add/edit recipes (sync when online)
- Queue operations for later sync

**Service Worker:**
- Cache strategy for recipes
- Update notification
- Offline-first architecture
- Background sync API

**Technical Implementation:**
- Service worker with Workbox
- IndexedDB for offline storage
- Manifest.json configuration
- Push notification service (optional)

**Acceptance Criteria:**
- App installs on iOS and Android
- Offline mode works for 95% of features
- Sync happens automatically when online
- Install prompt appears appropriately
- App feels native on mobile

---

### 6.2 Native Mobile Apps (iOS & Android)

**User Story:** As a user, I want native mobile apps for the best mobile experience.

**Priority:** MEDIUM (Higher effort, better UX)

**Approach Options:**

**Option 1: React Native**
- Single codebase for iOS and Android
- Large community and libraries
- Good performance
- Can reuse some web logic

**Option 2: Flutter**
- Single codebase
- Excellent performance
- Beautiful UI out of the box
- Growing ecosystem

**Option 3: Native (Swift/Kotlin)**
- Best performance and UX
- Full platform capabilities
- Two separate codebases
- Higher development cost

**Recommended:** React Native (balance of effort and quality)

**Mobile App Features:**
- All web features
- Native camera integration for recipe photos
- Share extension (share recipes from Safari/Chrome)
- Widget for quick recipe access
- Siri/Google Assistant shortcuts
- Barcode scanner for pantry items (future)
- Offline-first architecture

---

### 6.3 Third-Party Integrations

**User Story:** As a user, I want to connect my recipe app with other services I use.

**Priority:** LOW

**Potential Integrations:**

**Grocery Delivery:**
- Instacart integration (shopping list → cart)
- Amazon Fresh
- Walmart Grocery

**Nutrition Apps:**
- MyFitnessPal (sync recipes for calorie tracking)
- Lose It
- Cronometer

**Smart Home:**
- Alexa skill (voice-controlled recipes)
- Google Home integration
- Send recipe to smart display

**Calendar Apps:**
- Google Calendar (meal plan export)
- Apple Calendar
- Outlook Calendar

**Cloud Storage:**
- Auto-backup to Google Drive
- Dropbox backup
- iCloud sync

**Technical Implementation:**
- OAuth2 for third-party auth
- API integrations with respective services
- Webhook receivers for real-time sync
- Rate limiting and error handling

---

## Technical Architecture Updates

### Database Schema Additions

**New Tables Required:**

```sql
-- Shopping Lists
CREATE TABLE shopping_lists (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  household_id INTEGER,
  name TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (household_id) REFERENCES households(id)
);

CREATE TABLE shopping_list_items (
  id INTEGER PRIMARY KEY,
  shopping_list_id INTEGER NOT NULL,
  ingredient_name TEXT NOT NULL,
  quantity TEXT,
  unit TEXT,
  recipe_id INTEGER,
  category TEXT,
  is_checked BOOLEAN DEFAULT FALSE,
  notes TEXT,
  order_index INTEGER,
  FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(id),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

-- Meal Plans
CREATE TABLE meal_plans (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  household_id INTEGER,
  name TEXT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (household_id) REFERENCES households(id)
);

CREATE TABLE meal_plan_entries (
  id INTEGER PRIMARY KEY,
  meal_plan_id INTEGER NOT NULL,
  recipe_id INTEGER NOT NULL,
  date DATE NOT NULL,
  meal_type TEXT NOT NULL,
  servings INTEGER,
  notes TEXT,
  is_completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMP,
  FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

-- Households (Multi-User)
CREATE TABLE households (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE household_members (
  id INTEGER PRIMARY KEY,
  household_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',
  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  invited_by INTEGER,
  FOREIGN KEY (household_id) REFERENCES households(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (invited_by) REFERENCES users(id),
  UNIQUE(household_id, user_id)
);

CREATE TABLE household_invitations (
  id INTEGER PRIMARY KEY,
  household_id INTEGER NOT NULL,
  email TEXT NOT NULL,
  invited_by INTEGER NOT NULL,
  token TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'pending',
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (household_id) REFERENCES households(id),
  FOREIGN KEY (invited_by) REFERENCES users(id)
);

-- AI Interactions
CREATE TABLE ai_recipe_generations (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  input_ingredients TEXT,
  parameters TEXT,
  generated_recipe_id INTEGER,
  feedback TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (generated_recipe_id) REFERENCES recipes(id)
);

CREATE TABLE ai_menu_suggestions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  preferences TEXT,
  generated_menu TEXT,
  meal_plan_id INTEGER,
  feedback_rating INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id)
);

-- Tags
CREATE TABLE tags (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  color TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE(user_id, name)
);

CREATE TABLE recipe_tags (
  recipe_id INTEGER NOT NULL,
  tag_id INTEGER NOT NULL,
  PRIMARY KEY (recipe_id, tag_id),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id),
  FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- View Tracking (for insights)
CREATE TABLE recipe_views (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  recipe_id INTEGER NOT NULL,
  viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

-- Shared Recipes
CREATE TABLE recipe_shares (
  id INTEGER PRIMARY KEY,
  recipe_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  share_token TEXT UNIQUE NOT NULL,
  is_public BOOLEAN DEFAULT FALSE,
  password_hash TEXT,
  expires_at TIMESTAMP,
  view_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Updates to Existing Tables:**

```sql
-- Add to recipes table
ALTER TABLE recipes ADD COLUMN household_id INTEGER REFERENCES households(id);
ALTER TABLE recipes ADD COLUMN dietary_tags TEXT; -- JSON array
ALTER TABLE recipes ADD COLUMN allergens TEXT; -- JSON array
ALTER TABLE recipes ADD COLUMN view_count INTEGER DEFAULT 0;

-- Add to collections table
ALTER TABLE collections ADD COLUMN household_id INTEGER REFERENCES households(id);

-- Add to user_preferences table
ALTER TABLE user_preferences ADD COLUMN dietary_restrictions TEXT; -- JSON array
ALTER TABLE user_preferences ADD COLUMN allergen_profile TEXT; -- JSON array
ALTER TABLE user_preferences ADD COLUMN ai_credits INTEGER DEFAULT 100;
```

---

## API Endpoints Summary

### New Endpoints Required

**Shopping Lists:**
- `GET /api/shopping-lists/` - List all shopping lists
- `POST /api/shopping-lists/` - Create shopping list
- `GET /api/shopping-lists/{id}` - Get shopping list details
- `PATCH /api/shopping-lists/{id}` - Update shopping list
- `DELETE /api/shopping-lists/{id}` - Delete shopping list
- `POST /api/shopping-lists/{id}/items` - Add items
- `PATCH /api/shopping-lists/{id}/items/{item_id}` - Update item
- `DELETE /api/shopping-lists/{id}/items/{item_id}` - Remove item
- `POST /api/shopping-lists/from-recipes` - Generate from recipes
- `POST /api/shopping-lists/from-meal-plan/{meal_plan_id}` - Generate from meal plan

**Meal Plans:**
- `GET /api/meal-plans/` - List meal plans
- `POST /api/meal-plans/` - Create meal plan
- `GET /api/meal-plans/{id}` - Get meal plan
- `PATCH /api/meal-plans/{id}` - Update meal plan
- `DELETE /api/meal-plans/{id}` - Delete meal plan
- `POST /api/meal-plans/{id}/entries` - Add meal entry
- `PATCH /api/meal-plans/{id}/entries/{entry_id}` - Update entry
- `DELETE /api/meal-plans/{id}/entries/{entry_id}` - Remove entry
- `GET /api/meal-plans/{id}/shopping-list` - Generate shopping list
- `GET /api/meal-plans/{id}/export/ical` - Export to iCal

**Households:**
- `GET /api/households/` - List user's households
- `POST /api/households/` - Create household
- `GET /api/households/{id}` - Get household details
- `PATCH /api/households/{id}` - Update household
- `DELETE /api/households/{id}` - Delete household
- `GET /api/households/{id}/members` - List members
- `POST /api/households/{id}/invite` - Invite member
- `DELETE /api/households/{id}/members/{user_id}` - Remove member
- `POST /api/households/invitations/{token}/accept` - Accept invitation
- `POST /api/households/invitations/{token}/decline` - Decline invitation

**AI Features:**
- `POST /api/ai/generate-recipe` - Generate recipe from ingredients
- `POST /api/ai/generate-menu` - Generate meal plan
- `POST /api/ai/suggest-substitutions` - Ingredient substitutions
- `POST /api/ai/enhance-recipe/{recipe_id}` - Auto-enhance recipe
- `GET /api/ai/credits` - Check remaining AI credits

**Tags:**
- `GET /api/tags/` - List user's tags
- `POST /api/tags/` - Create tag
- `PATCH /api/tags/{id}` - Update tag
- `DELETE /api/tags/{id}` - Delete tag
- `POST /api/recipes/{recipe_id}/tags` - Add tags to recipe
- `DELETE /api/recipes/{recipe_id}/tags/{tag_id}` - Remove tag

**Sharing:**
- `POST /api/recipes/{id}/share` - Create share link
- `GET /api/recipes/{id}/share` - Get share settings
- `DELETE /api/recipes/{id}/share` - Revoke sharing
- `GET /api/share/{token}` - View shared recipe (public)

**Export Enhancements:**
- `GET /api/recipes/{id}/export/pdf` - Export recipe to PDF
- `POST /api/export/pdf` - Export multiple recipes to PDF
- `GET /api/collections/{id}/export/pdf` - Export collection as cookbook

---

## Dependencies & Prerequisites

### Phase 1 Dependencies
- SMTP service account (SendGrid, AWS SES, Mailgun)
- Browser extension development skills (JavaScript, Manifest V3)
- Chrome Web Store developer account

### Phase 2 Dependencies
- PDF generation library (ReportLab or WeasyPrint)
- Advanced CSS for themes
- Accessibility testing tools

### Phase 3 Dependencies
- Ingredient parsing library
- Unit conversion library
- Calendar component (FullCalendar.js)
- Email service for household invitations

### Phase 4 Dependencies
- OpenAI API account or Anthropic Claude API
- AI prompt engineering expertise
- USDA FoodData Central API (free)
- Budget for AI API costs

### Phase 5 Dependencies
- Image generation library (Puppeteer for recipe cards)
- Social sharing metadata implementation

### Phase 6 Dependencies
- React Native development environment
- Apple Developer account ($99/year)
- Google Play Developer account ($25 one-time)
- Mobile testing devices

---

## Success Metrics

### Phase 1 Metrics
- Browser extension installs: 1,000+ in first month
- Email verification rate: 80%+
- Import success rate: 95%+

### Phase 2 Metrics
- Dark mode adoption: 40%+ of users
- PDF exports: 30% of users export at least once
- Search satisfaction: 4+ stars average

### Phase 3 Metrics
- Shopping list creation: 50% of active users
- Meal planning adoption: 35% of active users
- Household creation: 20% of users create/join household

### Phase 4 Metrics
- AI recipe generation: 3+ recipes generated per user per month
- AI menu adoption: 20% of users try menu generation
- Positive AI feedback: 70%+ thumbs up rate

### Phase 5 Metrics
- Recipe sharing: 15% of recipes are shared
- Tag usage: 60% of users create custom tags
- Insights engagement: 40% view dashboard insights

### Phase 6 Metrics
- PWA installs: 40% of mobile users
- Mobile app downloads: 5,000+ in first 3 months
- Integration usage: 10% of users connect third-party app

---

## Cost Estimates

### Phase 1 Costs
- SMTP service: $0-50/month (depending on volume)
- Browser extension: $5 Chrome developer fee (one-time)
- Development time: 2-4 weeks

### Phase 2 Costs
- PDF generation: Minimal (server CPU cost)
- Theme development: Minimal
- Development time: 8-12 weeks

### Phase 3 Costs
- Email service: Covered in Phase 1
- Development time: 12-16 weeks

### Phase 4 Costs
- AI API costs: $0.01-0.20 per generation
- Monthly AI budget: $100-500 (scales with usage)
- Development time: 16-20 weeks

### Phase 5 Costs
- Image generation (Puppeteer): Minimal server cost
- Development time: 12-16 weeks

### Phase 6 Costs
- App store fees: $124/year (Apple $99 + Google $25)
- Mobile development: 16-24 weeks
- Push notification service: $0-100/month

---

## Risks & Mitigation

### AI Feature Risks
**Risk:** AI-generated recipes may be unsafe, inaccurate, or low quality
- **Mitigation:**
  - Add disclaimers about AI-generated content
  - Implement quality scoring/filtering
  - Allow user feedback to improve prompts
  - Human review of sample generations
  - Clear attribution of AI-generated content

**Risk:** AI API costs become prohibitive
- **Mitigation:**
  - Implement usage limits per user (free tier: 5/day)
  - Offer paid plans for higher usage
  - Cache common ingredient combinations
  - Consider open-source models for high-volume use

### Multi-User Risks
**Risk:** Privacy concerns with household sharing
- **Mitigation:**
  - Clear documentation of what's shared
  - Granular permission controls
  - Easy opt-out and data deletion
  - Household activity log for transparency

**Risk:** Abuse or spam in shared households
- **Mitigation:**
  - Limit household size (20 members max)
  - Owner can remove abusive members
  - Rate limiting on invitations
  - Report/block functionality

### Mobile App Risks
**Risk:** App store approval delays or rejections
- **Mitigation:**
  - Follow platform guidelines strictly
  - Test thoroughly before submission
  - Have legal/privacy policies ready
  - Plan 4-6 weeks for review process

**Risk:** Maintaining multiple codebases (web + mobile)
- **Mitigation:**
  - Use React Native to share logic
  - API-first architecture (already in place)
  - Automated testing for all platforms
  - Consistent design system

---

## Open Questions

### Phase 1
1. Which SMTP service should we use? (Recommendation: SendGrid for ease of setup)
2. Which browsers should the extension support first? (Recommendation: Chrome, then Firefox)
3. Should we charge for the browser extension? (Recommendation: Free, drives app adoption)

### Phase 2
1. Should PDF generation be server-side or client-side? (Recommendation: Server-side for quality)
2. How many custom themes should we support initially? (Recommendation: 4 as specified)

### Phase 3
1. Should shopping lists be shareable outside household? (Recommendation: Yes, via link)
2. Should meal plans support more than one week? (Recommendation: Yes, up to 4 weeks)
3. Household size limit? (Recommendation: 20 members max)

### Phase 4
1. Which AI provider? OpenAI or Anthropic? (Recommendation: OpenAI GPT-4 for MVP)
2. Free tier AI usage limits? (Recommendation: 5 generations per day)
3. How to handle AI costs long-term? (Recommendation: Freemium model)

### Phase 5
1. Should public profiles be opt-in or opt-out? (Recommendation: Opt-in for privacy)
2. Recipe sharing limits? (Recommendation: Unlimited for free users)

### Phase 6
1. Native apps or PWA only? (Recommendation: PWA first, native later)
2. Which integrations to prioritize? (Recommendation: Grocery delivery first)

---

## Implementation Priority Summary

### Immediate (Next 1-2 Months)
1. Browser Extension Development
2. Email Service Configuration
3. Production Deployment

### High Priority (2-4 Months)
4. Enhanced Themes & Dark Mode
5. Recipe Export to PDF
6. Advanced Search Enhancements
7. Image Upload Enhancement

### Medium Priority (4-8 Months)
8. Shopping List Generator
9. Meal Planning Calendar
10. Multi-User Tenancy

### Lower Priority (8-12 Months)
11. AI Recipe Generation
12. AI Menu Suggestions
13. Advanced Tagging
14. Recipe Sharing

### Long-Term (12+ Months)
15. Smart Recipe Enhancements
16. PWA Enhancement
17. Native Mobile Apps
18. Third-Party Integrations

---

## Appendix A: User-Requested Features Mapping

| User Request | PRD Section | Priority | Phase |
|--------------|-------------|----------|-------|
| Shopping list from ingredients | 3.1 Shopping List Generator | HIGH | Phase 3 |
| Weekly meal planning | 3.2 Meal Planning Calendar | HIGH | Phase 3 |
| AI recipe generation | 4.1 AI Recipe Generation | HIGH | Phase 4 |
| AI menu suggestions | 4.2 AI Menu Suggestions | MEDIUM | Phase 4 |
| Multi-user tenancy | 3.3 Multi-User Tenancy | HIGH | Phase 3 |
| Dark mode theme | 2.1 Enhanced Themes | HIGH | Phase 2 |
| High-contrast theme | 2.1 Enhanced Themes | HIGH | Phase 2 |
| Export recipes to PDF | 2.2 Recipe Export to PDF | MEDIUM | Phase 2 |

---

## Appendix B: Original PRD Phase Mapping

| Original PRD Phase | New PRD Phase | Status |
|--------------------|---------------|--------|
| Phase 2: Enhanced Organization | Phase 5 | Reorganized |
| Phase 3: Cooking Assistant | Phase 3 | Prioritized up |
| Phase 4: Social & Sharing | Phase 5 | Reorganized |
| Phase 5: Intelligence & Search | Phase 4 | Prioritized up |
| Phase 6: Mobile & Integrations | Phase 6 | Unchanged |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0 | Nov 16, 2025 | Product Team | Initial PRD Part 2 - Consolidated outstanding features from v1.1 and new user requests; Reorganized phases by priority; Added detailed requirements for high-priority features |

---

## Approval

This Product Requirements Document (Part 2) requires approval from the following stakeholders before proceeding to development:

- [ ] Product Owner
- [ ] Engineering Lead
- [ ] Design Lead
- [ ] Business Stakeholder
- [ ] AI/ML Lead (for Phase 4 features)

**Approved By**: _________________
**Date**: _________________

---

**End of Document**
