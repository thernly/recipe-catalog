/**
 * API client for communicating with the backend
 */

import { auth } from '$lib/stores/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
	requireAuth?: boolean;
	skipCsrf?: boolean;
}

// In-memory CSRF token storage
let csrfToken: string | null = null;

// Promise cache for refresh token to prevent concurrent refreshes
let refreshPromise: Promise<boolean> | null = null;

/**
 * Refresh the access token using the refresh token cookie
 */
async function refreshAccessToken(): Promise<boolean> {
	// Return existing promise if refresh is already in progress
	if (refreshPromise) {
		return refreshPromise;
	}

	refreshPromise = (async () => {
		try {
			const response = await fetch(`${API_URL}/api/auth/refresh`, {
				method: 'POST',
				credentials: 'include' // Send cookies
			});

			if (!response.ok) {
				// Refresh failed - logout user and redirect to login
				auth.logout(true);
				return false;
			}

			// Refresh successful - cookies are automatically updated
			return true;
		} catch (error) {
			console.error('Token refresh failed:', error);
			auth.logout(true);
			return false;
		} finally {
			// Clear the promise cache
			refreshPromise = null;
		}
	})();

	return refreshPromise;
}

/**
 * Fetch a new CSRF token from the backend
 */
async function fetchCsrfToken(): Promise<string> {
	const response = await fetch(`${API_URL}/api/auth/csrf-token`, {
		credentials: 'include'
	});
	if (!response.ok) {
		throw new Error('Failed to fetch CSRF token');
	}
	const data = await response.json();
	csrfToken = data.csrf_token;
	return csrfToken;
}

/**
 * Get the current CSRF token, fetching a new one if needed
 */
async function getCsrfToken(): Promise<string> {
	if (!csrfToken) {
		await fetchCsrfToken();
	}
	return csrfToken!;
}

/**
 * Make an authenticated API request
 */
export async function apiRequest<T>(
	endpoint: string,
	options: RequestOptions = {}
): Promise<T> {
	const { requireAuth = true, skipCsrf = false, ...fetchOptions } = options;

	// Don't set Content-Type for FormData - let the browser set it with boundary
	const headers: HeadersInit = fetchOptions.body instanceof FormData
		? { ...fetchOptions.headers }
		: {
			'Content-Type': 'application/json',
			...fetchOptions.headers
		};

	// Add CSRF token for state-changing requests
	const method = (fetchOptions.method || 'GET').toUpperCase();
	const isStateChanging = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);

	if (isStateChanging && !skipCsrf) {
		try {
			const token = await getCsrfToken();
			headers['X-CSRF-Token'] = token;
		} catch (error) {
			console.warn('Failed to get CSRF token:', error);
			// Continue without CSRF token - let backend validation handle it
		}
	}

	const url = `${API_URL}${endpoint}`;

	try {
		const response = await fetch(url, {
			...fetchOptions,
			headers,
			credentials: 'include' // Always send cookies
		});

		// Handle 401 Unauthorized - try to refresh token
		if (response.status === 401 && requireAuth) {
			// Try to refresh the access token
			const refreshed = await refreshAccessToken();

			if (refreshed) {
				// Retry the original request with refreshed token
				const retryResponse = await fetch(url, {
					...fetchOptions,
					headers,
					credentials: 'include'
				});

				if (!retryResponse.ok) {
					const errorData = await retryResponse.json().catch(() => ({}));
					throw new Error(errorData.detail || `HTTP error! status: ${retryResponse.status}`);
				}

				if (retryResponse.status === 204) {
					return {} as T;
				}

				return await retryResponse.json();
			}

			// Refresh failed, throw unauthorized error
			throw new Error('Authentication required');
		}

		// Handle non-2xx responses
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));

			// If CSRF validation failed, try to refresh the token and retry once
			if (response.status === 403 && errorData.detail?.includes('CSRF') && !skipCsrf) {
				try {
					await fetchCsrfToken(); // Get a fresh token
					headers['X-CSRF-Token'] = csrfToken!;

					// Retry the request
					const retryResponse = await fetch(url, {
						...fetchOptions,
						headers,
						credentials: 'include'
					});

					if (!retryResponse.ok) {
						const retryErrorData = await retryResponse.json().catch(() => ({}));
						throw new Error(retryErrorData.detail || `HTTP error! status: ${retryResponse.status}`);
					}

					if (retryResponse.status === 204) {
						return {} as T;
					}

					return await retryResponse.json();
				} catch (retryError) {
					// If retry fails, throw the original error
					throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
				}
			}

			throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
		}

		// Handle 204 No Content
		if (response.status === 204) {
			return {} as T;
		}

		return await response.json();
	} catch (error) {
		console.error('API request failed:', error);
		throw error;
	}
}

/**
 * Build query string from params object
 */
export function buildQueryString(params: Record<string, any>): string {
	const searchParams = new URLSearchParams();

	Object.entries(params).forEach(([key, value]) => {
		if (value !== undefined && value !== null && value !== '') {
			if (Array.isArray(value)) {
				value.forEach((item) => searchParams.append(key, String(item)));
			} else {
				searchParams.append(key, String(value));
			}
		}
	});

	const queryString = searchParams.toString();
	return queryString ? `?${queryString}` : '';
}
