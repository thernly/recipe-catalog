/**
 * API client for communicating with the backend
 */

import { auth } from "#lib/stores/auth.js";
import { API_V1_URL } from "#lib/config.js";
import { browser } from "$app/env";
import { FETCH_CREDENTIALS } from "#lib/constants.js";

const API_URL = API_V1_URL;

interface RequestOptions extends RequestInit {
  requireAuth?: boolean;
  responseType?: "json" | "blob";
  /** If false, a failed refresh clears auth state without redirecting to login. */
  redirectOnAuthFailure?: boolean;
}

/**
 * Get a cookie value by name
 */
function getCookie(name: string): string | null {
  if (!browser) {
    return null;
  }
  const cookies = document.cookie.split(";");
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.split("=").map((c) => c.trim());
    if (cookieName === name) {
      return decodeURIComponent(cookieValue);
    }
  }
  return null;
}

/**
 * Get CSRF token from cookie
 */
function getCsrfToken(): string | null {
  return getCookie("csrf_token");
}

/**
 * Typed API error with structured error information
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public errorCode?: string,
    public details?: Record<string, unknown>,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Promise cache for refresh token to prevent concurrent refreshes
let refreshPromise: Promise<boolean> | null = null;
let refreshGeneration = 0;

/**
 * Refresh the access token using the refresh token cookie
 */
async function refreshAccessToken(redirect = true): Promise<boolean> {
  // Return existing promise if refresh is already in progress
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const csrfToken = getCsrfToken();
      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
        credentials: FETCH_CREDENTIALS, // Send cookies
      });

      if (!response.ok) {
        // Refresh failed - logout user and redirect to login
        await auth.logout(redirect);
        return false;
      }

      refreshGeneration += 1;
      // Refresh successful - cookies are automatically updated
      return true;
    } catch (error) {
      console.error("Token refresh failed:", error);
      await auth.logout(redirect);
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
  options: RequestOptions = {},
): Promise<T> {
  const {
    requireAuth = true,
    responseType = "json",
    redirectOnAuthFailure = true,
    ...fetchOptions
  } = options;
  const generation = refreshGeneration;
  const method = (fetchOptions.method || "GET").toUpperCase();
  const mutation = ["POST", "PUT", "PATCH", "DELETE"].includes(method);
  const send = () => {
    const headers = new Headers(fetchOptions.headers);
    if (
      !(fetchOptions.body instanceof FormData) &&
      !headers.has("Content-Type")
    ) {
      headers.set("Content-Type", "application/json");
    }
    const csrfToken = getCsrfToken();
    if (mutation && csrfToken) headers.set("X-CSRF-Token", csrfToken);
    return fetch(`${API_URL}${endpoint}`, {
      ...fetchOptions,
      headers,
      credentials: FETCH_CREDENTIALS,
    });
  };
  let response = await send();
  if (
    requireAuth &&
    (response.status === 401 || (response.status === 403 && mutation))
  ) {
    if (
      generation !== refreshGeneration ||
      (await refreshAccessToken(redirectOnAuthFailure))
    ) {
      response = await send();
    }
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(
      data.message || data.detail || `HTTP error! status: ${response.status}`,
      data.error_code,
      data.details,
      response.status,
    );
  }
  if (responseType === "blob") return (await response.blob()) as T;
  if (response.status === 204) return {} as T;
  return (await response.json()) as T;
}

/**
 * Build query string from params object
 */
export function buildQueryString(params: object): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      if (Array.isArray(value)) {
        value.forEach((item) => searchParams.append(key, String(item)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
}
