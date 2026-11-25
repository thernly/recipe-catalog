/**
 * Tests for the households client module
 */
import { describe, it, expect, vi } from "vitest";

vi.mock("./client", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "./client";
import {
  acceptInvitation,
  declineInvitation,
  getInvitationByToken,
  joinViaInviteLink,
  transferOwnership,
} from "./households";

describe("households", () => {
  // The server serves these under /households; a bare /invitations path is a 404.
  it("calls the invitation routes under /households", async () => {
    vi.mocked(apiRequest).mockResolvedValue(undefined);

    await getInvitationByToken("tok");
    expect(apiRequest).toHaveBeenCalledWith("/households/invitations/tok", {
      requireAuth: false,
    });
    await acceptInvitation({ token: "tok" });
    expect(apiRequest).toHaveBeenCalledWith("/households/invitations/accept", {
      method: "POST",
      body: JSON.stringify({ token: "tok" }),
    });
    await declineInvitation("tok");
    expect(apiRequest).toHaveBeenCalledWith("/households/invitations/decline", {
      method: "POST",
      body: JSON.stringify({ token: "tok" }),
    });
  });

  it("lets the server do the leaving when switching households", async () => {
    vi.mocked(apiRequest).mockResolvedValue(undefined);

    await joinViaInviteLink("a-b-c-d-e", true);
    expect(apiRequest).toHaveBeenCalledWith("/households/join", {
      method: "POST",
      body: JSON.stringify({ code: "a-b-c-d-e", leave_current: true }),
    });
  });

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
