/**
 * OAuth/OIDC authentication API client
 */

import { apiRequest } from "./client";

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
export function initiateOAuthFlow(provider: string): void {
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  window.location.href = `${apiUrl}/api/v1/auth/${provider}/authorize`;
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
