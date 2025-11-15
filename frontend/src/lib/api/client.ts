/**
 * API client for communicating with the backend
 */

import { auth } from '$lib/stores/auth';
import { get } from 'svelte/store';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
	requireAuth?: boolean;
}

/**
 * Make an authenticated API request
 */
export async function apiRequest<T>(
	endpoint: string,
	options: RequestOptions = {}
): Promise<T> {
	const { requireAuth = true, ...fetchOptions } = options;

	const headers: HeadersInit = {
		'Content-Type': 'application/json',
		...fetchOptions.headers
	};

	// Add authentication token if required
	if (requireAuth) {
		const authState = get(auth);
		if (authState.token) {
			headers['Authorization'] = `Bearer ${authState.token}`;
		}
	}

	const url = `${API_URL}${endpoint}`;

	try {
		const response = await fetch(url, {
			...fetchOptions,
			headers
		});

		// Handle non-2xx responses
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
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
