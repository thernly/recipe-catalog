/**
 * Tests for the import page: saving a recipe from a web address
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";

vi.mock("#lib/api/recipes.js", () => ({
  importRecipes: vi.fn(),
  restoreBackup: vi.fn(),
  importRecipeFromUrl: vi.fn(),
}));
vi.mock("#lib/api/collections.js", () => ({ getCollections: vi.fn() }));

import Page from "./+page.svelte";
import { importRecipeFromUrl } from "#lib/api/recipes.js";
import { getCollections } from "#lib/api/collections.js";

describe("import page: from a web address", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getCollections).mockResolvedValue([]);
  });

  it("saves the recipe and links to it", async () => {
    vi.mocked(importRecipeFromUrl).mockResolvedValue({
      status: "created",
      id: 12,
      message: "Recipe saved",
    });
    const { getByLabelText, getByRole, findByRole } = render(Page);

    await fireEvent.input(getByLabelText("Web address"), {
      target: { value: "https://example.com/dal" },
    });
    await fireEvent.click(getByRole("button", { name: "Save Recipe" }));

    const link = await findByRole("link", { name: "Open the recipe" });
    expect(link.getAttribute("href")).toBe("/recipes/12");
    expect(importRecipeFromUrl).toHaveBeenCalledWith("https://example.com/dal");
    expect((getByLabelText("Web address") as HTMLInputElement).value).toBe("");
  });

  it("shows the server's reason and keeps the address when it fails", async () => {
    vi.mocked(importRecipeFromUrl).mockRejectedValue(
      new Error("No recipe was found on that page."),
    );
    const { getByLabelText, getByRole, findByRole } = render(Page);

    await fireEvent.input(getByLabelText("Web address"), {
      target: { value: "https://example.com/news" },
    });
    await fireEvent.click(getByRole("button", { name: "Save Recipe" }));

    expect((await findByRole("alert")).textContent).toContain(
      "No recipe was found on that page.",
    );
    expect((getByLabelText("Web address") as HTMLInputElement).value).toBe(
      "https://example.com/news",
    );
  });
});
