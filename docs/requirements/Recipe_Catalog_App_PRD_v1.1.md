# Recipe Catalog App - Product Requirements Document

**Version:** 1.1  
**Date:** November 14, 2025  
**Status:** Draft

---

## Executive Summary

A web application that allows users to import, organize, search, and discover recipes. Recipes can be imported from a companion browser extension (JSON format) or entered manually through the app interface. User accounts enable cloud storage and cross-device access while maintaining strong privacy protections.

### Product Vision

To create the most intuitive and privacy-focused personal recipe management system that helps home cooks organize their digital recipe collection and make cooking easier.

### Target Audience

- Home cooks who save recipes from various websites
- People who want to organize family recipes digitally
- Food enthusiasts building personal recipe collections
- Anyone frustrated with scattered bookmarks and printed recipes

---

## Product Principles

1. **Privacy First**: No user tracking, minimal data collection, clear attribution
2. **Simplicity**: Easy to use, fast to load, intuitive interface
3. **Flexibility**: Support both imported and manually entered recipes
4. **Respect**: Always credit recipe sources appropriately
5. **Reliability**: User data is secure, backed up, and always accessible

---

## Technical Architecture

**Decided on November 14, 2025**

### Backend Framework
**FastAPI (Python)**
- Automatic API documentation (OpenAPI/Swagger)
- Built-in data validation with Pydantic
- Async support for handling multiple requests
- Fast development velocity
- Easy to deploy on multiple platforms

### Frontend Framework
**SvelteKit**
- Fast development velocity
- Built-in routing and server-side rendering (SSR)
- Minimal boilerplate code
- Excellent developer experience
- Static export option for flexible deployment

### Database
**SQLite (Cloudflare D1) for MVP, PostgreSQL-ready architecture**
- D1 for Cloudflare deployment (managed SQLite)
- JSON storage support (similar to JSONB in PostgreSQL)
- Full-text search capabilities
- Migration path to PostgreSQL for scaling
- Efficient indexing for search and filtering

### Hosting Strategy
**Dual deployment option:**

1. **Cloudflare Ecosystem (Primary)**
   - Frontend: Cloudflare Pages
   - Backend API: Cloudflare Workers (Python support)
   - Database: Cloudflare D1 (SQLite)
   - Benefits: Zero-cost initial deployment, global CDN, automatic HTTPS
   
2. **Self-Hosted Proxmox (Alternative/Backup)**
   - Docker containers for all services
   - PostgreSQL instead of D1
   - Full control over infrastructure
   - Can run behind Cloudflare Tunnel for SSL/CDN

### Image Storage
**Base64 encoding in recipe JSON**
- Self-contained recipe data (no separate object storage)
- Easy export/import of complete recipes
- No broken image links or orphaned files
- Simplified architecture for MVP
- Migration path to CDN (R2/S3) post-MVP if needed

**Image Optimization:**
- Client-side compression before upload
- Maximum 5MB per image
- Target resolution: 1200px max width
- Quality: 85% JPEG or WebP format
- Lazy loading in list views

---

## MVP Features (Version 1.0)

### 1. User Authentication & Accounts

**User Story**: As a user, I want to create an account so I can access my recipes from any device.

**Functional Requirements**:
- User registration with email and password
- Email verification for new accounts
- Secure password requirements (minimum 12 characters, complexity rules)
- Password reset functionality
- Session management with persistent login option
- Account deletion with data export option

**Privacy Commitments**:
- No tracking scripts or analytics beyond essential error monitoring
- No third-party data sharing
- No email marketing without explicit opt-in
- Minimal data collection: email, password hash, and recipe data only
- Clear privacy policy displayed during registration

**Acceptance Criteria**:
- Successful registration sends verification email within 30 seconds
- Login session persists for 30 days with "remember me" option
- Password reset link expires after 1 hour
- Account deletion removes all user data within 24 hours
- Privacy policy is clearly accessible and readable

**Non-Functional Requirements**:
- Secure password storage (industry-standard hashing)
- HTTPS only
- Protection against common security vulnerabilities

---

### 2. Recipe Import from Browser Extension

**User Story**: As a user, I want to import recipes from my browser extension so I can build my personal recipe collection.

**Functional Requirements**:
- API endpoint that accepts JSON recipe data from browser extension
- Parse and validate recipe structure against expected schema
- Store recipes in cloud database associated with user account
- Handle duplicate detection based on source URL
- Support batch import of multiple recipes
- Display import confirmation with recipe name
- Handle both base64 image data and external image URLs

