import { describe, it, expect } from "vitest";
import { summarizeImport } from "./import-summary";
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
