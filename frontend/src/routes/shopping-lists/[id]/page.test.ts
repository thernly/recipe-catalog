/**
 * Tests for the shopping list detail page: editing and deleting a list
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import { get } from "svelte/store";

vi.mock("$app/navigation", () => ({ goto: vi.fn() }));
vi.mock("#lib/api/shopping-lists.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
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
  addShoppingListItem,
  updateShoppingListItem,
  deleteShoppingListItem,
  getCategories,
} from "#lib/api/shopping-lists.js";
import { dialog } from "#lib/stores/dialog.js";
import { SHOPPING_LIST_REFRESH_INTERVAL } from "#lib/constants.js";

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

  it("shows units and edits an item's quantity inline", async () => {
    const flour = {
      id: 3,
      list_id: 7,
      item_name: "flour",
      quantity: "2",
      unit: "cup",
      checked: false,
      display_order: 1,
      created_at: "2026-11-01T00:00:00Z",
      updated_at: "2026-11-01T00:00:00Z",
    };
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [flour] });
    vi.mocked(updateShoppingListItem).mockResolvedValue(flour);
    const { findByRole, getByLabelText, findByText } = render(Page, {
      params: { id: "7" },
    });

    expect(await findByText("2 cups")).toBeTruthy();
    await fireEvent.click(
      await findByRole("button", { name: /Quantity for flour/ }),
    );
    const quantity = getByLabelText("Quantity for flour");
    await fireEvent.input(quantity, { target: { value: "3" } });
    await fireEvent.submit(quantity.closest("form") as HTMLFormElement);

    await waitFor(() =>
      expect(updateShoppingListItem).toHaveBeenCalledWith(3, {
        quantity: "3",
        unit: "cup",
      }),
    );
  });

  it("cancels a quantity edit on Escape", async () => {
    const egg = {
      id: 4,
      list_id: 7,
      item_name: "egg",
      quantity: "2",
      checked: false,
      display_order: 1,
      created_at: "2026-11-01T00:00:00Z",
      updated_at: "2026-11-01T00:00:00Z",
    };
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [egg] });
    const { findByRole, getByLabelText } = render(Page, {
      params: { id: "7" },
    });

    await fireEvent.click(
      await findByRole("button", { name: /Quantity for egg/ }),
    );
    const quantity = getByLabelText("Quantity for egg");
    await fireEvent.input(quantity, { target: { value: "9" } });
    await fireEvent.keyDown(quantity, { key: "Escape" });

    expect(
      await findByRole("button", { name: /Quantity for egg/ }),
    ).toBeTruthy();
    expect(updateShoppingListItem).not.toHaveBeenCalled();
  });

  const milk = {
    id: 5,
    list_id: 7,
    item_name: "milk",
    checked: false,
    display_order: 1,
    created_at: "2026-11-01T00:00:00Z",
    updated_at: "2026-11-01T00:00:00Z",
  };

  it("checks an item off at once without refetching the list", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [milk] });
    vi.mocked(updateShoppingListItem).mockResolvedValue({
      ...milk,
      checked: true,
    });
    const { findByRole } = render(Page, { params: { id: "7" } });

    const box = (await findByRole("checkbox", {
      name: "Got milk",
    })) as HTMLInputElement;
    await fireEvent.click(box);

    expect(box.checked).toBe(true);
    expect(updateShoppingListItem).toHaveBeenCalledWith(5, { checked: true });
    expect(getShoppingList).toHaveBeenCalledTimes(1);
  });

  it("checks an item off when its name is tapped", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [milk] });
    vi.mocked(updateShoppingListItem).mockResolvedValue({
      ...milk,
      checked: true,
    });
    const { findByText } = render(Page, { params: { id: "7" } });

    await fireEvent.click(await findByText("milk"));

    expect(updateShoppingListItem).toHaveBeenCalledWith(5, { checked: true });
  });

  it("unchecks the item again when the update fails", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [milk] });
    vi.mocked(updateShoppingListItem).mockRejectedValue(new Error("offline"));
    const { findByRole } = render(Page, { params: { id: "7" } });

    const box = (await findByRole("checkbox", {
      name: "Got milk",
    })) as HTMLInputElement;
    await fireEvent.click(box);

    await waitFor(() => expect(box.checked).toBe(false));
  });

  it("shows another shopper's tick on return to the tab", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [milk] });
    const { findByRole } = render(Page, { params: { id: "7" } });
    const box = (await findByRole("checkbox", {
      name: "Got milk",
    })) as HTMLInputElement;

    vi.mocked(getShoppingList).mockResolvedValue({
      ...list,
      items: [{ ...milk, checked: true }],
    });
    document.dispatchEvent(new Event("visibilitychange"));

    await waitFor(() => expect(box.checked).toBe(true));
  });

  it("refreshes the list on a timer", async () => {
    const setIntervalSpy = vi.spyOn(window, "setInterval");
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [milk] });
    const { findByRole } = render(Page, { params: { id: "7" } });
    const box = (await findByRole("checkbox", {
      name: "Got milk",
    })) as HTMLInputElement;

    vi.mocked(getShoppingList).mockResolvedValue({
      ...list,
      items: [{ ...milk, checked: true }],
    });
    const tick = setIntervalSpy.mock.calls.find(
      ([, delay]) => delay === SHOPPING_LIST_REFRESH_INTERVAL,
    )?.[0] as () => void;
    setIntervalSpy.mockRestore();
    tick();

    await waitFor(() => expect(box.checked).toBe(true));
  });

  it("keeps a tick made while a refresh was on its way", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [milk] });
    vi.mocked(updateShoppingListItem).mockResolvedValue({
      ...milk,
      checked: true,
    });
    const { findByRole } = render(Page, { params: { id: "7" } });
    const box = (await findByRole("checkbox", {
      name: "Got milk",
    })) as HTMLInputElement;

    let finishRefresh: (value: typeof list) => void = () => {};
    vi.mocked(getShoppingList).mockReturnValue(
      new Promise((resolve) => (finishRefresh = resolve)),
    );
    document.dispatchEvent(new Event("visibilitychange"));
    await fireEvent.click(box);
    finishRefresh({ ...list, items: [milk] } as typeof list);
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(getShoppingList).toHaveBeenCalledTimes(2);
    expect(box.checked).toBe(true);
  });

  it("keeps the list on screen while it reloads after adding an item", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [milk] });
    vi.mocked(addShoppingListItem).mockResolvedValue({ ...milk, id: 6 });
    const { findByLabelText, queryByText, getByText } = render(Page, {
      params: { id: "7" },
    });
    const name = (await findByLabelText("Item name")) as HTMLInputElement;

    // The reload after the add never finishes, so the page is caught mid-reload
    vi.mocked(getShoppingList).mockReturnValue(new Promise(() => {}));
    await fireEvent.input(name, { target: { value: "eggs" } });
    await fireEvent.submit(name.closest("form") as HTMLFormElement);
    await waitFor(() => expect(getShoppingList).toHaveBeenCalledTimes(2));

    expect(queryByText("Loading shopping list...")).toBeNull();
    expect(getByText("milk")).toBeTruthy();
    expect(name.isConnected).toBe(true);
  });

  const gotEggs = { ...milk, id: 6, item_name: "eggs", checked: true };

  it("deletes an item at once, without asking", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({ ...list, items: [milk] });
    vi.mocked(deleteShoppingListItem).mockResolvedValue();
    const { findByRole, queryByText } = render(Page, { params: { id: "7" } });

    await fireEvent.click(await findByRole("button", { name: "Delete milk" }));

    expect(deleteShoppingListItem).toHaveBeenCalledWith(5);
    expect(get(dialog).open).toBe(false);
    await waitFor(() => expect(queryByText("milk")).toBeNull());
  });

  it("removes only the checked items, after one confirmation", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({
      ...list,
      items: [milk, gotEggs],
    });
    vi.mocked(deleteShoppingListItem).mockResolvedValue();
    const { findByRole } = render(Page, { params: { id: "7" } });

    await fireEvent.click(
      await findByRole("button", { name: "Remove checked" }),
    );
    expect(deleteShoppingListItem).not.toHaveBeenCalled();
    await get(dialog).onConfirm();

    expect(deleteShoppingListItem).toHaveBeenCalledTimes(1);
    expect(deleteShoppingListItem).toHaveBeenCalledWith(6);
  });

  it("unchecks every checked item", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({
      ...list,
      items: [milk, gotEggs],
    });
    vi.mocked(updateShoppingListItem).mockResolvedValue(gotEggs);
    const { findByRole } = render(Page, { params: { id: "7" } });

    await fireEvent.click(await findByRole("button", { name: "Uncheck all" }));

    await waitFor(() =>
      expect(updateShoppingListItem).toHaveBeenCalledWith(6, {
        checked: false,
      }),
    );
    expect(updateShoppingListItem).toHaveBeenCalledTimes(1);
  });

  it("remembers 'Hide checked items' between visits", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({
      ...list,
      items: [milk, gotEggs],
    });
    const first = render(Page, { params: { id: "7" } });
    await first.findByText("eggs");
    await fireEvent.click(first.getByLabelText("Hide checked items"));
    first.unmount();

    const second = render(Page, { params: { id: "7" } });
    await second.findByText("milk");
    expect(second.queryByText("eggs")).toBeNull();
    localStorage.clear();
  });

  it("unarchives an archived list", async () => {
    vi.mocked(getShoppingList).mockResolvedValue({
      ...list,
      status: "archived",
    });
    vi.mocked(updateShoppingList).mockResolvedValue(list);
    const { findByRole, queryByRole } = render(Page, { params: { id: "7" } });

    await fireEvent.click(await findByRole("button", { name: "Unarchive" }));

    await waitFor(() =>
      expect(updateShoppingList).toHaveBeenCalledWith(7, { status: "active" }),
    );
    expect(queryByRole("button", { name: "Archive" })).toBeNull();
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
