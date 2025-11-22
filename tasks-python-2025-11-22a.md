# Python Code Quality Improvement Tasks
**Date:** 2025-11-22
**Project:** Recipe Catalog Backend
**Based on:** python-assess-2025-11-22.md

---

## Task Organization

Tasks are organized by priority and grouped into logical work units. Each task includes:
- **Priority Level**: Critical, High, Medium, Low
- **Estimated Effort**: S (Small), M (Medium), L (Large)
- **Dependencies**: What must be completed first
- **Files Affected**: Primary files to modify

---

## Critical Priority - Do Immediately

### Task 1: Add Linting and Formatting Configuration
**Priority:** Critical
**Effort:** S
**Dependencies:** None

**Description:**
Configure ruff and mypy in pyproject.toml to enforce code quality standards.

**Actions:**
- [x] Add `[tool.ruff]` section to pyproject.toml
  - Set line-length = 100
  - Set target-version = "py313"
  - Configure select rules: ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
  - Add ignore patterns for migrations
- [x] Add `[tool.ruff.lint.isort]` section
  - Configure import sorting
- [x] Add `[tool.mypy]` section
  - Set python_version = "3.13"
  - Enable strict mode
  - Add SQLAlchemy plugin: `plugins = ["sqlalchemy.ext.mypy.plugin"]`
  - Configure per-module overrides if needed
- [x] Install SQLAlchemy mypy support: `uv pip install sqlalchemy[mypy]`

**Files:**
- `pyproject.toml`

**Success Criteria:**
- ruff and mypy configurations present in pyproject.toml
- No configuration errors when running `uv run ruff check .`
- No configuration errors when running `uv run mypy .`

---

### Task 2: Run Code Formatters
**Priority:** Critical
**Effort:** M
**Dependencies:** Task 1

**Description:**
Format all Python code to establish consistent style baseline.

**Actions:**
- [x] Run ruff formatter: `uv run ruff format .`
- [x] Run ruff linter with auto-fix: `uv run ruff check --fix .`
- [x] Review changes for any breaking modifications
- [x] Run test suite to ensure formatting didn't break anything
- [x] Commit formatted code with message: "Apply ruff formatting and auto-fixes"

**Files:**
- All Python files in app/, tests/, and scripts/

**Success Criteria:**
- `uv run ruff format --check .` passes
- `uv run ruff check .` shows no fixable issues
- All tests still pass

---

### Task 3: Remove Unused CSRF Protection Code
**Priority:** Critical
**Effort:** S
**Dependencies:** None

**Description:**
Remove over-engineered CSRF protection that isn't needed for JWT-in-headers authentication.

**Actions:**
- [x] Remove CSRF token generation and validation functions from `app/core/security.py:119-162`
  - Delete `generate_csrf_token()`
  - Delete `validate_csrf_token()`
  - Delete `_csrf_tokens` set
- [x] Search for any CSRF imports and remove them
- [x] Check if any endpoints use CSRF validation and remove those calls
- [x] Remove any CSRF-related tests
- [x] Update any documentation that mentions CSRF

**Files:**
- `app/core/security.py`
- Any files importing CSRF functions
- Test files

**Success Criteria:**
- No CSRF-related code in codebase
- All tests pass
- No unused imports

---

### Task 4: Extract Recipe Export Logic to Service
**Priority:** Critical
**Effort:** L
**Dependencies:** None

**Description:**
Eliminate 200+ lines of duplicate code by creating a RecipeExporter service class.

**Actions:**
- [x] Create new file: `app/services/recipe_export.py`
- [x] Design RecipeExporter class with methods:
  - `export_json(recipe) -> dict`
  - `export_markdown(recipe) -> str`
  - `export_text(recipe) -> str`
  - `export_pdf(recipe) -> bytes`
- [x] Extract common metadata formatting logic to private method:
  - `_format_metadata(schema_recipe) -> dict`
- [x] Extract Schema.org conversion to method:
  - `_to_schema_org(recipe) -> dict`
