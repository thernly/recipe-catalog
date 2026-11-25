/**
 * The statistics tiles read the field names the stats endpoint actually sends.
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/svelte/svelte5";
import StatsSection from "./StatsSection.svelte";
import type { User } from "#lib/api/users.js";

describe("StatsSection", () => {
  it("shows the imported and manual counts", () => {
    const { getByText } = render(StatsSection, {
      // Shape of GET /api/v1/users/me/stats
      stats: {
        total_recipes: 12,
        imported_recipes: 9,
        manual_recipes: 3,
        total_collections: 2,
        trashed_recipes: 1,
      },
      user: { display_name: "Sam", created_at: "2026-01-01T00:00:00Z" } as User,
    });

    expect(getByText("Imported").previousElementSibling?.textContent).toBe("9");
    expect(getByText("Manual Entry").previousElementSibling?.textContent).toBe(
      "3",
    );
  });
});
