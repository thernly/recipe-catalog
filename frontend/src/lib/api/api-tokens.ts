/**
 * Personal API token endpoints.
 *
 * Tokens authenticate the Recipe Siphon browser extension against the intake
 * routes only. The token value is returned once, by createApiToken.
 */

import { apiRequest } from "./client";

export interface ApiToken {
  id: number;
  name: string;
  token_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export interface CreatedApiToken extends ApiToken {
  token: string;
}

/**
 * List the current user's active API tokens
 */
export async function listApiTokens(): Promise<ApiToken[]> {
  return apiRequest<ApiToken[]>("/users/me/api-tokens");
}

/**
 * Create an API token. The response is the only place the token value appears.
 */
export async function createApiToken(name: string): Promise<CreatedApiToken> {
  return apiRequest<CreatedApiToken>("/users/me/api-tokens", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

/**
 * Revoke an API token
 */
export async function revokeApiToken(id: number): Promise<void> {
  return apiRequest<void>(`/users/me/api-tokens/${id}`, {
    method: "DELETE",
  });
}
