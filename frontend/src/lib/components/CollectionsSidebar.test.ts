/**
 * The sidebar lists the household's collections but only offers edit and
 * delete on the signed-in user's own.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/svelte/svelte5";

vi.mock("$app/navigation", () => ({ goto: vi.fn() }));
vi.mock("$app/state", () => ({ page: { url: new URL("http://x/recipes") } }));
vi.mock("#lib/stores/auth.js", async () => {
  const { readable } = await import("svelte/store");
  return { auth: readable({ user: { id: 1 } }) };
});
vi.mock("#lib/api/users.js", () => ({
  getUserStats: vi.fn().mockResolvedValue({ total_recipes: 0 }),
}));
vi.mock("#lib/api/collections.js", () => ({
  getCollections: vi.fn(),
  createCollection: vi.fn(),
  updateCollection: vi.fn(),
  deleteCollection: vi.fn(),
}));

import CollectionsSidebar from "./CollectionsSidebar.svelte";
import { collections } from "#lib/stores/collections.js";
import { getCollections } from "#lib/api/collections.js";

const collection = (id: number, user_id: number, name: string, extra = {}) => ({
  id,
  user_id,
  name,
  is_default: false,
  recipe_count: 0,
  created_at: "",
  updated_at: "",
  creator_display_name: user_id === 1 ? "Me" : "Sam",
  ...extra,
});

describe("CollectionsSidebar", () => {
  beforeEach(() => {
    collections.clear();
    vi.mocked(getCollections).mockResolvedValue([
      collection(1, 1, "Favorites", { is_default: true }),
      collection(2, 2, "Favorites", { is_default: true }),
      collection(3, 1, "Weeknight"),
      collection(4, 2, "Baking"),
    ]);
  });

  it("offers edit and delete only on my own collections", async () => {
    const { findByText, queryByLabelText, getByLabelText } =
      render(CollectionsSidebar);
    await findByText("Weeknight");

    expect(getByLabelText("Edit collection Weeknight")).toBeTruthy();
    expect(getByLabelText("Delete collection Weeknight")).toBeTruthy();
    expect(queryByLabelText("Edit collection Baking")).toBeNull();
    expect(queryByLabelText("Delete collection Baking")).toBeNull();
    // Another member's Favorites is listed, but is not mine to change either
    expect(queryByLabelText("Edit collection Favorites")).toBeNull();
  });

  it("says whose collection it is when it is not mine", async () => {
    const { findByText, getAllByText } = render(CollectionsSidebar);

    expect(
      (await findByText("Baking", { exact: false })).textContent,
    ).toContain("Sam");
    // My Favorites and Sam's are both shown, Sam's with his name
    expect(getAllByText("Favorites", { exact: false })).toHaveLength(2);
  });
});