**Recipe JSON Schema**:
The system accepts recipes in the following JSON format:
- `name` (required): Recipe title
- `description`: Brief description of the dish
- `image`: Array of image objects with url, base64 data, and mimeType
- `author`: Recipe author information
- `datePublished`: Publication date
- `recipeYield`: Serving size/yield
- `prepTime`, `cookTime`, `totalTime`: Time durations
- `recipeCategory`: Array of categories (e.g., "Side Dish")
- `recipeCuisine`: Array of cuisine types (e.g., "German")
- `keywords`: Comma-separated keywords
- `recipeIngredient`: Array of ingredient strings
- `recipeInstructions`: Array of instruction steps
- `equipment`: Array of required equipment
- `notes`: Additional notes or tips
- `aggregateRating`: Rating information with value, count, best/worst
- `nutrition`: Nutritional information object
- `url`: Source URL of the recipe

**Acceptance Criteria**:
- Successfully import valid recipe JSON
- Store recipes associated with authenticated user only
- Reject malformed JSON with specific, helpful error messages
- Prevent duplicate URLs within a user's collection
- Import completes within 5 seconds per recipe
- Handle missing optional fields gracefully
- Preserve all data from original JSON

---

### 3. Manual Recipe Entry

**User Story**: As a user, I want to manually add recipes so I can include family recipes or recipes from non-web sources.

**Functional Requirements**:
- Recipe creation form with the following fields:
  - **Required Fields**: 
    - Recipe name
    - Ingredients (minimum 1)
    - Instructions (minimum 1)
  - **Optional Fields**:
    - Description
    - Image upload
    - Prep time, cook time, total time
    - Yield/servings
    - Category
    - Cuisine type
    - Keywords
    - Notes
    - Equipment
    - Source URL or attribution
    - Nutrition information

- Dynamic ingredient list (add/remove rows)
- Dynamic instruction steps (add/remove/reorder)
- Image upload functionality (maximum 5MB per image, jpg/png/webp formats)
- Auto-save draft every 30 seconds
- Store in same JSON format as browser extension imports
- Rich text editor for instructions with basic formatting (bold, italic, lists)

**Acceptance Criteria**:
- Form validates required fields before submission
- Images are optimized for web display while maintaining quality
- Draft recovery available if user navigates away
- Manually entered recipes are indistinguishable from imported ones in the UI
- Save completes within 2 seconds
- Clear error messages for validation failures
- Support for pasting formatted text

---

### 4. Recipe Display

**User Story**: As a user, I want to view my recipes in an attractive, readable format so I can easily follow them while cooking.

**Functional Requirements**:

**Display Elements**:
- Hero image with zoom/enlarge capability
- Recipe name (large, prominent heading)
- Description
- Source attribution with the following rules:
  - If URL exists: Display as "Source: [Website Name]" with clickable link
  - If manual entry: Display "Personal Recipe" or "Added Manually"
  - Date published (if available)
- Metadata section displaying:
  - Prep time, cook time, total time
  - Yield/servings
  - Cuisine type
  - Category
- Ingredients list with checkbox format for marking items
- Step-by-step instructions (numbered, large readable font)
- Nutrition information (collapsible/expandable section)
- Notes and tips section
- Rating display (if available from source)
- Keywords displayed as visual tags
- Origin badge: "Imported" vs "Manual Entry"

**Interaction Features**:
- Checkbox state persists during user session
- Print-friendly view option
- Responsive layout for mobile, tablet, and desktop
- Image gallery if multiple images exist

**Source Attribution Requirements**:
- Display source URL domain prominently (e.g., "Source: natashaskitchen.com")
- Make source clickable to open original recipe in new tab
- Clear visual distinction between imported and manual recipes
- Include publication date if available

**Acceptance Criteria**:
- All recipe data renders correctly without data loss
- Images load with graceful fallback for missing/broken images
- Print view excludes navigation and includes only recipe content
- Checked ingredients clear on page refresh but persist during active session
- Source attribution is clearly visible near recipe title
- Layout is readable on screens from 320px to 4K displays
- Recipe loads within 1 second

---

### 5. Recipe Listing & Dashboard

**User Story**: As a user, I want to see all my recipes in a browsable list so I can find what I'm looking for.

**Functional Requirements**:

**View Options**:
- Grid view (default): Visual cards with images
- List view: Compact text-based rows
- View toggle control easily accessible

**Recipe Card Display** (Grid View):
- Thumbnail image (square crop)
- Recipe name (with text truncation for long names)
- Cuisine badge/tag
- Total time with clock icon
- Source indicator (imported vs manual)
- Quick action buttons on hover/tap: View, Edit, Delete

**Recipe Row Display** (List View):
- Small thumbnail
- Recipe name
- Cuisine, category
- Time duration
- Quick actions

**Sort Options**:
- Recently added (default)
- Alphabetically A-Z
- Alphabetically Z-A
- Cooking time (shortest first)
- Cooking time (longest first)
- Recently viewed

**Additional Features**:
- Pagination: 24 recipes per page (grid), 50 per page (list)
- Recipe count display: "Showing X-Y of Z recipes"
- Empty state for new users with clear call-to-action
- Loading states for slow connections

