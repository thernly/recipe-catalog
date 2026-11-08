import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";

vi.mock("#lib/api/shopping-lists.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listShoppingLists: vi.fn(),
}));

import AddToShoppingListDialog from "./AddToShoppingListDialog.svelte";
import {
  listShoppingLists,
  setLastShoppingListId,
} from "#lib/api/shopping-lists.js";

const lists = [7, 8].map((id) => ({
  id,
  household_id: 1,
  name: `List ${id}`,
  status: "active" as const,
  created_by_user_id: 1,
  created_at: "2026-11-01T00:00:00Z",
  item_count: 0,
  checked_count: 0,
}));

describe("AddToShoppingListDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setLastShoppingListId(null);
    vi.mocked(listShoppingLists).mockResolvedValue(lists);
  });

  it("picks an existing active list, preselecting the last-used one", async () => {
    setLastShoppingListId(8);
    const onPick = vi.fn();
    const { findByRole, getByRole } = render(AddToShoppingListDialog, {
      open: true,
      onPick,
      onClose: vi.fn(),
    });

    const last = (await findByRole("radio", {
      name: /List 8/,
    })) as HTMLInputElement;
    await waitFor(() => expect(last.checked).toBe(true));
    expect(listShoppingLists).toHaveBeenCalledWith("active");

    await fireEvent.click(getByRole("radio", { name: /List 7/ }));
    await fireEvent.click(getByRole("button", { name: "Add" }));
    expect(onPick).toHaveBeenCalledWith(7);
  });

  it("offers New list unless in pick-a-list mode", async () => {
    const onPick = vi.fn();
    const { findByRole, getByRole } = render(AddToShoppingListDialog, {
      open: true,
      onPick,
      onClose: vi.fn(),
    });
    await fireEvent.click(await findByRole("radio", { name: "New list" }));
    await fireEvent.click(getByRole("button", { name: "Add" }));
    expect(onPick).toHaveBeenCalledWith(null);
  });

  it("hides New list in pick-a-list mode", async () => {
    const { findByRole, queryByRole } = render(AddToShoppingListDialog, {
      open: true,
      allowNew: false,
      onPick: vi.fn(),
      onClose: vi.fn(),
    });
    await findByRole("radio", { name: /List 7/ });
    expect(queryByRole("radio", { name: "New list" })).toBeNull();
  });
});
