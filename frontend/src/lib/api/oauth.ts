/**
 * OAuth/OIDC authentication API client
 */

import { apiRequest, buildQueryString } from "./client";
import { API_V1_URL } from "#lib/config.js";

export function completeOAuthFlow(provider: string, code: string, state: string): Promise<void> {
  return apiRequest<void>(`/auth/${encodeURIComponent(provider)}/callback${buildQueryString({code, state})}`, {requireAuth: false});
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  enabled: boolean;
}

export interface LinkedProvider {
  id: number;
  provider_name: string;
  email_at_provider: string;
  created_at: string;
  last_used_at: string | null;
}

/**
 * Get list of available OAuth providers
 */
export async function getAvailableProviders(): Promise<ProviderInfo[]> {
  return apiRequest<ProviderInfo[]>("/auth/providers", {
    method: "GET",
    requireAuth: false,
  });
}

/**
 * Initiate OAuth flow with specified provider
 * Redirects to provider's authorization URL
 */
export function initiateOAuthFlow(provider: string, link = false): void {
  window.location.href = `${API_V1_URL}/auth/${encodeURIComponent(provider)}/authorize${link ? "?link=true" : ""}`;
}

/**
 * Get list of identity providers linked to current user
 */
export async function getLinkedProviders(): Promise<LinkedProvider[]> {
  return apiRequest<LinkedProvider[]>("/auth/me/providers", {
    method: "GET",
  });
}

/**
 * Remove a linked identity provider
 */
export async function unlinkProvider(providerId: number): Promise<void> {
  return apiRequest<void>(`/auth/providers/${providerId}`, {
    method: "DELETE",
  });
}