**Acceptance Criteria**:
- Smooth scrolling performance with 1000+ recipes
- Grid layout adapts to screen size (1 column mobile, 2-4 columns desktop)
- Sort preference persists during user session
- Page load time under 2 seconds for any page
- Clear visual feedback for current sort order
- Thumbnails load progressively (lazy loading)

---

### 6. Recipe Editing

**User Story**: As a user, I want to edit my existing recipes so I can correct mistakes, update ingredients, or improve instructions.

**Functional Requirements**:
- Edit button on recipe detail view
- Pre-populate edit form with all existing recipe data
- Support editing all fields (same fields as manual entry)
- Maintain edit history/last modified timestamp
- Preserve recipe ID and creation date
- Handle editing of both imported and manually-entered recipes
- Validate edited data against same rules as creation
- Cancel button to discard changes
- Confirmation prompt if navigating away with unsaved changes

**Edit Restrictions**:
- Cannot edit source URL for imported recipes (read-only field)
- Cannot change "origin" badge (imported vs manual)
- Can add/modify all other fields including images

**Data Handling**:
- Update JSON in database with new values
- Preserve original import date
- Add/update "lastModified" timestamp
- If recipe was imported, add "modified" flag to metadata

**Acceptance Criteria**:
- Edit form loads with all existing data within 1 second
- All field types editable (text, arrays, images, times, etc.)
- Changes save successfully and reflect immediately in recipe view
- Validation prevents saving invalid data
- Source attribution remains accurate after edits
- Draft auto-save functionality works during editing (every 30 seconds)
- Original import source remains visible even after edits
- Success message displays after successful save
- Error messages are specific and actionable

**Non-Functional Requirements**:
- Optimistic UI updates (show changes immediately)
- Backend validation matches frontend validation
- No data loss if edit operation fails
- Edit history could be added post-MVP (version control)

---

### 7. User Collections/Folders

**User Story**: As a user, I want to organize my recipes into custom collections so I can group related recipes together.

**Functional Requirements**:

**Collection Management**:
- Create new collections with custom names
- Edit collection names
- Delete collections (with confirmation)
- View list of all user collections
- Default collections:
  - "All Recipes" (virtual collection, cannot be deleted)
  - "Favorites" (can be cleared but not deleted)
  - "Uncategorized" (recipes not in any collection)

**Recipe-Collection Relationship**:
- Add recipe to one or multiple collections
- Remove recipe from collection
- Recipes can exist in multiple collections simultaneously
- Adding to collection does NOT remove from other collections
- Deleting a collection does NOT delete recipes

**UI Components**:
- Collections sidebar/dropdown in main navigation
- "Add to Collection" button on recipe detail view
- Multi-select checkbox to add to collection during recipe creation/edit
- Collection badge/tags displayed on recipe cards
- Collection filter in recipe listing view
- Recipe count displayed per collection

**Collection Display Options**:
- Sort collections alphabetically or by creation date
- Display collection as filtered recipe list
- Show collection name in page header when viewing collection
- Empty state message for collections with no recipes

**Favorites Feature**:
- Heart/star icon on recipe cards and detail view
- One-click toggle to add/remove from Favorites collection
- Favorites is a special collection type

**Acceptance Criteria**:
- Create collection with name up to 50 characters
- Collection names must be unique per user
- Successfully add/remove recipes from collections
- Collection view displays only recipes in that collection
- Deleting collection requires confirmation and does NOT delete recipes
- Collection changes reflect immediately in UI
- Can assign recipe to multiple collections
- Favorites toggle works with single click
- Recipe cards show collection membership visually
- Collection creation/editing completes within 2 seconds

**Non-Functional Requirements**:
- Efficient queries when filtering by collection (indexed relationship)
- Collection limit: 50 collections per user (to prevent abuse)
- Recipes per collection: unlimited

**Database Schema Considerations**:
- Many-to-many relationship between recipes and collections
- Collections table: id, user_id, name, created_at, is_favorite
- Recipe_Collections junction table: recipe_id, collection_id
- Soft delete for collections (retain history)

---

### 8. Search Functionality

**User Story**: As a user, I want to search my recipes by various criteria so I can quickly find what I need.

**Functional Requirements**:

**Search Interface**:
- Search bar prominent in header (always visible)
- Clear/reset search button
- Search activates on typing (with brief delay to avoid excessive queries)

**Search Scope** (searches across):
- Recipe name (highest relevance weight)
- Ingredients
- Description
- Instructions
- Keywords
- Cuisine type
- Category

**Search Features**:
- Real-time search results (300ms delay after typing stops)
- Partial word matching (e.g., "chick" finds "chicken")
- Case-insensitive search
- Search term highlighting in results
- Recent searches display (last 10, session-based)
- Multi-word search support (AND logic by default)

**Search Results Display**:
- Same card/list layout as main recipe listing
- Result count: "Found X recipes matching 'search term'"
- "No results" state with helpful suggestions:
  - Check spelling
  - Try different keywords
  - Browse all recipes link
