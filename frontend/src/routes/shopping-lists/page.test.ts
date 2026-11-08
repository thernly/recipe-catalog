/**
 * Tests for the shopping list index: per-card Rename/Delete and "Created by"
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import { get } from "svelte/store";

vi.mock("$app/navigation", () => ({ goto: vi.fn() }));
vi.mock("#lib/api/shopping-lists.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listShoppingLists: vi.fn(),
  createShoppingList: vi.fn(),
  updateShoppingList: vi.fn(),
  deleteShoppingList: vi.fn(),
}));

import Page from "./+page.svelte";
import {
  listShoppingLists,
  updateShoppingList,
  deleteShoppingList,
} from "#lib/api/shopping-lists.js";
import { dialog } from "#lib/stores/dialog.js";

const summary = {
  id: 7,
  household_id: 1,
  name: "Weekly",
  status: "active" as const,
  created_by_user_id: 99,
  created_by_name: "Sam",
  created_at: "2026-11-01T00:00:00Z",
  item_count: 2,
  checked_count: 0,
};

describe("shopping list index cards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listShoppingLists).mockResolvedValue([summary]);
    dialog.close();
  });

  it("keeps the card body a link and the controls outside it", async () => {
    const { findByRole, getByRole, findByText } = render(Page);
    const rename = await findByRole("button", { name: "Rename Weekly" });
    const link = getByRole("link", { name: /Weekly/ });
    expect(link.getAttribute("href")).toBe("/shopping-lists/7");
    expect(link.contains(rename)).toBe(false);
    expect(await findByText(/Created by Sam/)).toBeTruthy();
  });

  it("renames a list inline", async () => {
    vi.mocked(updateShoppingList).mockResolvedValue({} as never);
    const { findByRole, getByLabelText, getByRole } = render(Page);

    await fireEvent.click(
      await findByRole("button", { name: "Rename Weekly" }),
    );
    await fireEvent.input(getByLabelText("New name for Weekly"), {
      target: { value: "Party" },
    });
    await fireEvent.click(getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(updateShoppingList).toHaveBeenCalledWith(7, { name: "Party" }),
    );
    expect(await findByRole("button", { name: "Rename Party" })).toBeTruthy();
  });

  it("deletes a list after confirmation", async () => {
    vi.mocked(deleteShoppingList).mockResolvedValue();
    const { findByRole, queryByRole } = render(Page);

    await fireEvent.click(
      await findByRole("button", { name: "Delete Weekly" }),
    );
    expect(deleteShoppingList).not.toHaveBeenCalled();
    await get(dialog).onConfirm();

    expect(deleteShoppingList).toHaveBeenCalledWith(7);
    await waitFor(() =>
      expect(queryByRole("button", { name: "Delete Weekly" })).toBeNull(),
    );
  });
});
