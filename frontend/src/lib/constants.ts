/**
 * Application-wide constants
 * Centralizes magic numbers and configuration values for maintainability
 */

// ========================================
// Pagination
// ========================================

/**
 * Default number of items per page for recipe listings
 * 24 provides a good balance for grid layouts (4x6, 3x8, 2x12)
 */
export const DEFAULT_PAGE_SIZE = 24;

/**
 * Default starting page for paginated lists (1-indexed)
 */
export const DEFAULT_PAGE = 1;

// ========================================
// API Configuration
// ========================================

/**
 * Default timeout for API requests in milliseconds
 * 30 seconds allows for slower connections while preventing indefinite hangs
 */
export const REQUEST_TIMEOUT = 30000;

/**
 * Credentials mode for fetch requests
 * 'include' ensures cookies are sent for authentication
 */
export const FETCH_CREDENTIALS = 'include' as const;

// ========================================
// UI Configuration
// ========================================

/**
 * Duration toast notifications are displayed in milliseconds
 * 5 seconds gives users enough time to read without being intrusive
 */
export const TOAST_DURATION = 5000;

/**
 * Debounce delay for search inputs in milliseconds
 * 300ms provides responsive feel while reducing unnecessary API calls
 */
export const DEBOUNCE_DELAY = 300;

/**
 * Delay before auto-focusing elements in modals (in milliseconds)
 * Small delay ensures DOM is ready for focus management
 */
export const FOCUS_DELAY = 0;
