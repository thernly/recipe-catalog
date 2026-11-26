import { describe, it, expect } from "vitest";
import { summarizeImport, summarizeRestored } from "./import-summary";
import type { ImportResult } from "#lib/api/recipes.js";

function result(details: Partial<ImportResult["details"]>): ImportResult {
  return {
    success: true,
    message: "",
    details: {
      total: 0,
      created: 0,
      updated: 0,
      skipped: 0,
      failed: 0,
      errors: [],
      items: [],
      ...details,
    },
  };
}

describe("summarizeRestored", () => {
  const none = {
    collections: 0,
    collection_recipes: 0,
    meal_plans: 0,
    planned_meals: 0,
    planned_meals_skipped: 0,
    shopping_lists: 0,
    shopping_lists_skipped: 0,
  };

  it("says nothing for a recipes-only restore or when nothing was added", () => {
    expect(summarizeRestored(null)).toBe("");
    expect(summarizeRestored(none)).toBe("");
  });

  it("lists what was added and what was left out", () => {
    const text = summarizeRestored({
      ...none,
      collections: 1,
      collection_recipes: 3,
      planned_meals: 2,
      planned_meals_skipped: 1,
      shopping_lists_skipped: 2,
    });

    expect(text).toBe(
      "Also restored: 1 collection, 3 recipes put back in collections, 2 planned meals. " +
        "1 planned meal left out because the recipe is not in the backup. " +
        "2 shopping lists already here.",
    );
  });
});

describe("summarizeImport", () => {
  it("reports recipes, not files", () => {
    const out = summarizeImport([
      { file: "a.json", result: result({ created: 3, skipped: 2 }) },
      { file: "b.json", result: result({ created: 1, updated: 4 }) },
    ]);

    expect(out.summary).toBe(
      "4 new recipes added, 4 updated, 2 duplicates skipped",
    );
    expect(out.problems).toEqual([]);
    expect(out.imported).toBe(8);
  });

  it("names each recipe that failed and why", () => {
    const out = summarizeImport([
      {
        file: "backup.json",
        result: result({
          failed: 1,
          errors: [
            { index: 0, name: "Stew", error: "Recipe name is required" },
          ],
        }),
      },
      { file: "broken.json", result: "Invalid JSON file" },
    ]);

    expect(out.summary).toBe("0 new recipes added, 2 failed");
    expect(out.problems).toEqual([
      'backup.json: "Stew" – Recipe name is required',
      "broken.json: Invalid JSON file",
    ]);
    expect(out.imported).toBe(0);
  });
});
