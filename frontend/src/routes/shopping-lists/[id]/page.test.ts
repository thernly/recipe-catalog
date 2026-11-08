/**
 * Tests for the shopping list detail page: editing and deleting a list
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import { get } from "svelte/store";

vi.mock("$app/navigation", () => ({ goto: vi.fn() }));
vi.mock("#lib/api/shopping-lists.js", () => ({
  getShoppingList: vi.fn(),
  updateShoppingList: vi.fn(),
  deleteShoppingList: vi.fn(),
  archiveShoppingList: vi.fn(),
  duplicateShoppingList: vi.fn(),
  addShoppingListItem: vi.fn(),
  updateShoppingListItem: vi.fn(),
  deleteShoppingListItem: vi.fn(),
  getCategories: vi.fn(),
}));

import Page from "./+page.svelte";
import { goto } from "$app/navigation";
import {
  getShoppingList,
  updateShoppingList,
  deleteShoppingList,
  getCategories,
} from "#lib/api/shopping-lists.js";
import { dialog } from "#lib/stores/dialog.js";

const list = {
  id: 7,
  household_id: 1,
  name: "Weekly",
  description: "",
  status: "active" as const,
  created_by_user_id: 2,
  created_at: "2026-11-01T00:00:00Z",
  updated_at: "2026-11-01T00:00:00Z",
  items: [],
};

describe("shopping list detail page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getShoppingList).mockResolvedValue(list);
    vi.mocked(getCategories).mockResolvedValue([]);
    dialog.close();
  });

  it("renames the list", async () => {
    vi.mocked(updateShoppingList).mockResolvedValue({ ...list, name: "Party" });
    const { findByRole, getByLabelText, getByRole } = render(Page, {
      params: { id: "7" },
    });

    await fireEvent.click(await findByRole("button", { name: "Edit list" }));
    await fireEvent.input(getByLabelText("List name"), {
      target: { value: "Party" },
    });
    await fireEvent.click(getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(updateShoppingList).toHaveBeenCalledWith(7, {
        name: "Party",
        description: "",
      }),
    );
  });

  it("reloads when the id changes without a remount", async () => {
    const { findByRole, rerender } = render(Page, { params: { id: "7" } });
    await findByRole("heading", { name: "Weekly" });

    vi.mocked(getShoppingList).mockResolvedValue({
      ...list,
      id: 8,
      name: "Weekly (Copy)",
    });
    await rerender({ params: { id: "8" } });

    expect(await findByRole("heading", { name: "Weekly (Copy)" })).toBeTruthy();
    expect(getShoppingList).toHaveBeenLastCalledWith(8);
  });

  it("deletes the list after confirmation", async () => {
    vi.mocked(deleteShoppingList).mockResolvedValue();
    const { findByRole } = render(Page, { params: { id: "7" } });

    await fireEvent.click(await findByRole("button", { name: "Delete" }));
    await get(dialog).onConfirm();

    await waitFor(() => expect(deleteShoppingList).toHaveBeenCalledWith(7));
    expect(goto).toHaveBeenCalledWith("/shopping-lists");
  });
});
