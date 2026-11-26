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
import { getPreferences } from "#lib/api/users.js";
import { getCollections } from "#lib/api/collections.js";

const preferences = (overrides: object) =>
  ({
    default_cuisines: [],
    default_categories: [],
    ...overrides,
  }) as unknown as Awaited<ReturnType<typeof getPreferences>>;

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
    vi.mocked(getPreferences).mockResolvedValue(preferences({}));
  });

  const lastSearch = () => vi.mocked(searchRecipes).mock.lastCall?.[0];

  it("opens in the saved default sort and page size", async () => {
    vi.mocked(getPreferences).mockResolvedValue(
      preferences({ default_sort: "alphabetical", recipes_per_page: 48 }),
    );
    render(Page);

    await waitFor(() => expect(searchRecipes).toHaveBeenCalled());
    expect(lastSearch()?.sort_by).toBe("alphabetical");
    expect(lastSearch()?.per_page).toBe(48);
  });

  it("lets a sort in the page address win over the saved default", async () => {
    vi.mocked(getPreferences).mockResolvedValue(
      preferences({ default_sort: "alphabetical" }),
    );
    nav.url = "http://localhost/recipes?sort=time_asc";
    render(Page);

    await waitFor(() => expect(searchRecipes).toHaveBeenCalled());
    expect(lastSearch()?.sort_by).toBe("time_asc");
  });

  it("shuffles afresh on each visit when the default sort is Random", async () => {
    vi.mocked(getPreferences).mockResolvedValue(
      preferences({ default_sort: "random" }),
    );
    const first = render(Page);
    await waitFor(() => expect(searchRecipes).toHaveBeenCalled());
    const firstSeed = lastSearch()?.seed;
    first.unmount();
    vi.mocked(searchRecipes).mockClear();
    render(Page);
    await waitFor(() => expect(searchRecipes).toHaveBeenCalled());

    expect(lastSearch()?.sort_by).toBe("random");
    expect(firstSeed).toBeGreaterThan(0);
    expect(lastSearch()?.seed).not.toBe(firstSeed);
  });

  it("keeps the shuffle that is in the page address", async () => {
    nav.url = "http://localhost/recipes?sort=random&seed=4242";
    render(Page);

    await waitFor(() => expect(searchRecipes).toHaveBeenCalled());
    expect(lastSearch()?.seed).toBe(4242);
  });

  it("sends no seed for the other sorts", async () => {
    render(Page);

    await waitFor(() => expect(searchRecipes).toHaveBeenCalled());
    expect(lastSearch()?.seed).toBeUndefined();
  });

  it("refetches the sidebar's collection counts on every visit", async () => {
    const first = render(Page);
    await waitFor(() => expect(getCollections).toHaveBeenCalledTimes(1));
    first.unmount();

    // A recipe starred on its own page changes a count while the list is away
    render(Page);

    await waitFor(() => expect(getCollections).toHaveBeenCalledTimes(2));
  });

  it("falls back to Recently Added and 24 when preferences cannot be loaded", async () => {
    vi.mocked(getPreferences).mockRejectedValue(new Error("offline"));
    render(Page);

    await waitFor(() => expect(searchRecipes).toHaveBeenCalled());
    expect(lastSearch()?.sort_by).toBe("recently_added");
    expect(lastSearch()?.per_page).toBe(24);
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