- [x] Move HTML escaping logic from pdf_export.py to use stdlib `html.escape()`
- [x] Update `app/api/recipes.py:536-819` to use new RecipeExporter service
  - Inject RecipeExporter via dependency injection
  - Replace 4 export code paths with service calls
- [x] Add unit tests for RecipeExporter class
- [x] Remove duplicate code from recipes.py

**Files:**
- NEW: `app/services/recipe_export.py`
- MODIFY: `app/api/recipes.py`
- MODIFY: `app/utils/pdf_export.py`
- NEW: `tests/services/test_recipe_export.py`

**Success Criteria:**
- RecipeExporter service created and tested
- recipes.py export endpoint reduced from 284 lines to <50 lines
- All export formats still work correctly
- No duplicate metadata formatting logic
- All existing export tests pass

---

## High Priority

### Task 5: Split Large Recipe API File
**Priority:** High
**Effort:** L
**Dependencies:** Task 4

**Description:**
Break up 844-line recipes.py into smaller, focused modules.

**Actions:**
- [x] Create new directory: `app/api/recipes/`
- [x] Create `app/api/recipes/__init__.py` with router
- [x] Create `app/api/recipes/crud.py` for CRUD operations:
  - create_recipe
  - get_recipe
  - update_recipe
  - delete_recipe
  - list_recipes
- [x] Create `app/api/recipes/search.py` for search operations:
  - search_recipes
  - filter_by_tags
  - filter_by_ingredients
- [x] Create `app/api/recipes/export.py` for export operations:
  - export_recipe (using RecipeExporter service)
  - bulk_export
- [x] Update imports in `app/main.py`
- [x] Move tests to `tests/api/recipes/` directory structure
- [x] Update test imports

**Files:**
- NEW: `app/api/recipes/__init__.py`
- NEW: `app/api/recipes/crud.py`
- NEW: `app/api/recipes/search.py`
- NEW: `app/api/recipes/export.py`
- DELETE: `app/api/recipes.py`
- MODIFY: `app/main.py`
- REORGANIZE: `tests/api/recipes/`

**Success Criteria:**
- No single file over 500 lines
- Clear separation of concerns
- All tests pass
- API functionality unchanged

---

### Task 6: Add Comprehensive Type Hints
**Priority:** High
**Effort:** M
**Dependencies:** Task 1, Task 2

**Description:**
Improve type hint coverage from ~70% to >90%, replacing all `Any` types.

**Actions:**
- [x] Run mypy in strict mode to find missing type hints: `uv run mypy app/`
- [x] Fix all type errors in priority order:
  1. `app/utils/pdf_export.py` - Replace `Any` with `Recipe` model
  2. `app/services/ai.py` - Add return types to all methods
  3. `app/api/` endpoints - Ensure all endpoints have return types
  4. `app/core/` utilities - Add complete type coverage
- [x] Add missing return type hints to all functions
- [x] Fix SQLAlchemy `func.count` mypy errors using plugin
- [x] Add type hints to test files (use `pytest` types)
- [x] Run mypy again and ensure no errors

**Files:**
- `app/utils/pdf_export.py`
- `app/services/ai.py`
- `app/api/*.py`
- `app/core/*.py`
- `tests/*.py`

**Success Criteria:**
- `uv run mypy app/ --strict` passes with no errors
- No `Any` types except where truly necessary
- Type hint coverage >90%

---

### Task 7: Set Up Test Coverage Measurement
**Priority:** High
**Effort:** S
**Dependencies:** None

**Description:**
Add pytest-cov and establish coverage baseline, targeting 80%+ coverage.

**Actions:**
- [ ] Add pytest-cov to dev dependencies if not present
- [x] Create `.coveragerc` configuration file:
  - Exclude migrations, tests, and __init__.py
  - Set minimum coverage threshold
- [x] Run coverage: `uv run pytest --cov=app --cov-report=html --cov-report=term-missing`
- [x] Review coverage report in htmlcov/index.html
- [x] Identify files with <80% coverage
- [x] Add coverage badge/report to CI/CD
- [x] Document coverage in README

**Files:**
- NEW: `.coveragerc`
- MODIFY: `pyproject.toml` (if adding pytest-cov)
- MODIFY: `.github/workflows/` (if adding to CI)

