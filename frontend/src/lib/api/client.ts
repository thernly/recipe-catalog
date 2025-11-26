/**
 * API client for communicating with the backend
 */

import { auth } from '$lib/stores/auth';
import { API_V1_URL } from '$lib/config';

const API_URL = API_V1_URL;

interface RequestOptions extends RequestInit {
	requireAuth?: boolean;
}

/**
 * Typed API error with structured error information
 */
export class ApiError extends Error {
	constructor(
		message: string,
		public errorCode?: string,
		public details?: Record<string, any>,
		public status?: number
	) {
		super(message);
		this.name = 'ApiError';
	}
}

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
 * Make an authenticated API request
 */
export async function apiRequest<T>(
	endpoint: string,
	options: RequestOptions = {}
): Promise<T> {
	const { requireAuth = true, ...fetchOptions } = options;

	// Don't set Content-Type for FormData - let the browser set it with boundary
	const headers: HeadersInit = fetchOptions.body instanceof FormData
		? { ...fetchOptions.headers }
		: {
			'Content-Type': 'application/json',
			...fetchOptions.headers
		};

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
					throw new ApiError(
						errorData.message || errorData.detail || `HTTP error! status: ${retryResponse.status}`,
						errorData.error_code,
						errorData.details,
						retryResponse.status
					);
				}

				if (retryResponse.status === 204) {
					return {} as T;
				}

				return await retryResponse.json();
			}

			// Refresh failed, throw unauthorized error
			throw new ApiError('Authentication required', 'unauthorized', {}, 401);
		}

		// Handle non-2xx responses
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new ApiError(
				errorData.message || errorData.detail || `HTTP error! status: ${response.status}`,
				errorData.error_code,
				errorData.details,
				response.status
			);
		}

		// Handle 204 No Content
		if (response.status === 204) {
			return {} as T;
		}

		return await response.json();
	} catch (error) {
		// Re-throw ApiError as-is
		if (error instanceof ApiError) {
			console.error('API request failed:', {
				message: error.message,
				errorCode: error.errorCode,
				status: error.status,
				details: error.details
			});
			throw error;
		}

		// Wrap unexpected errors in ApiError
		console.error('API request failed:', error);
		throw new ApiError(
			error instanceof Error ? error.message : 'An unexpected error occurred',
			'network_error',
			{ originalError: error }
		);
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