- Results ranked by relevance

**Acceptance Criteria**:
- Search returns results within 500ms for collections of 5000+ recipes
- Relevance ranking works correctly (exact matches appear first)
- Special characters handled properly
- Search works with multiple words
- Search state persists when navigating back from recipe detail
- Empty search shows all recipes

---

### 9. Filtering

**User Story**: As a user, I want to filter recipes by common attributes so I can narrow down my options.

**Functional Requirements**:

**Filter Interface**:
- Filter panel/sidebar (collapsible on mobile)
- Filters work independently and in combination with search
- Applied filters display as removable chips/tags
- "Clear all filters" button
- Filter counts showing number of recipes in each option

**Filter Categories**:

1. **Cuisine Type**
   - Auto-generated from user's recipe collection
   - Multi-select checkboxes
   - Alphabetically sorted
   - Shows recipe count for each cuisine

2. **Category**
   - Auto-generated from user's recipe collection
   - Multi-select checkboxes
   - Common categories: Breakfast, Lunch, Dinner, Dessert, Snack, Side Dish, etc.
   - Shows recipe count for each category

3. **Cooking Time**
   - Under 30 minutes
   - 30-60 minutes
   - 1-2 hours
   - Over 2 hours
   - No time specified
   - Single or multi-select

4. **Source Type**
   - Imported from web
   - Manually entered
   - Multi-select

5. **Collections**
   - Filter by user-created collections
   - Multi-select checkboxes
   - Shows recipe count per collection

**Filter Logic**:
- Multiple selections within a category use OR logic (e.g., "Italian" OR "French")
- Multiple categories combined use AND logic (e.g., "Italian" AND "Under 30 min")
- Filters combine with search using AND logic

**Acceptance Criteria**:
- Filters update results in real-time (within 300ms)
- Filter state persists during session
- Filter combinations work correctly
- No performance degradation when multiple filters applied
- Filter counts update based on current search/filter state
- Mobile-friendly filter interface (drawer or modal)
- Clear visual indication of active filters

---

### 10. Data Export

**User Story**: As a user, I want to export my recipe data so I can back it up, migrate to another service, or use it offline.

**Functional Requirements**:

**Export Formats**:
1. **JSON Export** (complete data)
   - Single JSON file with all recipes
   - Preserves complete recipe schema
   - Includes all metadata, images (base64), ratings, etc.
   - Format compatible with browser extension import
   - Human-readable with proper indentation

2. **Markdown Export** (readable text)
   - Individual .md files per recipe OR single combined file
   - Human-readable format
   - Includes all text content (ingredients, instructions, notes)
   - Metadata as YAML frontmatter
   - Images as references (not embedded)

3. **Plain Text Export** (simple)
   - Basic text format
   - Recipe name, ingredients list, instructions
   - Minimal formatting
   - Good for printing or simple backup

**Export Options**:
- **Scope Selection**:
  - All recipes
  - Selected recipes (multi-select)
  - Specific collection
  - Favorites only
  - Date range (recipes added between dates)

- **Format Options**:
  - Single file vs. multiple files (for markdown/text)
  - Include images or exclude images
  - Include metadata (nutrition, ratings) or exclude

**User Interface**:
- Export button in account settings or main menu
- Modal/page with export options
- Format selector (radio buttons)
- Scope selector (dropdown + checkboxes)
- Preview of export structure
- Generate button triggers export
- Download link/button appears when ready
- Progress indicator for large exports

**Technical Implementation**:
- Server-side generation for large exports
- Client-side for small exports (<50 recipes)
- ZIP file for multiple-file exports
- Filename format: `recipes_export_YYYY-MM-DD.json` (or .zip, .md, .txt)
- Maximum export size: 100MB per request

**Acceptance Criteria**:
- JSON export contains all recipe data in valid JSON format
- Markdown export is human-readable and properly formatted
- Text export is clean and simple
- All export formats successfully download
- Large exports (500+ recipes) complete without timeout
- Progress indicator shows during generation
- Export filename includes date stamp
- Re-importing exported JSON works without errors
- Collections can be exported with their recipes
- Export completes within 30 seconds for 1000 recipes
- Clear error message if export fails

**Special Handling**:
- Images in JSON: Keep as base64 (already in recipe JSON)
- Images in Markdown: Option to include as base64 data URLs or exclude
- Images in Text: Exclude entirely (text-only format)
- Privacy: No user account data in export (only recipes)

**Non-Functional Requirements**:
- Exports are generated on-demand (not pre-computed)
- No persistent storage of export files on server
- Export generation uses background job for large sets
- Rate limiting: 5 exports per hour per user

---

### 11. Recipe Management (Delete & Duplicate)

**User Story**: As a user, I want to manage my recipe collection so I can keep it organized and up-to-date.

**Functional Requirements**:

