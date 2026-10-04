/**
 * Tests for the API token client module
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("./client", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "./client";
import { listApiTokens, createApiToken, revokeApiToken } from "./api-tokens";

const mockedApiRequest = vi.mocked(apiRequest);

describe("api-tokens", () => {
  beforeEach(() => {
    mockedApiRequest.mockReset();
  });

  it("lists tokens", async () => {
    mockedApiRequest.mockResolvedValue([]);

    await expect(listApiTokens()).resolves.toEqual([]);
    expect(mockedApiRequest).toHaveBeenCalledWith("/users/me/api-tokens");
  });

  it("creates a token with its name", async () => {
    const created = {
      id: 1,
      name: "Firefox",
      token_prefix: "rcat_abcdef",
      token: "rcat_abcdef123",
      created_at: "2026-10-04T00:00:00Z",
      last_used_at: null,
    };
    mockedApiRequest.mockResolvedValue(created);

    await expect(createApiToken("Firefox")).resolves.toEqual(created);
    expect(mockedApiRequest).toHaveBeenCalledWith("/users/me/api-tokens", {
      method: "POST",
      body: JSON.stringify({ name: "Firefox" }),
    });
  });

  it("revokes a token by id", async () => {
    mockedApiRequest.mockResolvedValue({});

    await revokeApiToken(7);
    expect(mockedApiRequest).toHaveBeenCalledWith("/users/me/api-tokens/7", {
      method: "DELETE",
    });
  });
});
