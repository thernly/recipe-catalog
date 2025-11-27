/**
 * Authentication store using Svelte stores.
 */
import { writable, derived } from "svelte/store";
import { browser } from "$app/environment";
import { API_V1_URL } from "$lib/config";
import type { User } from "$lib/types";

interface AuthState {
  user: User | null;
  isLoading: boolean;
}

/**
 * Check if a specific cookie exists
 */
function hasCookie(name: string): boolean {
  if (!browser) {
    return false;
  }
  const cookies = document.cookie.split(";");
  return cookies.some((cookie) => cookie.trim().startsWith(`${name}=`));
}

// Initialize with no user (will check cookies on init)
const initialState: AuthState = {
  user: null,
  isLoading: false,
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
        const response = await fetch(`${API_V1_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
          credentials: "include", // Send and receive cookies
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || "Login failed");
        }

        // Login successful - cookies are set automatically
        // Fetch user profile
        const userResponse = await fetch(`${API_V1_URL}/users/me`, {
          credentials: "include", // Send cookies
        });

        if (!userResponse.ok) {
          throw new Error("Failed to fetch user profile");
        }

        const user = await userResponse.json();

        update((state) => ({
          ...state,
          user,
          isLoading: false,
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
    async register(
      email: string,
      password: string,
      displayName?: string,
    ): Promise<void> {
      update((state) => ({ ...state, isLoading: true }));

      try {
        const response = await fetch(`${API_V1_URL}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            password,
            display_name: displayName || null,
          }),
          credentials: "include",
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || "Registration failed");
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
        await fetch(`${API_V1_URL}/auth/logout`, {
          method: "POST",
          credentials: "include",
        });
      } catch (error) {
        console.error("Logout request failed:", error);
        // Continue with local logout even if backend call fails
      }

      set({
        user: null,
        isLoading: false,
      });

      // Redirect to login page if requested and in browser
      if (redirect && browser) {
        globalThis.location.href = "/auth/login";
      }
    },

    /**
     * Initialize auth from cookies
     */
    async init(): Promise<void> {
      if (!browser) {
        return;
      }

      // Check if csrf_token cookie exists (access_token is httpOnly and can't be read by JS)
      // If no csrf_token, user is not logged in, but don't clear user if already set
      // (e.g., during login flow)
      if (!hasCookie("csrf_token")) {
        // No auth cookie present, skip API call but preserve existing user state
        update((state) => ({
          ...state,
          isLoading: false,
        }));
        return;
      }

      update((state) => ({ ...state, isLoading: true }));

      try {
        const response = await fetch(`${API_V1_URL}/users/me`, {
          credentials: "include", // Send cookies
        });

        if (!response.ok) {
          // API call failed - only clear user if this is an initial load,
          // not if user was just set by login
          update((state) => ({
            ...state,
            // Preserve user if already set (e.g., just logged in)
            user: state.user || null,
            isLoading: false,
          }));
          return;
        }

        const user = await response.json();

        update((state) => ({
          ...state,
          user,
          isLoading: false,
        }));
      } catch (error) {
        // Network error - preserve existing user state
        update((state) => ({
          ...state,
          isLoading: false,
        }));
      }
    },

    /**
     * Reset store to initial state (for testing)
     */
    reset(): void {
      set(initialState);
    },
  };
}

export const auth = createAuthStore();

// Derived store for checking if user is authenticated
export const isAuthenticated = derived(auth, ($auth) => $auth.user !== null);
