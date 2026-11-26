/**
 * Tests for the recipe page: group headings, load failures and Duplicate
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import { get } from "svelte/store";

vi.mock("$app/navigation", () => ({
  goto: vi.fn(),
  afterNavigate: (fn: () => void) => fn(),
}));
vi.mock("$app/state", () => ({
  page: { url: new URL("http://localhost/recipes/7"), params: { id: "7" } },
}));
vi.mock("#lib/api/recipes.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getRecipe: vi.fn(),
  duplicateRecipe: vi.fn(),
}));
vi.mock("#lib/api/recipe-notes.js", () => ({
  listNotes: vi.fn().mockResolvedValue([]),
}));
vi.mock("#lib/api/collections.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getCollections: vi.fn().mockResolvedValue([]),
}));

import Page from "./+page.svelte";
import { goto } from "$app/navigation";
import { ApiError } from "#lib/api/client.js";
import { getRecipe, duplicateRecipe, type Recipe } from "#lib/api/recipes.js";
import { dialog } from "#lib/stores/dialog.js";

const recipe = {
  id: 7,
  user_id: 1,
  name: "Pie",
  recipe_data: {
    recipeIngredient: ["For the crust:", "2 cups flour"],
    recipeInstructions: ["Bake."],
    parsedIngredients: [
      { raw: "For the crust:", header: true, group: "For the crust" },
      { raw: "2 cups flour", quantity: 2, unit: "cup", item: "flour" },
    ],
  },
  source_type: "manual",
  is_modified: false,
  created_at: "2026-11-01T00:00:00Z",
  updated_at: "2026-11-01T00:00:00Z",
} as unknown as Recipe;

describe("recipe page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getRecipe).mockResolvedValue(recipe);
    dialog.close();
    localStorage.clear();
    sessionStorage.clear();
  });

  // After Edit and Save the page address no longer carries the list's address
  it("goes back to the list as it was last seen, sort and all", async () => {
    sessionStorage.setItem("recipes-list-url", "/recipes?sort=alphabetical");
    const { findAllByRole } = render(Page, { params: { id: "7" } });

    const [back] = await findAllByRole("button", { name: "Back to Recipes" });
    await fireEvent.click(back);

    expect(goto).toHaveBeenCalledWith("/recipes?sort=alphabetical");
  });

  it("shows a group heading as a heading, not a tickable ingredient", async () => {
    const { findByText, getAllByRole, queryByRole } = render(Page, {
      params: { id: "7" },
    });

    expect(await findByText("For the crust:")).toBeTruthy();
    const ticks = getAllByRole("checkbox").map((box) => box.id);
    expect(ticks).toEqual(["ingredient-1"]);
    expect(queryByRole("button", { name: /Add For the crust/ })).toBeNull();
  });

  it("offers to try again when the recipe fails to load", async () => {
    vi.mocked(getRecipe).mockRejectedValueOnce(
      new TypeError("Failed to fetch"),
    );
    const { findByRole, findByText, queryByText } = render(Page, {
      params: { id: "7" },
    });

    expect(await findByText("Could not load this recipe")).toBeTruthy();
    expect(queryByText("Recipe not found")).toBeNull();
    await fireEvent.click(await findByRole("button", { name: "Try again" }));

    expect(await findByRole("heading", { name: "Pie" })).toBeTruthy();
  });

  it("says a recipe is not found only when the server says so", async () => {
    vi.mocked(getRecipe).mockRejectedValue(
      new ApiError("Recipe not found", "RECIPE_NOT_FOUND", {}, 404),
    );
    const { findByText, queryByRole } = render(Page, { params: { id: "7" } });

    expect(await findByText("Recipe not found")).toBeTruthy();
    expect(queryByRole("button", { name: "Try again" })).toBeNull();
  });

  it("asks before making a copy", async () => {
    vi.mocked(duplicateRecipe).mockResolvedValue({ ...recipe, id: 8 });
    const { findByRole } = render(Page, { params: { id: "7" } });

    await fireEvent.click(
      await findByRole("button", { name: /Duplicate|Save a copy/ }),
    );
    expect(duplicateRecipe).not.toHaveBeenCalled();
    expect(get(dialog).message).toContain('"Pie (Copy)"');

    await get(dialog).onConfirm();
    await waitFor(() => expect(goto).toHaveBeenCalledWith("/recipes/8/edit"));
  });

  it("multiplies ingredient amounts when a scale button is pressed", async () => {
    const { findByRole, findByText } = render(Page, { params: { id: "7" } });

    await fireEvent.click(await findByRole("button", { name: "2×" }));

    expect(await findByText(/4 cups flour/)).toBeTruthy();
  });

  it("links each keyword to a search for it", async () => {
    vi.mocked(getRecipe).mockResolvedValue({
      ...recipe,
      recipe_data: { ...recipe.recipe_data, keywords: "brunch, date night" },
    } as unknown as Recipe);
    const { findByRole } = render(Page, { params: { id: "7" } });

    const tag = await findByRole("link", { name: "date night" });
    expect(tag.getAttribute("href")).toBe("/recipes?q=date%20night");
  });

  describe("cook mode", () => {
    const twoSteps = {
      ...recipe,
      recipe_data: {
        ...recipe.recipe_data,
        recipeInstructions: ["Mix.", "Bake."],
      },
    } as unknown as Recipe;
    const currentStep = (container: HTMLElement) =>
      container.querySelector('[aria-current="step"]')?.textContent;

    beforeEach(() => vi.mocked(getRecipe).mockResolvedValue(twoSteps));

    it("hides the button bar and highlights the first unticked step", async () => {
      const { container, findByRole, queryByRole } = render(Page, {
        params: { id: "7" },
      });
      expect(currentStep(container)).toBeUndefined();

      await fireEvent.click(await findByRole("button", { name: "Cook mode" }));

      expect(queryByRole("button", { name: /Duplicate/ })).toBeNull();
      expect(currentStep(container)).toContain("Mix.");

      await fireEvent.click(
        await findByRole("button", { name: "Mark step 1 as complete" }),
      );
      expect(currentStep(container)).toContain("Bake.");
    });

    it("is still on, with its ticks, after the page is reopened", async () => {
      const first = render(Page, { params: { id: "7" } });
      await fireEvent.click(
        await first.findByRole("button", { name: "Cook mode" }),
      );
      await fireEvent.click(
        await first.findByRole("button", { name: "Mark step 1 as complete" }),
      );
      first.unmount();

      const { container, findByRole } = render(Page, { params: { id: "7" } });

      expect(
        await findByRole("button", { name: "Exit cook mode" }),
      ).toBeTruthy();
      expect(currentStep(container)).toContain("Bake.");
    });
  });
});
