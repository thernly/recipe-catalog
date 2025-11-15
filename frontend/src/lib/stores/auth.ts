/**
 * Authentication store using Svelte stores.
 */
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

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
	token: string | null;
	isLoading: boolean;
}

// Initialize from localStorage if in browser
const initialState: AuthState = {
	user: null,
	token: browser ? localStorage.getItem('auth_token') : null,
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
				const response = await fetch('http://localhost:8000/api/auth/login', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ email, password })
				});

				if (!response.ok) {
					const error = await response.json();
					throw new Error(error.detail || 'Login failed');
				}

				const data = await response.json();

				// Store token
				if (browser) {
					localStorage.setItem('auth_token', data.access_token);
				}

				// Fetch user profile
				const userResponse = await fetch('http://localhost:8000/api/users/me', {
					headers: {
						Authorization: `Bearer ${data.access_token}`
					}
				});

				if (!userResponse.ok) {
					throw new Error('Failed to fetch user profile');
				}

				const user = await userResponse.json();

				update((state) => ({
					...state,
					user,
					token: data.access_token,
					isLoading: false
				}));
			} catch (error) {
				update((state) => ({ ...state, isLoading: false }));
				throw error;
			}
		},

		/**
		 * Register new user
		 */
		async register(email: string, password: string, displayName?: string): Promise<void> {
			update((state) => ({ ...state, isLoading: true }));

			try {
				const response = await fetch('http://localhost:8000/api/auth/register', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						email,
						password,
						display_name: displayName || null
					})
				});

				if (!response.ok) {
					const error = await response.json();
					throw new Error(error.detail || 'Registration failed');
				}

				// Auto-login after registration
				await this.login(email, password);
			} catch (error) {
				update((state) => ({ ...state, isLoading: false }));
				throw error;
			}
		},

		/**
		 * Logout user
		 */
		logout() {
			if (browser) {
				localStorage.removeItem('auth_token');
			}

			set({
				user: null,
				token: null,
				isLoading: false
			});
		},

		/**
		 * Initialize auth from stored token
		 */
		async init(): Promise<void> {
			const token = browser ? localStorage.getItem('auth_token') : null;

			if (!token) {
				return;
			}

			update((state) => ({ ...state, isLoading: true }));

			try {
				const response = await fetch('http://localhost:8000/api/users/me', {
					headers: {
						Authorization: `Bearer ${token}`
					}
				});

				if (!response.ok) {
					// Token is invalid, clear it
					this.logout();
					return;
				}

				const user = await response.json();

				update((state) => ({
					...state,
					user,
					token,
					isLoading: false
				}));
			} catch (error) {
				this.logout();
			}
		}
	};
}

export const auth = createAuthStore();

// Derived store for checking if user is authenticated
export const isAuthenticated = derived(auth, ($auth) => $auth.user !== null);