**Success Criteria:**
- Coverage measurement working
- HTML coverage report generated
- Coverage metrics documented
- Baseline coverage established (current %)

---

### Task 8: Replace Manual Dict Construction with Pydantic
**Priority:** High
**Effort:** M
**Dependencies:** Task 6

**Description:**
Replace manual dictionary construction with Pydantic's model_validate().

**Actions:**
- [x] Identify all manual dict construction patterns:
  - `app/api/recipes.py:123-141` (18 lines of manual mapping)
  - Search for similar patterns in other files
- [x] Create Pydantic response schemas if missing
- [x] Replace manual dict construction with:
  ```python
  return RecipeSchema.model_validate(new_recipe)
  ```
- [x] Configure Pydantic ORM mode if needed
- [x] Update tests to verify response schemas
- [x] Remove old dict construction code

**Files:**
- `app/api/recipes.py`
- `app/api/shopping_lists.py`
- `app/api/collections.py`
- `app/schemas/*.py` (may need new schemas)

**Success Criteria:**
- No manual dict construction (18+ line blocks eliminated)
- All endpoints return Pydantic models
- Response validation automatic
- Code reduced by 100+ lines

---

## Medium Priority

### Task 9: Standardize Error Handling
**Priority:** Medium
**Effort:** M
**Dependencies:** None

**Description:**
Create custom exception classes and standardize error response format.

**Actions:**
- [x] Create `app/core/exceptions.py` with custom exceptions:
  - `RecipeNotFoundError`
  - `UnauthorizedAccessError`
  - `InvalidInputError`
  - `RateLimitExceededError`
  - `ExternalServiceError`
- [x] Add error codes enum:
  ```python
  class ErrorCode(str, Enum):
      RECIPE_NOT_FOUND = "RECIPE_NOT_FOUND"
      UNAUTHORIZED = "UNAUTHORIZED"
      # ... etc
  ```
- [x] Create standardized error response schema:
  ```python
  class ErrorResponse(BaseModel):
      error_code: str
      message: str
      details: Optional[dict] = None
  ```
- [x] Update exception handlers in `app/main.py`
- [x] Replace generic `HTTPException` with custom exceptions throughout codebase
- [x] Update error handling in:
  - `app/api/auth.py:139-152`
  - `app/services/ai.py:95-160`
  - All other API endpoints
- [x] Add tests for error handling
- [x] Document error codes in API documentation

**Files:**
- NEW: `app/core/exceptions.py`
- MODIFY: `app/main.py`
- MODIFY: `app/api/*.py`
- MODIFY: `app/services/*.py`
- NEW: `tests/test_exceptions.py`

**Success Criteria:**
- Custom exception classes defined
- Consistent error response format
- Error codes documented
- All endpoints use custom exceptions
- Error handling tests pass

---

### Task 10: Add Structured Logging
**Priority:** Medium
**Effort:** M
**Dependencies:** None

**Description:**
Implement structured logging with correlation IDs for better tracing.

**Actions:**
- [ ] Add `structlog` to dependencies
- [ ] Create `app/core/logging.py` with configuration:
  - JSON formatting for production
  - Pretty console for development
  - Correlation ID processor
- [ ] Create correlation ID middleware:
  ```python
  class CorrelationIdMiddleware:
      async def __call__(self, request, call_next):
          correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
          # Add to context
  ```
- [ ] Update logging calls to use structured logging:
  - Replace `logger.info(f"...")` with `logger.info("event", key=value)`
- [ ] Add logging to endpoints missing it:
  - Most API endpoints
  - Service layer operations
- [ ] Add exception logging to all exception handlers
- [ ] Add request/response logging middleware (optional)
- [ ] Update logging configuration in settings

**Files:**
- NEW: `app/core/logging.py`
- NEW: `app/middleware/correlation_id.py`
- MODIFY: `app/main.py`
- MODIFY: `app/core/config.py`
- MODIFY: All files with logging

