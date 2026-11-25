/**
 * Tests for ownership transfer in the household settings section
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import { get, readable } from "svelte/store";

vi.mock("#lib/stores/auth.js", () => ({
  auth: readable({ user: { id: 1 } }),
}));

vi.mock("#lib/api/households.js", () => ({
  getCurrentHousehold: vi.fn(),
  getHouseholdMembers: vi.fn(),
  getHouseholdInvitations: vi.fn(),
  updateHousehold: vi.fn(),
  removeMember: vi.fn(),
  transferOwnership: vi.fn(),
  createInvitation: vi.fn(),
  revokeInvitation: vi.fn(),
  createInviteLink: vi.fn(),
  joinViaInviteLink: vi.fn(),
  leaveHousehold: vi.fn(),
}));

import HouseholdSection from "./HouseholdSection.svelte";
import {
  getCurrentHousehold,
  getHouseholdMembers,
  getHouseholdInvitations,
  transferOwnership,
} from "#lib/api/households.js";
import { dialog } from "#lib/stores/dialog.js";

const household = {
  id: 3,
  name: "Home",
  owner_user_id: 1,
  max_members: 10,
  created_at: "2026-11-01T00:00:00Z",
  updated_at: "2026-11-01T00:00:00Z",
};
const me = {
  id: 10,
  household_id: 3,
  user_id: 1,
  role: "owner" as const,
  joined_at: "2026-11-01T00:00:00Z",
  user_display_name: "Me",
};
const sam = {
  id: 11,
  household_id: 3,
  user_id: 2,
  role: "member" as const,
  joined_at: "2026-11-02T00:00:00Z",
  user_display_name: "Sam",
};

describe("HouseholdSection ownership transfer", () => {
  beforeEach(() => {
    vi.mocked(getCurrentHousehold).mockReset();
    vi.mocked(getHouseholdMembers).mockReset();
    vi.mocked(getHouseholdInvitations).mockReset().mockResolvedValue([]);
    vi.mocked(transferOwnership).mockReset();
    dialog.close();
  });

  it("hands ownership over after confirmation and drops owner controls", async () => {
    vi.mocked(getCurrentHousehold)
      .mockResolvedValueOnce(household)
      .mockResolvedValue({ ...household, owner_user_id: 2 });
    vi.mocked(getHouseholdMembers)
      .mockResolvedValueOnce([me, sam])
      .mockResolvedValue([
        { ...me, role: "member" },
        { ...sam, role: "owner" },
      ]);
    vi.mocked(transferOwnership).mockResolvedValue({
      ...household,
      owner_user_id: 2,
    });

    const { findByRole, queryByRole } = render(HouseholdSection);
    await fireEvent.click(await findByRole("button", { name: "Make owner" }));

    // Nothing happens until the dialog is confirmed
    const state = get(dialog);
    expect(state.open).toBe(true);
    expect(state.message).toContain("Sam");
    expect(transferOwnership).not.toHaveBeenCalled();

    await state.onConfirm();

    await waitFor(() => expect(transferOwnership).toHaveBeenCalledWith(3, 2));
    await waitFor(() =>
      expect(queryByRole("button", { name: "Make owner" })).toBeNull(),
    );
    expect(queryByRole("button", { name: "Remove" })).toBeNull();
  });
});
