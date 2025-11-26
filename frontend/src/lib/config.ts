/**
 * Application configuration
 * Uses environment variables with sensible defaults
 */

// In development, use relative URLs so Vite's proxy can forward requests
// In production, use the full API URL
// Use environment variable if set, otherwise empty string in dev (for proxy)
// or location.origin in production (same-origin deployment)
export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.PUBLIC_API_URL ||
  (import.meta.env.DEV ? "" : location.origin);

/**
 * Versioned API base URL
 * All API calls should use this URL with the /api/v1 prefix
 */
export const API_V1_URL = `${API_BASE_URL}/api/v1`;
