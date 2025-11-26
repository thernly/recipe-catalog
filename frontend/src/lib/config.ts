/**
 * Application configuration
 * Uses environment variables with sensible defaults
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Versioned API base URL
 * All API calls should use this URL with the /api/v1 prefix
 */
export const API_V1_URL = `${API_BASE_URL}/api/v1`;
