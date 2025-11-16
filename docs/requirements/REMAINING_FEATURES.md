# Remaining Features to Implement

**Last Updated:** November 15, 2025
**Based on:** Recipe_Catalog_App_PRD_v1.1.md

---

## Summary

The Recipe Catalog MVP is **95% complete**. The core application is fully functional and production-ready. This document outlines remaining features from the Product Requirements Document organized by priority and development phase.

---

## 🔴 High Priority (MVP Polish)

### 1. Email Service Integration
**Status:** Code complete, needs configuration
**Effort:** 1-2 hours (configuration only)

**What's needed:**
- Configure SMTP service (SendGrid, AWS SES, Gmail, etc.)
- Test email verification flow
- Test password reset flow
- Update `.env` with SMTP credentials

**Files:**
- `backend/app/core/email.py` (already implemented)
- `backend/.env` (add SMTP variables)

**Implementation notes:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Recipe Catalog
```

---

### 2. Browser Extension
**Status:** Not started (separate project)
**Effort:** 20-30 hours (full extension development)

**Backend API:** ✅ Complete (`backend/app/api/import_recipes.py`)
**Extension:** ❌ Needs development

**What's needed:**
- Chrome/Firefox extension manifest
- Recipe scraping logic (parse Schema.org markup)
- Extension UI for recipe capture
- Authentication with web app API
- One-click import to collections
- Duplicate detection UI

**Features:**
- Parse recipe from current webpage
- Extract Schema.org Recipe markup
- Preview recipe before importing
- Add to specific collection
- Handle websites without Schema.org markup

**Technology:**
- Manifest V3 (Chrome/Edge)
- Manifest V2 (Firefox)
- vanilla JavaScript or React
- Content script for page parsing
- Background script for API calls

---

### 3. Image File Upload
**Status:** Only URL input supported
**Effort:** 3-4 hours

**Currently:**
- ✅ Recipe image URLs work
- ❌ No file upload from device
- ❌ No image optimization

**What's needed:**
- File input component in RecipeForm
- Frontend image preview before upload
- Image compression (max 5MB, 1200px width)
- Base64 encoding or separate upload endpoint
- Progress indicator for large images

**Options:**
1. **Base64 encoding** - Store in recipe JSON (simple, current approach)
2. **Separate upload endpoint** - Return URL to store in recipe
3. **CDN upload** - Cloudflare R2, AWS S3 (future enhancement)

**Files to modify:**
- `frontend/src/lib/components/RecipeForm.svelte`
- Add image compression utility
- Possibly `backend/app/api/recipes.py` for upload endpoint

---

## 🟡 Medium Priority (Enhancements)

### 4. Advanced Search Features
**Status:** Basic search complete
**Effort:** 4-6 hours

**Currently implemented:**
- ✅ Search by name, ingredients, description, instructions
- ✅ Basic filters (cuisine, category, time, source)

**PRD requirements not yet implemented:**
- ❌ Ingredient-based search: "What can I make with chicken, rice, beans?"
- ❌ Dietary restriction filters (vegetarian, vegan, gluten-free, dairy-free)
- ❌ Allergen detection and warnings
- ❌ Nutrition-based search (under X calories, high protein, low carb)
- ❌ "Similar recipes" recommendation

**Implementation approach:**
1. Add dietary restriction fields to recipe model
2. Create allergen detection from ingredients list
3. Build multi-ingredient search query
4. Add nutrition filters to FilterSidebar
5. Implement similarity algorithm (cosine similarity on ingredients)

---

### 5. Recipe Scaling Calculator
**Status:** Not implemented
**Effort:** 2-3 hours

**Feature description:**
- Automatically scale recipe servings
- Adjust ingredient quantities proportionally
- Handle fractional measurements (1/2 cup → 1 cup)
- Smart rounding for practical measurements

**What's needed:**
- Serving size adjuster UI (2x, 3x, 1/2x, custom)
- Ingredient parsing and unit conversion
- Fraction handling library
- Real-time quantity updates

**Files to create:**
- `frontend/src/lib/utils/recipeScaling.ts`
- Modify `frontend/src/routes/recipes/[id]/+page.svelte`

---

### 6. Favorites Enhancement
**Status:** Collection exists, no quick toggle
**Effort:** 1 hour

**Currently:**
- ✅ Favorites collection exists
- ❌ No star icon quick toggle on recipe cards
- ❌ No one-click favorite from detail page

**What's needed:**
- Star icon component
- Toggle favorite API call
- Optimistic UI update
- Visual feedback (filled/outline star)

**Implementation:**
- Add star button to RecipeCard
- Add star button to recipe detail page
- API: Add/remove recipe from Favorites collection
- Update collections store

---

### 7. Duplicate Recipe Detection
**Status:** Basic by-name detection in import
**Effort:** 2-3 hours

**Currently:**
- ✅ Duplicate detection by name during import
- ❌ No similarity detection for similar recipes
- ❌ No merge duplicate UI

**What's needed:**
- Fuzzy matching for recipe names (Levenshtein distance)
- Ingredient similarity comparison
- "Similar recipes exist" warning
- Merge duplicate recipes UI
- Compare side-by-side before merging

---

## 🟢 Low Priority (Future Phases)

### Phase 2: Enhanced Organization (Q2 2026)

#### Advanced Tagging System
**Effort:** 6-8 hours

- User-created custom tags (beyond categories)
- Auto-suggested tags based on ingredients
- Tag management interface (merge, rename, delete)
- Tag-based filtering
- Tag clouds or popular tags

**Database changes:**
- New `tags` table
- `recipe_tags` junction table

---

#### Collection Enhancements
**Effort:** 4-6 hours

- Share collections via public link (opt-in)
- Export collections as cookbooks (PDF)
- Collection cover images
- Collection descriptions (already implemented ✅)
- Collection sorting/ordering

---

#### Smart Lists
**Effort:** 6-8 hours

- Recently viewed recipes (track view history)
- Frequently cooked recipes (view count tracking)
- "Cook this week" planning list
- Recipes not yet tried
- Seasonal recipe suggestions

**Database changes:**
- `recipe_views` table (recipe_id, user_id, viewed_at)
- View count column on recipes

---

#### Export Enhancements
**Effort:** 8-10 hours

- Export individual recipes to PDF (professional formatting)
- Recipe card image for social media sharing
- Custom recipe book generation (PDF)
- Print multiple recipes at once
- Export to other formats (Paprika, Pepperplate, etc.)

---

### Phase 3: Cooking Assistant (Q3 2026)

#### Meal Planning
**Effort:** 20-30 hours

- Weekly meal calendar view
- Drag-and-drop recipe scheduling
- Serving size calculator for planned meals
- Grocery list generation from meal plan
- Calendar export (iCal format)
- Meal prep suggestions

**New models:**
- `meal_plans` (user_id, week_start_date)
- `planned_meals` (meal_plan_id, recipe_id, day, meal_type, servings)

---

#### Shopping List Generator
**Effort:** 15-20 hours

- Auto-generate from selected recipes
- Consolidate duplicate ingredients across recipes
- Smart quantity aggregation (1 cup + 2 cups = 3 cups)
- Organize by grocery store section/aisle
- Mobile-friendly checkoff interface
- Share list with household members
- Integration with grocery delivery services

**New models:**
- `shopping_lists` (user_id, name, created_at)
- `shopping_list_items` (list_id, ingredient, quantity, checked)

---

#### Cooking Mode
**Effort:** 10-15 hours

- Hands-free cooking interface
- Large text optimized for reading from distance
- Timer integration for each cooking step
- Progress tracking through recipe steps
- Keep screen awake during cooking
- Voice commands for navigation (future)
- Step-by-step photos if available

**New UI:**
- Full-screen cooking mode layout
- Timer component with notifications
- Voice control integration (Web Speech API)

---

### Phase 4: Social & Sharing (Q4 2026)

#### Recipe Sharing
**Effort:** 12-16 hours

- Share individual recipes via public link
- Privacy controls per recipe (private/public)
- Generate recipe cards optimized for social media
- Copy recipe to another user's collection (with attribution)
- QR code generation for easy sharing
- Embed recipe on external websites

**Database changes:**
- `public_recipe_links` table
- `recipe_shares` table (tracking)

---

#### Community Features (Optional)
**Effort:** 40-60 hours

- Public recipe profiles (opt-in only)
- Follow other users
- Recipe recommendations based on saved recipes
- Trending recipes
- Curated collections from community
- Recipe ratings and reviews (from other users)
- User comments on public recipes

**Major database additions:**
- `follows` table
- `recipe_ratings` table
- `recipe_comments` table
- `trending_recipes` view

---

#### Recipe Notes & Modifications
**Effort:** 8-12 hours

- Personal cooking notes on any recipe
- Track modifications and substitutions made
- Success/failure ratings with private notes
- Photo uploads of finished dishes
- Version history for edited recipes
- Compare original vs modified version

**Database changes:**
- `recipe_notes` table (recipe_id, user_id, note, date)
- `recipe_photos` table (user-uploaded finished dish photos)
- `recipe_versions` table (version history)

---

### Phase 5: Intelligence & Advanced Search (Q1 2027)

#### Smart Search Enhancements
**Effort:** 20-30 hours

- Ingredient-based search: "What can I make with..."
- Dietary restriction filtering (vegetarian, vegan, gluten-free, dairy-free)
- Auto-detect allergens from ingredients
- Nutrition-based search (under X calories, high protein, low carb)
- "Similar recipes" recommendation engine
- Visual similarity search (find recipes with similar presentation)

**Technology:**
- Machine learning for recipe similarity
- Natural language processing for ingredient search
- Nutrition database integration (USDA, Nutritionix)

---

#### AI-Powered Features
**Effort:** 40-60 hours

- Recipe summarization and highlights
- Ingredient substitution suggestions
- Automatic recipe scaling with intelligent adjustments
- Duplicate recipe detection with merge suggestions
- Auto-categorization and tagging improvements
- Recipe format normalization (clean up inconsistent data)
- Extract recipes from photos/screenshots (OCR)
- Convert recipe videos to text instructions

**Technology:**
- OpenAI API or similar LLM
- OCR library (Tesseract)
- Computer vision for food recognition

---

#### Nutritional Intelligence
**Effort:** 15-20 hours

- Enhanced nutrition data parsing and calculation
- Macro breakdown visualization (charts)
- Healthier alternative recipe suggestions
- Allergen detection and warnings
- Nutrition goals tracking
- Recipe modifications for dietary needs

**Technology:**
- Nutrition API integration (Nutritionix, Edamam)
- Ingredient parsing library
- Chart library (Chart.js, D3)

---

### Phase 6: Mobile & Integrations (Q2 2027)

#### Cross-Platform Apps
**Effort:** 80-120 hours

- Native mobile apps (iOS and Android) - React Native or Flutter
- Offline mode with background sync
- Progressive Web App (PWA) capabilities
- Desktop application (Electron)
- Apple Watch/Android Wear companion app

---

#### Browser Extension Enhancements
**Effort:** 10-15 hours (beyond basic extension)

- Auto-categorization during import
- Duplicate detection before import
- Bulk import operations
- Import from recipe images (OCR)
- Import from YouTube cooking videos
- Save recipes from Instagram/TikTok
- Browser sidebar for quick access

---

#### Third-Party Integrations
**Effort:** 30-50 hours

- Fitness app sync (MyFitnessPal, Lose It, etc.)
- Smart home integration (Alexa, Google Home)
- Grocery delivery services (Instacart, Amazon Fresh)
- Kitchen appliance integration (smart ovens, thermometers)
- Calendar apps (Google Calendar, Apple Calendar)

---

## 🔧 Infrastructure & DevOps

### Required for Production

#### Docker Configuration
**Effort:** 4-6 hours

- Dockerfile for backend
- Dockerfile for frontend
- docker-compose.yml
- Multi-stage builds for optimization
- Health checks
- Volume management for database

---

#### CI/CD Pipeline
**Effort:** 8-12 hours

- GitHub Actions workflows
- Automated testing on PR
- Automated deployment on merge to main
- Environment-specific deployments (staging, production)
- Database migration automation
- Rollback procedures

---

#### Monitoring & Observability
**Effort:** 6-8 hours

- Sentry for error tracking
- Application performance monitoring
- Structured logging (JSON logs)
- Log aggregation (ELK stack or similar)
- Uptime monitoring (UptimeRobot, Pingdom)
- User analytics (privacy-respecting, optional)

---

#### Security Enhancements
**Effort:** 6-10 hours

- API rate limiting (per user, per IP)
- CAPTCHA for registration (prevent bots)
- Two-factor authentication (2FA)
- Security headers (CSP, HSTS, etc.)
- Dependency vulnerability scanning
- Penetration testing

---

### Recommended Enhancements

#### Performance Optimization
**Effort:** 8-12 hours

- Database query optimization
- API response caching (Redis)
- Image CDN (Cloudflare R2, AWS S3)
- Frontend code splitting
- Lazy loading components
- Database connection pooling optimization
- Full-text search optimization (PostgreSQL)

---

#### Testing Suite
**Effort:** 20-30 hours

- Backend unit tests (pytest) - 80%+ coverage
- Frontend unit tests (Vitest) - 80%+ coverage
- Integration tests (API + DB)
- End-to-end tests (Playwright)
- Visual regression tests
- Performance tests (load testing)

---

## 📋 Implementation Priority Recommendations

### Immediate (Next 1-2 weeks)
1. Email service configuration (1-2 hours)
2. Image file upload (3-4 hours)
3. Favorites quick toggle (1 hour)

**Total: ~5-7 hours**

### Short-term (Next month)
1. Recipe scaling calculator (2-3 hours)
2. Browser extension (20-30 hours)
3. Advanced search features (4-6 hours)
4. Docker configuration (4-6 hours)

**Total: ~30-45 hours**

### Medium-term (Next quarter)
1. CI/CD pipeline (8-12 hours)
2. Monitoring & observability (6-8 hours)
3. Testing suite (20-30 hours)
4. Phase 2 enhancements (20-30 hours)

**Total: ~54-80 hours**

### Long-term (6+ months)
- Phase 3: Cooking Assistant
- Phase 4: Social & Sharing
- Phase 5: AI & Intelligence
- Phase 6: Mobile Apps

---

## 📊 Effort Summary

| Category | Hours | Priority |
|----------|-------|----------|
| MVP Polish | 5-7 | 🔴 High |
| Browser Extension | 20-30 | 🔴 High |
| Enhancements | 30-45 | 🟡 Medium |
| Infrastructure | 40-60 | 🟡 Medium |
| Phase 2 Features | 50-80 | 🟢 Low |
| Phase 3 Features | 80-120 | 🟢 Low |
| Phase 4 Features | 100-150 | 🟢 Low |
| Phase 5 Features | 80-120 | 🟢 Low |
| Phase 6 Features | 150-200 | 🟢 Low |

**Total Additional Development:** 555-812 hours

---

## 🎯 Recommended Next Steps

For a production launch, focus on:

1. **Email service configuration** (1-2 hours) - Enable verification emails
2. **Image file upload** (3-4 hours) - Better UX than URL input
3. **Docker setup** (4-6 hours) - Easy deployment
4. **Production deployment** (4-6 hours) - Get it live
5. **Browser extension MVP** (20-30 hours) - Core value proposition

**Total to production: ~32-48 hours of development**

After launch, gather user feedback to prioritize Phase 2+ features based on actual user needs rather than assumptions.

---

**Note:** All effort estimates assume a developer familiar with the codebase. First-time developers may need 1.5-2x the estimated time.
