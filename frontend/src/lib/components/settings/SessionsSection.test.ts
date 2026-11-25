/**
 * Tests for the active sessions settings section
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import { get } from "svelte/store";

vi.mock("#lib/api/sessions.js", async (importOriginal) => ({
  ...(await importOriginal<typeof import("#lib/api/sessions.js")>()),
  listSessions: vi.fn(),
  revokeSession: vi.fn(),
}));

import SessionsSection from "./SessionsSection.svelte";
import { listSessions, revokeSession } from "#lib/api/sessions.js";
import { dialog } from "#lib/stores/dialog.js";

const here = {
  id: 1,
  user_agent:
    "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
  last_active_at: "2026-11-25T10:00:00Z",
  current: true,
};
const phone = {
  id: 2,
  user_agent:
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
  last_active_at: "2026-11-24T10:00:00Z",
  current: false,
};

describe("SessionsSection", () => {
  beforeEach(() => {
    vi.mocked(listSessions).mockReset();
    vi.mocked(revokeSession).mockReset();
    dialog.close();
  });

  it("labels sessions and offers sign-out only for other devices", async () => {
    vi.mocked(listSessions).mockResolvedValue([here, phone]);

    const { findByText, getByText, getAllByRole } = render(SessionsSection);

    expect(await findByText(/Firefox on Linux/)).toBeTruthy();
    expect(getByText("This device")).toBeTruthy();
    expect(getByText(/Safari on iOS/)).toBeTruthy();
    expect(getAllByRole("button", { name: "Sign out" })).toHaveLength(1);
  });

  it("signs out a session after confirmation", async () => {
    vi.mocked(listSessions)
      .mockResolvedValueOnce([here, phone])
      .mockResolvedValue([here]);
    vi.mocked(revokeSession).mockResolvedValue();

    const { findByRole, queryByText } = render(SessionsSection);
    await fireEvent.click(await findByRole("button", { name: "Sign out" }));

    // Nothing happens until the dialog is confirmed
    const state = get(dialog);
    expect(state.open).toBe(true);
    expect(state.message).toContain("Safari on iOS");
    expect(revokeSession).not.toHaveBeenCalled();

    await state.onConfirm();

    await waitFor(() => expect(revokeSession).toHaveBeenCalledWith(2));
    await waitFor(() => expect(queryByText(/Safari on iOS/)).toBeNull());
  });

  it("shows an error when loading fails", async () => {
    vi.mocked(listSessions).mockRejectedValue(new Error("boom"));

    const { findByText } = render(SessionsSection);

    expect(await findByText("Failed to load sessions")).toBeTruthy();
  });
});