**Delete Recipe**:
- Delete button accessible from recipe detail page and card quick actions
- Confirmation modal displaying:
  - Recipe name
  - Recipe image thumbnail
  - "Delete permanently" button (destructive styling)
  - "Cancel" button
  - Optional: "Don't ask again" checkbox (session only)
- Soft delete with 30-day recovery period
- Deleted recipes moved to "Trash" folder
- Permanent deletion after 30 days

**Duplicate Recipe**:
- "Duplicate" option in recipe menu
- Creates copy with " (Copy)" appended to name
- Opens immediately in edit mode
- Useful for creating variations of existing recipes

**Recipe Metadata** (tracked automatically):
- Created date and time
- Last modified date and time
- Import source (for browser extension imports)
- View count (tracked but not displayed in MVP)
- Manual vs imported flag

**Acceptance Criteria**:
- Deleted recipes removed from main listing immediately
- Confirmation always required for delete action (unless dismissed)
- No data loss during operations
- Clear success/error messages for all actions
- Trash folder accessible from main navigation
- Restore from trash functionality works correctly

---

### 12. User Settings & Profile

**User Story**: As a user, I want to manage my account settings and preferences.

**Functional Requirements**:

**Profile Settings**:
- Email address (with re-verification required if changed)
- Password change functionality
- Display name (optional)
- Time zone preference for accurate timestamps

**Application Preferences**:
- Default sort order for recipe listing
- Default view type (grid or list)
- Recipes per page preference
- Theme preference: Light/Dark/System (future enhancement)

**Data Management**:
- Export all recipes functionality (see Section 10)
- Recipe collection statistics:
  - Total number of recipes
  - Number of imported recipes
  - Number of manual entries
  - Number of collections
  - Account creation date
  - Storage used (future: if limits implemented)

**Privacy & Security**:
- View privacy policy link
- Active sessions management (view and revoke)
- Account deletion with warnings:
  - Prompt to export data first
  - Confirmation required
  - 24-hour grace period before permanent deletion
  - Clear explanation of what will be deleted

**Acceptance Criteria**:
- Email change requires verification of new email
- Password change logs out all other sessions
- Export generates within 30 seconds for 1000+ recipes
- Settings save immediately with visual confirmation
- Account deletion requires typing "DELETE" to confirm
- Clear navigation to settings from main menu

---

### 13. Data Privacy & Source Attribution

**User Story**: As a user, I want assurance that my data is private and that recipe sources are properly credited.

**Privacy Requirements**:
- No third-party tracking scripts
- No analytics beyond essential error monitoring
- No cookies except for authentication
- No email marketing without explicit opt-in
- Data is never sold or shared with third parties
- Clear privacy policy in plain language
- GDPR/CCPA compliance where applicable
- User data export available on request
- User data deletion honored within 24 hours

**Source Attribution Requirements**:
- Always display source URL when available
- Link to original recipe prominently
- Never claim ownership of imported recipes
- Clear distinction between imported and user-created content
- Respect copyright by linking to originals
- Attribution format: "Source: [Domain Name]" with clickable link
- Date published shown if available

**Acceptance Criteria**:
- Privacy policy accessible from all pages
- No third-party requests in browser network tab
- Source links open in new tab
- Attribution visible without scrolling on recipe page
- Clear "Personal Recipe" badge for manual entries

---

## Future Features (Post-MVP Roadmap)

### Phase 2: Enhanced Organization (Q2 2026)

**Advanced Tagging**
- User-created custom tags
- Auto-suggested tags based on ingredients
- Tag management interface (merge, rename, delete)
- Tag-based filtering in addition to categories

**Collection Enhancements**
- Share collections via public link (opt-in)
- Export collections as cookbooks (PDF)
- Collection cover images
- Collection descriptions

**Smart Lists**
- Recently viewed recipes
- Frequently cooked recipes (based on view count)
- "Cook this week" planning list
- Recipes not yet tried

**Export Enhancements**
- Export individual recipes to PDF with professional formatting
- Recipe card image for social media sharing
- Custom recipe book generation (PDF)
- Print multiple recipes at once

---

### Phase 3: Cooking Assistant Features (Q3 2026)

**Meal Planning**
- Weekly meal calendar view
- Drag-and-drop recipe scheduling
- Serving size calculator for planned meals
- Grocery list generation from meal plan
- Calendar export (iCal format)
- Meal prep suggestions

**Shopping List Generator**
- Auto-generate from selected recipes
- Consolidate duplicate ingredients across recipes
- Smart quantity aggregation
- Organize by grocery store section/aisle
- Mobile-friendly checkoff interface
- Share list with household members
- Integration with grocery delivery services

**Cooking Mode**
- Hands-free cooking interface
- Large text optimized for reading from distance
- Timer integration for each cooking step
- Progress tracking through recipe steps
- Keep screen awake during cooking
- Voice commands for navigation (future)
- Step-by-step photos if available

---

### Phase 4: Social & Sharing (Q4 2026)

