/**
 * Tests for the households client module
 */
import { describe, it, expect, vi } from "vitest";

vi.mock("./client", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "./client";
import { transferOwnership } from "./households";

describe("households", () => {
  it("transfers ownership to a member", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ id: 3, owner_user_id: 9 });

    await transferOwnership(3, 9);
    expect(apiRequest).toHaveBeenCalledWith(
      "/households/3/transfer-ownership",
      {
        method: "POST",
        body: JSON.stringify({ new_owner_user_id: 9 }),
      },
    );
  });
});
