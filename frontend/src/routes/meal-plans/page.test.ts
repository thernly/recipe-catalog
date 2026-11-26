/**
 * Tests for the meal planner page
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";

vi.mock("$app/navigation", () => ({ goto: vi.fn() }));
vi.mock("#lib/api/meal-plans.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getCurrentWeekMealPlan: vi.fn(),
}));
vi.mock("#lib/api/recipes.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  searchRecipes: vi.fn(),
}));

vi.mock("#lib/api/shopping-lists.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  generateFromMealPlan: vi.fn(),
}));

vi.mock("#lib/utils/download.js", () => ({ downloadBlob: vi.fn() }));

import Page from "./+page.svelte";
import { downloadBlob } from "#lib/utils/download.js";
import { getCurrentWeekMealPlan } from "#lib/api/meal-plans.js";
import { searchRecipes } from "#lib/api/recipes.js";
import { generateFromMealPlan } from "#lib/api/shopping-lists.js";
import { wasAddedToList } from "#lib/utils/added-weeks.js";

const plan = {
  id: 1,
  household_id: 1,
  week_start_date: "2026-11-23",
  created_by_user_id: 2,
  created_at: "2026-11-23T00:00:00Z",
  updated_at: "2026-11-23T00:00:00Z",
  planned_meals: [
    {
      id: 9,
      meal_plan_id: 1,
      recipe_id: 4,
      recipe_name: "Lasagne",
      day_of_week: 0,
      meal_type: "dinner" as const,
      created_at: "2026-11-23T00:00:00Z",
      updated_at: "2026-11-23T00:00:00Z",
    },
  ],
};

describe("meal planner page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getCurrentWeekMealPlan).mockResolvedValue(plan);
    vi.mocked(searchRecipes).mockResolvedValue({
      recipes: [],
    } as unknown as Awaited<ReturnType<typeof searchRecipes>>);
  });

  it("keeps the week on screen while it reloads after a meal is edited", async () => {
    const { findByRole, queryByText, getByText } = render(Page);
    await fireEvent.click(await findByRole("button", { name: /Lasagne/ }));

    // The reload after the edit never finishes, so the page is caught mid-reload
    vi.mocked(getCurrentWeekMealPlan).mockReturnValue(new Promise(() => {}));
    await fireEvent.click(await findByRole("button", { name: "Save Changes" }));
    await waitFor(() =>
      expect(getCurrentWeekMealPlan).toHaveBeenCalledTimes(2),
    );

    expect(queryByText("Loading meal plan...")).toBeNull();
    expect(getByText("Lasagne")).toBeTruthy();
  });

  it("exports the week on screen as a calendar file", async () => {
    const { findByRole } = render(Page);

    await fireEvent.click(
      await findByRole("button", { name: /Export to Calendar/ }),
    );

    const [blob, filename] = vi.mocked(downloadBlob).mock.calls[0];
    expect(filename).toBe("meal-plan-2026-11-23.ics");
    expect(blob.type).toBe("text/calendar");
    expect(await blob.text()).toContain("SUMMARY:Dinner: Lasagne");
  });

  it("remembers which list a week was generated into", async () => {
    localStorage.clear();
    vi.mocked(generateFromMealPlan).mockResolvedValue({
      id: 31,
    } as Awaited<ReturnType<typeof generateFromMealPlan>>);
    const { findByRole } = render(Page);

    await fireEvent.click(
      await findByRole("button", { name: /Generate Shopping List/ }),
    );

    await waitFor(() => expect(wasAddedToList(plan.id, 31)).toBe(true));
  });

  it("leaves an unticked meal off the shopping list", async () => {
    const soup = {
      ...plan.planned_meals[0],
      id: 10,
      recipe_name: "Soup",
      day_of_week: 1,
    };
    vi.mocked(getCurrentWeekMealPlan).mockResolvedValue({
      ...plan,
      planned_meals: [...plan.planned_meals, soup],
    });
    vi.mocked(generateFromMealPlan).mockResolvedValue({
      id: 31,
    } as Awaited<ReturnType<typeof generateFromMealPlan>>);
    const { findByRole, findByText } = render(Page);

    await findByText("Meals to shop for (2 of 2)");
    await fireEvent.click(
      await findByRole("checkbox", { name: /Monday dinner: Lasagne/ }),
    );
    await findByText("Meals to shop for (1 of 2)");
    await fireEvent.click(
      await findByRole("button", { name: /Generate Shopping List/ }),
    );

    expect(vi.mocked(generateFromMealPlan).mock.calls[0][0]).toMatchObject({
      meal_plan_id: 1,
      selected_meal_ids: [10],
    });
  });

  it("sends no meal selection when every meal is ticked", async () => {
    vi.mocked(generateFromMealPlan).mockResolvedValue({
      id: 31,
    } as Awaited<ReturnType<typeof generateFromMealPlan>>);
    const { findByRole } = render(Page);

    await fireEvent.click(
      await findByRole("button", { name: /Generate Shopping List/ }),
    );

    expect(vi.mocked(generateFromMealPlan).mock.calls[0][0]).not.toHaveProperty(
      "selected_meal_ids",
    );
  });

  it("shows the loading message while another week loads", async () => {
    const { findByRole, findByText } = render(Page);
    await findByRole("button", { name: /Lasagne/ });

    vi.mocked(getCurrentWeekMealPlan).mockReturnValue(new Promise(() => {}));
    await fireEvent.click(await findByRole("button", { name: /Next Week/ }));

    expect(await findByText("Loading meal plan...")).toBeTruthy();
  });
});
