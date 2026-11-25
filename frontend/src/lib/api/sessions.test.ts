/**
 * Tests for the sessions client module
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("./client", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "./client";
import { listSessions, revokeSession, describeUserAgent } from "./sessions";

const mockedApiRequest = vi.mocked(apiRequest);

describe("sessions", () => {
  beforeEach(() => {
    mockedApiRequest.mockReset();
  });

  it("lists sessions", async () => {
    mockedApiRequest.mockResolvedValue([]);

    await expect(listSessions()).resolves.toEqual([]);
    expect(mockedApiRequest).toHaveBeenCalledWith("/users/me/sessions");
  });

  it("revokes a session by id", async () => {
    mockedApiRequest.mockResolvedValue({});

    await revokeSession(7);
    expect(mockedApiRequest).toHaveBeenCalledWith("/users/me/sessions/7", {
      method: "DELETE",
    });
  });

  it.each([
    [
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
      "Safari on macOS",
    ],
    [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
      "Edge on Windows",
    ],
    [
      "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
      "Chrome on Android",
    ],
    [
      "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
      "Safari on iOS",
    ],
    [
      "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
      "Firefox on Linux",
    ],
    ["curl/8.0", "Unknown browser"],
    [null, "Unknown device"],
  ])("describes %s as %s", (ua, label) => {
    expect(describeUserAgent(ua)).toBe(label);
  });
});
