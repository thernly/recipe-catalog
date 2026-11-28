import { describe, it, expect } from "vitest";
import { render } from "@testing-library/svelte/svelte5";
import RecipeListItem from "./RecipeListItem.svelte";
import type { RecipeSummary } from "#lib/api/recipes.js";

const recipe: RecipeSummary = {
  id: 1,
  name: "Roast Chicken",
  source_type: "imported",
  source_url: "https://www.seriouseats.com/roast-chicken",
  created_at: "2024-01-01T00:00:00Z",
};

describe("RecipeListItem", () => {
  it("shows the source site instead of a plain 'Imported'", () => {
    const { getByText, queryByText } = render(RecipeListItem, {
      props: { recipe },
    });
    expect(getByText("seriouseats.com")).toBeTruthy();
    expect(queryByText("Imported")).toBeNull();
  });

  it("falls back to 'Imported' without a usable source address", () => {
    const { getByText } = render(RecipeListItem, {
      props: { recipe: { ...recipe, source_url: "not a url" } },
    });
    expect(getByText("Imported")).toBeTruthy();
  });
});
