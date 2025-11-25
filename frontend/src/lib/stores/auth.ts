/**
 * Authentication store using Svelte stores.
 */
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { API_BASE_URL } from '$lib/config';

interface User {
	id: number;
	email: string;
	display_name: string | null;
	is_active: boolean;
	is_verified: boolean;
	created_at: string;
}

interface AuthState {
	user: User | null;
	isLoading: boolean;
}

// Initialize with no user (will check cookies on init)
const initialState: AuthState = {
	user: null,
	isLoading: false
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,

		/**
		 * Login with email and password
		 */
		async login(email: string, password: string): Promise<void> {
			update((state) => ({ ...state, isLoading: true }));

			try {
				const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ email, password }),
					credentials: 'include' // Send and receive cookies
				});

				if (!response.ok) {
					const error = await response.json();
					throw new Error(error.detail || 'Login failed');
				}

				// Login successful - cookies are set automatically
				// Fetch user profile
				const userResponse = await fetch(`${API_BASE_URL}/api/users/me`, {
					credentials: 'include' // Send cookies
				});

				if (!userResponse.ok) {
					throw new Error('Failed to fetch user profile');
				}

				const user = await userResponse.json();

				update((state) => ({
					...state,
					user,
					isLoading: false
				}));
			} catch (error) {
				update((state) => ({ ...state, isLoading: false }));
				throw error;
			}
		},

		/**
		 * Register new user
		 * Note: Does not automatically log in. Call login() separately if needed.
		 */
		async register(email: string, password: string, displayName?: string): Promise<void> {
			update((state) => ({ ...state, isLoading: true }));

			try {
				const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						email,
						password,
						display_name: displayName || null
					}),
					credentials: 'include'
				});

				if (!response.ok) {
					const error = await response.json();
					throw new Error(error.detail || 'Registration failed');
				}

				update((state) => ({ ...state, isLoading: false }));
			} catch (error) {
				update((state) => ({ ...state, isLoading: false }));
				throw error;
			}
		},

		/**
		 * Logout user
		 * @param redirect - If true, redirect to login page after logout
		 */
		async logout(redirect: boolean = false) {
			try {
				// Call backend logout to clear cookies
				await fetch(`${API_BASE_URL}/api/auth/logout`, {
					method: 'POST',
					credentials: 'include'
				});
			} catch (error) {
				console.error('Logout request failed:', error);
				// Continue with local logout even if backend call fails
			}

			set({
				user: null,
				isLoading: false
			});

			// Redirect to login page if requested and in browser
			if (redirect && browser) {
				window.location.href = '/auth/login';
			}
		},

		/**
		 * Initialize auth from cookies
		 */
		async init(): Promise<void> {
			if (!browser) {
				return;
			}

			update((state) => ({ ...state, isLoading: true }));

			try {
				const response = await fetch(`${API_BASE_URL}/api/users/me`, {
					credentials: 'include' // Send cookies
				});

				if (!response.ok) {
					// No valid auth cookie, clear user
					update((state) => ({
						...state,
						user: null,
						isLoading: false
					}));
					return;
				}

				const user = await response.json();

				update((state) => ({
					...state,
					user,
					isLoading: false
				}));
			} catch (error) {
				update((state) => ({
					...state,
					user: null,
					isLoading: false
				}));
			}
		},

		/**
		 * Reset store to initial state (for testing)
		 */
		reset(): void {
			set(initialState);
		}
	};
}

export const auth = createAuthStore();

// Derived store for checking if user is authenticated
export const isAuthenticated = derived(auth, ($auth) => $auth.user !== null);
