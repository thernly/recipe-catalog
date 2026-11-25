/**
 * Recipes inside a collection must open, and their edit button must work.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";

vi.mock("$app/navigation", () => ({ goto: vi.fn() }));
vi.mock("#lib/api/collections.js", () => ({
  getCollection: vi.fn(),
  getCollectionRecipes: vi.fn(),
  exportCollectionPdf: vi.fn(),
}));
vi.mock("#lib/api/recipes.js", () => ({ deleteRecipe: vi.fn() }));

import Page from "./+page.svelte";
import { goto } from "$app/navigation";
import { getCollection, getCollectionRecipes } from "#lib/api/collections.js";

describe("collection page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getCollection).mockResolvedValue({
      id: 4,
      name: "Weeknight",
      recipe_count: 1,
    } as Awaited<ReturnType<typeof getCollection>>);
    vi.mocked(getCollectionRecipes).mockResolvedValue([
      { id: 12, name: "Stew", source_type: "manual" },
    ] as Awaited<ReturnType<typeof getCollectionRecipes>>);
  });

  it("links each recipe to its page and returns to the collection", async () => {
    const { findByRole } = render(Page, { params: { id: "4" } });

    const link = await findByRole("link", { name: /Stew/ });
    expect(link.getAttribute("href")).toBe(
      "/recipes/12?returnUrl=%2Fcollections%2F4",
    );
  });

  it("opens the editor from the card's edit button", async () => {
    const { findByRole } = render(Page, { params: { id: "4" } });

    await fireEvent.click(await findByRole("button", { name: "Edit recipe" }));
    expect(goto).toHaveBeenCalledWith("/recipes/12/edit");
  });
});
