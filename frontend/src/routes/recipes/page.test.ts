/**
 * Tests for the recipe list page: its two empty states and the Add Recipe link
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";

const nav = vi.hoisted(() => ({ url: "http://localhost/recipes" }));

vi.mock("$app/navigation", () => ({
  goto: vi.fn(),
  replaceState: vi.fn(),
  afterNavigate: (fn: (n: { to: { url: URL } }) => void) =>
    fn({ to: { url: new URL(nav.url) } }),
}));
vi.mock("$app/state", () => ({
  page: { url: new URL("http://localhost/recipes"), params: {} },
}));
vi.mock("#lib/api/recipes.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  searchRecipes: vi.fn(),
}));
vi.mock("#lib/api/users.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getPreferences: vi
    .fn()
    .mockResolvedValue({ default_cuisines: [], default_categories: [] }),
  getUserStats: vi.fn().mockResolvedValue({}),
}));
vi.mock("#lib/api/collections.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getCollections: vi.fn().mockResolvedValue([]),
}));

import Page from "./+page.svelte";
import { searchRecipes } from "#lib/api/recipes.js";

const none = {
  recipes: [],
  total: 0,
  page: 1,
  per_page: 24,
  total_pages: 0,
} as unknown as Awaited<ReturnType<typeof searchRecipes>>;

describe("recipe list page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(searchRecipes).mockResolvedValue(none);
    nav.url = "http://localhost/recipes";
  });

  it("offers to clear the search when nothing matches", async () => {
    nav.url = "http://localhost/recipes?q=zzz";
    const { findByRole, queryByText } = render(Page);

    const clear = await findByRole("button", {
      name: "Clear search and filters",
    });
    expect(queryByText("No recipes yet")).toBeNull();

    await fireEvent.click(clear);
    await waitFor(() =>
      expect(vi.mocked(searchRecipes).mock.lastCall?.[0]?.query).toBe(""),
    );
  });

  it("says there are no recipes yet when nothing is being searched for", async () => {
    const { findByText, queryByRole } = render(Page);

    expect(await findByText("No recipes yet")).toBeTruthy();
    expect(
      queryByRole("button", { name: "Clear search and filters" }),
    ).toBeNull();
  });

  it("links to the new recipe page from the header", async () => {
    const { findByRole } = render(Page);

    const add = await findByRole("link", { name: "Add recipe" });
    expect(add.getAttribute("href")).toBe("/recipes/new");
  });
});
