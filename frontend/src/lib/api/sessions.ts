/**
 * Active login session endpoints: one entry per signed-in browser.
 */

import { apiRequest } from "./client";

export interface Session {
  id: number;
  user_agent: string | null;
  last_active_at: string;
  current: boolean;
}

/**
 * List the current user's signed-in browsers, most recently active first
 */
export async function listSessions(): Promise<Session[]> {
  return apiRequest<Session[]>("/users/me/sessions");
}

/**
 * Sign out one session
 */
export async function revokeSession(id: number): Promise<void> {
  return apiRequest<void>(`/users/me/sessions/${id}`, {
    method: "DELETE",
  });
}

/**
 * Short "Browser on OS" label from a User-Agent string.
 * ponytail: substring checks for common browsers only; anything else shows as
 * "Unknown browser". Swap in a UA parser if that proves too coarse.
 */
export function describeUserAgent(ua: string | null): string {
  if (!ua) return "Unknown device";
  const browser = /Edg\//.test(ua)
    ? "Edge"
    : /Firefox\//.test(ua)
      ? "Firefox"
      : /Chrome\//.test(ua)
        ? "Chrome"
        : /Safari\//.test(ua)
          ? "Safari"
          : "Unknown browser";
  const os = /iPhone|iPad/.test(ua)
    ? "iOS"
    : /Android/.test(ua)
      ? "Android"
      : /Mac OS X/.test(ua)
        ? "macOS"
        : /Windows/.test(ua)
          ? "Windows"
          : /Linux/.test(ua)
            ? "Linux"
            : null;
  return os ? `${browser} on ${os}` : browser;
}