**Recipe Sharing**
- Share individual recipes via public link
- Privacy controls per recipe (private/public)
- Generate recipe cards optimized for social media
- Copy recipe to another user's collection (with attribution)
- QR code generation for easy sharing

**Community Features** (Optional)
- Public recipe profiles (opt-in only)
- Follow other users
- Recipe recommendations based on saved recipes
- Trending recipes
- Curated collections from community

**Recipe Notes & Modifications**
- Personal cooking notes on any recipe
- Track modifications and substitutions made
- Success/failure ratings with private notes
- Photo uploads of finished dishes
- Version history for edited recipes
- Compare original vs modified version

---

### Phase 5: Intelligence & Advanced Search (Q1 2027)

**Smart Search Enhancements**
- Ingredient-based search: "What can I make with chicken, rice, and beans?"
- Dietary restriction filtering (vegetarian, vegan, gluten-free, dairy-free)
- Auto-detect allergens from ingredients
- Nutrition-based search (under X calories, high protein, low carb)
- "Similar recipes" recommendation engine
- Visual similarity search (find recipes with similar presentation)

**AI-Powered Features**
- Recipe summarization and highlights
- Ingredient substitution suggestions
- Automatic recipe scaling with intelligent adjustments
- Duplicate recipe detection with merge suggestions
- Auto-categorization and tagging improvements
- Recipe format normalization (clean up inconsistent data)
- Extract recipes from photos/screenshots (OCR)
- Convert recipe videos to text instructions

**Nutritional Intelligence**
- Enhanced nutrition data parsing and calculation
- Macro breakdown visualization
- Healthier alternative recipe suggestions
- Allergen detection and warnings
- Nutrition goals tracking
- Recipe modifications for dietary needs

---

### Phase 6: Mobile & Integrations (Q2 2027)

**Cross-Platform Apps**
- Native mobile apps (iOS and Android)
- Offline mode with background sync
- Progressive Web App (PWA) capabilities
- Desktop application (Electron)
- Apple Watch/Android Wear companion app

**Browser Extension Enhancements**
- Auto-categorization during import
- Duplicate detection before import
- Bulk import operations
- Import from recipe images (OCR)
- Import from YouTube cooking videos
- Save recipes from Instagram/TikTok
- Browser sidebar for quick access

**Third-Party Integrations**
- Fitness app sync (MyFitnessPal, Lose It, etc.)
- Smart home integration (Alexa, Google Home)
- Grocery delivery services (Instacart, Amazon Fresh)
- Kitchen appliance integration (smart ovens, thermometers)
- Calendar apps (Google Calendar, Apple Calendar)

---

## Success Metrics (MVP)

### Adoption & Growth Metrics
- **User Acquisition**: 70% of browser extension users create app accounts within 1 week
- **Recipe Import**: Average 15+ recipes imported per user in first week
- **Manual Entry**: 50% of users manually enter at least 1 recipe
- **Retention**: Week 4 retention rate of 40% or higher
- **Collection Usage**: 60% of users create at least one custom collection

### Engagement Metrics
- **Session Frequency**: Active users have 3+ sessions per week
- **Session Duration**: Average session length of 3-7 minutes
- **Search Usage**: Search functionality used in 50%+ of sessions
- **Edit Rate**: 30% of users edit at least one recipe within first month
- **Export Usage**: 10% of users export their data within first 3 months

### Quality Metrics
- **Uptime**: 99.5% availability
- **Import Success**: Less than 2% import failure rate
- **Error Rate**: Less than 0.5% application error rate
- **Performance**: Search results return in under 500ms (95th percentile)
- **Page Load**: Recipe pages load in under 1 second (95th percentile)

### User Satisfaction
- **Post-Registration Survey**: Average 4+ stars (out of 5)
- **Support Volume**: Support tickets from less than 5% of user base
- **Churn**: Account deletion rate below 10% annually
- **Net Promoter Score**: Target NPS of 40+ within 6 months

---

## Out of Scope for MVP

The following features are explicitly **NOT** included in the MVP release:

1. Mobile native applications (iOS/Android)
2. Offline functionality
3. Recipe sharing or social features (except export)
4. Meal planning or calendar features
5. Shopping list generation
6. Recipe recommendations or discovery
7. AI-powered features
8. Third-party integrations
9. Recipe import from sources other than the browser extension
10. Video content or cooking tutorials
11. User-to-user messaging
12. Recipe ratings or reviews (from other users)
13. Recipe modifications tracking
14. Advanced nutrition tracking
15. Dietary restriction management
16. Multi-language support
17. Recipe scaling calculator
18. Advanced print customization
19. Public recipe profiles
20. Recipe versioning/history (beyond last modified date)

---

## User Experience Principles

### Simplicity
- Every feature should have a clear purpose
- Reduce clicks to accomplish common tasks
- Avoid overwhelming users with options
- Progressive disclosure of advanced features

### Speed
- Fast page loads (under 2 seconds)
- Instant search results
- No unnecessary loading states
- Optimistic UI updates where appropriate

