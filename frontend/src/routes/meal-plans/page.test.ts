/**
 * Tests for the meal planner page
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";

vi.mock("$app/navigation", () => ({ goto: vi.fn() }));
vi.mock("#lib/api/meal-plans.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getCurrentWeekMealPlan: vi.fn(),
  addPlannedMeal: vi.fn(),
}));
vi.mock("#lib/api/recipes.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  searchRecipes: vi.fn(),
}));

vi.mock("#lib/api/shopping-lists.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  generateFromMealPlan: vi.fn(),
  previewFromMealPlan: vi.fn(),
}));

vi.mock("#lib/utils/download.js", () => ({ downloadBlob: vi.fn() }));

import Page from "./+page.svelte";
import { downloadBlob } from "#lib/utils/download.js";
import {
  addPlannedMeal,
  formatDateISO,
  getCurrentWeekMealPlan,
  getWeekStart,
} from "#lib/api/meal-plans.js";
import { get } from "svelte/store";
import { dialog } from "#lib/stores/dialog.js";
import { searchRecipes } from "#lib/api/recipes.js";
import {
  generateFromMealPlan,
  previewFromMealPlan,
} from "#lib/api/shopping-lists.js";
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

  it("previews the ingredients of the ticked meals, and drops the preview when a tick changes", async () => {
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
    vi.mocked(previewFromMealPlan).mockResolvedValue([
      { item_name: "stock", quantity: "2", unit: "cup", notes: "for Soup" },
    ]);
    const { findByRole, findByText, queryByText } = render(Page);

    await fireEvent.click(
      await findByRole("checkbox", { name: /Monday dinner: Lasagne/ }),
    );
    await fireEvent.click(
      await findByRole("button", { name: "Preview ingredients" }),
    );

    expect(await findByText(/stock\s+\(2 cups\)/)).toBeTruthy();
    expect(await findByText("for Soup")).toBeTruthy();
    expect(previewFromMealPlan).toHaveBeenCalledWith({
      meal_plan_id: 1,
      selected_meal_ids: [10],
    });
    expect(generateFromMealPlan).not.toHaveBeenCalled();

    await fireEvent.click(
      await findByRole("checkbox", { name: /Monday dinner: Lasagne/ }),
    );
    await waitFor(() => expect(queryByText("for Soup")).toBeNull());
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

  describe("free-text meals", () => {
    const leftovers = {
      ...plan.planned_meals[0],
      id: 12,
      recipe_id: null,
      recipe_name: null,
      title: "Leftovers",
      day_of_week: 1,
    };

    it("adds a meal that is just text, with no recipe", async () => {
      vi.mocked(addPlannedMeal).mockResolvedValue(leftovers);
      const { findByRole, findByLabelText } = render(Page);

      await fireEvent.click(
        await findByRole("button", { name: "Add lunch on Tuesday" }),
      );
      await fireEvent.input(
        await findByLabelText("Or something without a recipe"),
        { target: { value: " Eating out " } },
      );
      await fireEvent.click(await findByRole("button", { name: "Add Meal" }));

      await waitFor(() =>
        expect(addPlannedMeal).toHaveBeenCalledWith(1, {
          title: "Eating out",
          day_of_week: 1,
          meal_type: "lunch",
          servings: undefined,
          notes: undefined,
        }),
      );
    });

    it("shows a newly added meal in the grid without leaving the page", async () => {
      vi.mocked(addPlannedMeal).mockResolvedValue(leftovers);
      const { findByRole, findByLabelText } = render(Page);

      await fireEvent.click(
        await findByRole("button", { name: "Add dinner on Tuesday" }),
      );
      await fireEvent.input(
        await findByLabelText("Or something without a recipe"),
        { target: { value: "Leftovers" } },
      );
      // The reload after the add returns the week with the new meal in it
      vi.mocked(getCurrentWeekMealPlan).mockResolvedValue({
        ...plan,
        planned_meals: [...plan.planned_meals, leftovers],
      });
      await fireEvent.click(await findByRole("button", { name: "Add Meal" }));

      expect(await findByRole("button", { name: /Leftovers/ })).toBeTruthy();
    });

    it("shows it by its text and leaves it out of the meals to shop for", async () => {
      vi.mocked(getCurrentWeekMealPlan).mockResolvedValue({
        ...plan,
        planned_meals: [...plan.planned_meals, leftovers],
      });
      const { findByRole, findByText, queryByRole } = render(Page);

      expect(await findByRole("button", { name: /Leftovers/ })).toBeTruthy();
      expect(await findByText("Meals to shop for (1 of 1)")).toBeTruthy();
      expect(queryByRole("checkbox", { name: /Leftovers/ })).toBeNull();
    });
  });

  describe("Copy Last Week", () => {
    const thisWeek = formatDateISO(getWeekStart());
    const empty = { ...plan, id: 2, planned_meals: [] };

    // The week on screen is `shown`; any other week asked for is last week's
    const weeks = (shown: typeof plan) =>
      vi
        .mocked(getCurrentWeekMealPlan)
        .mockImplementation(async (week) => (week === thisWeek ? shown : plan));

    it("adds last week's meals to an empty week, same day and meal", async () => {
      weeks(empty);
      const { findByRole } = render(Page);

      await fireEvent.click(
        await findByRole("button", { name: /Copy Last Week/ }),
      );

      await waitFor(() =>
        expect(addPlannedMeal).toHaveBeenCalledWith(2, {
          recipe_id: 4,
          day_of_week: 0,
          meal_type: "dinner",
          servings: undefined,
          notes: undefined,
        }),
      );
      expect(get(dialog).open).toBe(false);
    });

    it("asks first when the week already has meals", async () => {
      weeks({ ...plan, id: 2 });
      const { findByRole } = render(Page);

      await fireEvent.click(
        await findByRole("button", { name: /Copy Last Week/ }),
      );
      expect(addPlannedMeal).not.toHaveBeenCalled();
      expect(get(dialog).message).toContain("added alongside");

      await get(dialog).onConfirm();
      await waitFor(() => expect(addPlannedMeal).toHaveBeenCalledOnce());
    });

    it("copies a free-text meal as free text", async () => {
      vi.mocked(getCurrentWeekMealPlan).mockImplementation(async (week) =>
        week === thisWeek
          ? empty
          : {
              ...plan,
              planned_meals: [
                {
                  ...plan.planned_meals[0],
                  recipe_id: null,
                  recipe_name: null,
                  title: "Leftovers",
                },
              ],
            },
      );
      const { findByRole } = render(Page);

      await fireEvent.click(
        await findByRole("button", { name: /Copy Last Week/ }),
      );

      await waitFor(() =>
        expect(addPlannedMeal).toHaveBeenCalledWith(2, {
          title: "Leftovers",
          day_of_week: 0,
          meal_type: "dinner",
          servings: undefined,
          notes: undefined,
        }),
      );
    });
  });

  it("shows the loading message while another week loads", async () => {
    const { findByRole, findByText } = render(Page);
    await findByRole("button", { name: /Lasagne/ });

    vi.mocked(getCurrentWeekMealPlan).mockReturnValue(new Promise(() => {}));
    await fireEvent.click(await findByRole("button", { name: /Next Week/ }));

    expect(await findByText("Loading meal plan...")).toBeTruthy();
  });
});