**Success Criteria:**
- Structured logging configured
- Correlation IDs in all logs
- All API operations logged
- All exceptions logged with context
- JSON logs in production mode

---

### Task 11: Extract Magic Numbers to Constants
**Priority:** Medium
**Effort:** S
**Dependencies:** None

**Description:**
Replace magic numbers throughout codebase with named constants.

**Actions:**
- [ ] Create `app/core/constants.py` for global constants
- [ ] Identify all magic numbers:
  - `household_recipes[:50]` → `MAX_RECIPES_FOR_PROMPT = 50`
  - Password length checks → `MIN_PASSWORD_LENGTH = 8`
  - Token expiration times → `ACCESS_TOKEN_EXPIRE_MINUTES = 30`
  - File size limits
  - Pagination limits
  - Rate limits
- [ ] Define constants with clear names:
  ```python
  # app/core/constants.py
  MAX_RECIPES_IN_PROMPT = 50
  MIN_PASSWORD_LENGTH = 8
  MAX_UPLOAD_SIZE_MB = 10
  DEFAULT_PAGE_SIZE = 20
  MAX_PAGE_SIZE = 100
  ```
- [ ] Replace magic numbers with constants throughout codebase
- [ ] Update tests to use constants

**Files:**
- NEW: `app/core/constants.py`
- MODIFY: `app/utils/pdf_export.py`
- MODIFY: `app/services/ai.py`
- MODIFY: `app/api/*.py`
- MODIFY: `app/core/security.py`

**Success Criteria:**
- No unexplained magic numbers
- All limits defined as constants
- Constants documented with comments
- Easy to adjust configuration

---

### Task 12: Add API Versioning
**Priority:** Medium
**Effort:** M
**Dependencies:** Task 5 (recommended)

**Description:**
Implement API versioning to allow future changes without breaking clients.

**Actions:**
- [ ] Create versioning strategy (URL path versioning recommended)
- [ ] Update router structure:
  ```python
  # app/api/v1/__init__.py
  api_v1_router = APIRouter(prefix="/api/v1")
  ```
- [ ] Move current API routes to `/api/v1/`:
  - `/api/v1/auth`
  - `/api/v1/recipes`
  - `/api/v1/collections`
  - `/api/v1/households`
  - `/api/v1/shopping-lists`
- [ ] Keep backwards compatibility:
  - Redirect `/api/*` → `/api/v1/*` (with deprecation warning)
- [ ] Update OpenAPI docs to show version
- [ ] Update all tests to use versioned endpoints
- [ ] Update API documentation
- [ ] Add deprecation warning headers to old endpoints

**Files:**
- NEW: `app/api/v1/__init__.py`
- MODIFY: `app/main.py`
- MODIFY: `app/api/*.py` (move to v1/)
- MODIFY: All test files
- MODIFY: Documentation

**Success Criteria:**
- All endpoints under `/api/v1/`
- OpenAPI docs show version
- Tests use versioned endpoints
- Backward compatibility maintained
- Deprecation warnings in place

---

## Low Priority

### Task 13: Add Performance Tests
**Priority:** Low
**Effort:** M
**Dependencies:** Task 7

**Description:**
Add performance and load testing to identify bottlenecks.

**Actions:**
- [ ] Add `locust` or `pytest-benchmark` to dev dependencies
- [ ] Create `tests/performance/` directory
- [ ] Create performance test scenarios:
  - Recipe creation/retrieval under load
  - Search performance with large datasets
  - Export performance for large recipes
  - Shopping list operations
- [ ] Establish performance baselines
- [ ] Add performance tests to CI (optional, can be manual)
- [ ] Document performance metrics

**Files:**
- NEW: `tests/performance/test_recipe_performance.py`
- NEW: `tests/performance/test_search_performance.py`
- MODIFY: `pyproject.toml`

**Success Criteria:**
- Performance tests created
- Baselines established
- Slow operations identified
- Performance metrics documented

---

### Task 14: Simplify Over-Engineered Validation
**Priority:** Low
**Effort:** S
**Dependencies:** None

**Description:**
Simplify complex validation logic that doesn't provide practical value.