### Accessibility
- Keyboard navigation support
- Screen reader compatibility
- Sufficient color contrast
- Readable font sizes
- Clear focus indicators
- Alt text for all images

### Mobile-First
- Responsive design from 320px to 4K
- Touch-friendly tap targets (minimum 44x44px)
- Thumb-friendly navigation on mobile
- Optimized images for mobile bandwidth

### Error Prevention & Recovery
- Clear validation messages
- Confirm destructive actions
- Auto-save drafts
- Easy undo/recovery options
- Helpful error messages with next steps

### Data Portability
- Users can export their complete data at any time
- Export format is open and well-documented
- Imported recipes can be re-exported without data loss
- No vendor lock-in through proprietary formats

---

## Open Questions & Pending Decisions

### Business Model
**Question**: Is this a free app, or will we have pricing tiers?
- **Options**:
  - Completely free with no limits
  - Freemium (free tier with limits, paid tier with more features)
  - Paid subscription only (monthly/annual)
  - One-time purchase
- **Considerations**: Server costs, storage costs, sustainability
- **Current Direction**: Start free, add monetization options later
- **Decision needed by**: Before MVP development begins

### Recipe Storage Limits
**Question**: Should we impose limits on number of recipes per user?
- **Options**:
  - Unlimited recipes for all users
  - Tiered limits (e.g., 50 free, unlimited paid)
  - Storage-based limits (e.g., 1GB free, more for paid)
- **Considerations**: Database scaling costs, user expectations
- **Current Direction**: Start unlimited, monitor costs and usage
- **Decision needed by**: Before MVP development begins

### Branding
**Question**: What is the product name and branding?
- **Needed**:
  - Application name
  - Domain name
  - Logo and visual identity
  - Brand colors and fonts
- **Decision needed by**: Before marketing and design phase

### Browser Extension Compatibility
**Question**: Browser extension status and requirements
- **Status**: Extension already exists
- **Integration Questions**:
  - Which browsers does it support? (Chrome, Firefox, Safari, Edge?)
  - Does it need updates to integrate with the web app API?
  - How does authentication work between extension and web app?
- **Decision needed by**: Before API development begins

### Launch Strategy
**Question**: How should we roll out the product?
- **Options**:
  - Private beta with invite codes
  - Public beta with sign-up waitlist
  - Phased rollout by region
  - Full public launch
- **Target Dates**:
  - MVP completion target?
  - Beta testing period length?
  - Public launch date?
- **Decision needed by**: Project kickoff

---

## Assumptions

1. **Browser Extension**: A functional browser extension already exists
2. **Target Audience**: Primary users are English-speaking home cooks in North America
3. **Device Usage**: Users will primarily access via desktop web browsers initially
4. **Internet Connection**: Users have reliable internet access (offline mode is post-MVP)
5. **Recipe Sources**: Most recipes will come from popular recipe websites with schema.org markup
6. **User Technical Skill**: Users have basic web browsing skills
7. **Data Volume**: Average user will have 100-500 recipes in their collection
8. **Session Length**: Users will access recipes while actively cooking (short sessions)
9. **Privacy Expectations**: Users value data privacy and expect no tracking
10. **Mobile Usage**: While web-first, significant mobile usage is expected
11. **Development Velocity**: Solo developer with AI assistance (Claude Code) can deliver MVP in reasonable timeframe
12. **Image Sizes**: Users will upload reasonably-sized images (under 5MB) suitable for web display
13. **Collection Usage**: Average user will create 5-15 custom collections
14. **Export Frequency**: Data exports will be occasional (backup/migration) not frequent
15. **Deployment Platform**: Cloudflare ecosystem provides sufficient free tier for initial users

---

## Dependencies

### External Dependencies
1. **Browser Extension**: Recipe import functionality depends on working extension
2. **Recipe Websites**: Quality of imported data depends on source website markup
3. **Email Service**: Account verification and password reset require email delivery
4. **Hosting Provider**: Cloud infrastructure for application and database
5. **Image Storage**: Currently base64 in database, no separate storage needed
6. **Domain Registration**: Domain name for web application
7. **Cloudflare Account**: For Pages, Workers, and D1 database hosting
8. **Cloudflare Tunnel** (optional): For Proxmox self-hosted alternative

### Internal Dependencies
1. **Design System**: UI/UX design must be completed before implementation
2. **API Specification**: Backend API must be defined before frontend work
3. **Authentication System**: Must be implemented before other user-facing features
4. **Database Schema**: Must be finalized before data operations
5. **Testing Environment**: Required for QA before production deployment
6. **Image Processing Library**: For client-side image compression and optimization
7. **Export Generation Logic**: Background job system for large exports
8. **Collection Data Model**: Junction table and relationships before collection features

---

## Risks & Mitigation

### Technical Risks

**Risk**: Poor search performance with large recipe collections
- **Impact**: High - Core feature becomes unusable
- **Likelihood**: Medium
- **Mitigation**: Implement proper database indexing; full-text search implementation; load testing with large datasets; consider Elasticsearch post-MVP

**Risk**: Image storage costs become prohibitive (base64 in database)
- **Impact**: High - Affects business sustainability
- **Likelihood**: Low (with base64 approach)
- **Mitigation**: Client-side image compression; monitor database growth; migration path to R2/S3 if needed; consider storage limits

**Risk**: Browser extension integration failures
- **Impact**: High - Primary recipe import method fails
- **Likelihood**: Low
- **Mitigation**: Thorough integration testing; fallback to manual entry; clear error messages; extension documentation

**Risk**: SQLite (D1) performance limitations at scale
- **Impact**: Medium - May need database migration
- **Likelihood**: Medium
- **Mitigation**: Architecture designed for PostgreSQL migration; monitor performance metrics; plan migration path early

**Risk**: Cloudflare Workers limitations for FastAPI
- **Impact**: Medium - May need hosting change
- **Likelihood**: Low
- **Mitigation**: Test thoroughly on Workers; have Proxmox self-host as backup; containerized deployment ready

### Business Risks

**Risk**: Low user adoption
- **Impact**: High - Product doesn't find market fit
- **Likelihood**: Medium
- **Mitigation**: User research before launch; beta testing; gather feedback early; iterate based on user needs

**Risk**: Competitive products release similar features
- **Impact**: Medium - Differentiation becomes difficult
- **Likelihood**: High
- **Mitigation**: Focus on privacy and user experience differentiators; rapid iteration; listen to users

**Risk**: Scaling costs exceed budget
- **Impact**: High - Unsustainable operations
- **Likelihood**: Medium
- **Mitigation**: Monitor usage metrics; implement usage limits if needed; efficient architecture; Cloudflare free tier helps

**Risk**: Free model is unsustainable long-term
- **Impact**: High - Need to monetize or shut down
- **Likelihood**: Medium
- **Mitigation**: Architecture supports future monetization; monitor costs closely; build engaged user base first

### Legal/Compliance Risks

**Risk**: Copyright concerns over recipe storage
- **Impact**: High - Legal liability
- **Likelihood**: Low
- **Mitigation**: Always attribute sources; link to originals; consult legal counsel; clear ToS; fair use principles

**Risk**: Data privacy regulation compliance
- **Impact**: High - Fines or forced shutdown
- **Likelihood**: Low
- **Mitigation**: GDPR/CCPA compliance from day one; privacy-first architecture; legal review; data export/deletion

**Risk**: Terms of service violations with recipe websites
- **Impact**: Medium - Some sites may block or restrict access
- **Likelihood**: Medium
- **Mitigation**: Respect robots.txt; don't scrape directly; rely on user action via extension; link to originals

---

## Appendix

### Glossary

- **MVP**: Minimum Viable Product - Initial release with core features only
- **Recipe Schema**: Structured data format for recipe information (based on schema.org)
- **Browser Extension**: Software that extends browser functionality (Chrome extension, Firefox add-on, etc.)
- **Base64**: Encoding format for binary image data as text
- **Soft Delete**: Marking data as deleted without permanent removal (allows recovery)
- **Progressive Web App (PWA)**: Web application that works like a native app
- **API**: Application Programming Interface - System for software communication
- **HTTPS**: Secure web protocol for encrypted communication
- **CDN**: Content Delivery Network for fast content distribution
- **JSONB**: PostgreSQL's binary JSON data type with indexing capabilities
- **D1**: Cloudflare's managed SQLite database service
- **SvelteKit**: Full-stack framework for building web applications with Svelte
- **FastAPI**: Modern Python web framework for building APIs
- **Cloudflare Workers**: Serverless compute platform for running code at the edge
- **Cloudflare Pages**: Platform for deploying static sites and applications

### References

- Schema.org Recipe Markup: https://schema.org/Recipe
- GDPR Compliance: https://gdpr.eu/
- CCPA Overview: https://oag.ca.gov/privacy/ccpa
- Web Content Accessibility Guidelines (WCAG): https://www.w3.org/WAI/WCAG21/quickref/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SvelteKit Documentation: https://kit.svelte.dev/
- Cloudflare Workers Documentation: https://developers.cloudflare.com/workers/
- Cloudflare D1 Documentation: https://developers.cloudflare.com/d1/

### Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 14, 2025 | Product Team | Initial draft |
| 1.1 | Nov 14, 2025 | Product Team | Added recipe editing, collections, data export features; Added technical architecture decisions; Updated assumptions and dependencies |

---

## Approval

This Product Requirements Document requires approval from the following stakeholders before proceeding to development:

- [ ] Product Owner
- [ ] Engineering Lead
- [ ] Design Lead
- [ ] Business Stakeholder

**Approved By**: _________________  
**Date**: _________________

---

**End of Document**