**Actions:**
- [ ] Simplify SECRET_KEY validation in `app/core/config.py:115-148`:
  - Remove weak key dictionary (ops responsibility)
  - Keep only length check
  - Remove complex entropy checks
- [ ] Review other validators for over-engineering
- [ ] Update tests for simplified validation

**Files:**
- `app/core/config.py`
- `tests/test_config.py`

**Success Criteria:**
- Simpler validation logic
- Tests still pass
- Security not compromised

---

### Task 15: Add Database Indexes
**Priority:** Low
**Effort:** S
**Dependencies:** None

**Description:**
Add database indexes for common query patterns to improve performance.

**Actions:**
- [ ] Analyze common queries:
  - Recipe searches by name, tags, ingredients
  - User lookups by email
  - Household filtering
- [ ] Identify missing indexes
- [ ] Create Alembic migration for new indexes:
  ```python
  op.create_index('idx_recipes_name', 'recipes', ['name'])
  op.create_index('idx_recipes_household_deleted', 'recipes', ['household_id', 'deleted_at'])
  ```
- [ ] Test query performance improvement
- [ ] Document index strategy

**Files:**
- NEW: `alembic/versions/xxx_add_performance_indexes.py`
- Documentation

**Success Criteria:**
- Indexes added for common queries
- Query performance improved
- Migration tested

---

## Testing & Validation Tasks

### Task 16: Expand Test Coverage
**Priority:** High (After Task 7)
**Effort:** L
**Dependencies:** Task 7

**Description:**
Add tests to reach 80%+ coverage, focusing on untested areas.

**Actions:**
- [ ] Review coverage report from Task 7
- [ ] Identify files with <80% coverage
- [ ] Add tests for:
  - Edge cases (very large uploads, invalid data)
  - Error conditions
  - Service layer methods
  - Utility functions
- [ ] Add integration tests (currently missing):
  - Full recipe CRUD workflow
  - Shopping list generation flow
  - Collection management flow
- [ ] Add missing edge case tests
- [ ] Re-run coverage and verify >80%

**Files:**
- `tests/**/*.py` (various test files)

**Success Criteria:**
- Overall coverage >80%
- No critical paths untested
- Edge cases covered
- Integration tests added

---

### Task 17: Update Documentation
**Priority:** Medium
**Effort:** S
**Dependencies:** Tasks 1-12

**Description:**
Update documentation to reflect code improvements.

**Actions:**
- [ ] Update README with:
  - Linting/formatting instructions
  - Coverage instructions
  - API versioning information
- [ ] Update CONTRIBUTING guide (if exists)
- [ ] Update API documentation
- [ ] Add inline code documentation where needed
- [ ] Update deployment docs with new requirements

**Files:**
- `README.md`
- `CONTRIBUTING.md` (if exists)
- API documentation files

**Success Criteria:**
- Documentation up-to-date
- New developers can onboard easily
- All new tools documented

---

## Summary Statistics

**Total Tasks:** 17
**Critical Priority:** 4 tasks
**High Priority:** 5 tasks
**Medium Priority:** 5 tasks
**Low Priority:** 3 tasks

**Estimated Effort:**
- Small tasks: 7
- Medium tasks: 7
- Large tasks: 3

**Expected Code Reduction:**
- ~200 lines from export logic extraction
- ~100 lines from Pydantic conversion
- ~44 lines from CSRF removal
- ~50 lines from constant extraction
- **Total: ~400 lines removed**

**Expected Improvements:**
- Type coverage: 70% → 90%+
- Test coverage: Unknown → 80%+
- Largest file: 844 lines → <500 lines
- Code duplication: Significant reduction
- Consistency: Major improvement

---

## Notes

1. **Order matters**: Some tasks have dependencies. Follow the suggested order.
2. **Test after each task**: Run the test suite after completing each task.
3. **Commit frequently**: Make atomic commits for each completed task.
4. **Review changes**: Code review each task before moving to the next.
5. **Measure impact**: Track metrics (coverage, file sizes, type hints) as you go.

**Estimated total effort:** 2-3 weeks for one developer working full-time, or 4-6 weeks part-time.
