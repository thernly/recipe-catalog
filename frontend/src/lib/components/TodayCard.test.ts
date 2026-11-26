import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/svelte/svelte5";

vi.mock("#lib/api/meal-plans.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listMealPlans: vi.fn(),
  getMealPlan: vi.fn(),
}));
vi.mock("#lib/api/shopping-lists.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listShoppingLists: vi.fn(),
}));

import TodayCard from "./TodayCard.svelte";
import { listMealPlans, getMealPlan } from "#lib/api/meal-plans.js";
import { listShoppingLists } from "#lib/api/shopping-lists.js";

const stamp = { created_at: "", updated_at: "" };
const meal = (
  id: number,
  day_of_week: number,
  meal_type: "breakfast" | "dinner",
  recipe_name: string,
) => ({
  id,
  meal_plan_id: 1,
  recipe_id: id * 10,
  recipe_name,
  day_of_week,
  meal_type,
  ...stamp,
});
const summary = {
  id: 1,
  household_id: 1,
  week_start_date: "2026-11-23",
  created_at: "",
  meal_count: 3,
};
const listSummary = (id: number, name: string, created_at: string) => ({
  id,
  household_id: 1,
  name,
  status: "active" as const,
  created_by_user_id: 2,
  created_at,
  item_count: 8,
  checked_count: 3,
});

describe("TodayCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Thursday 26 November 2026: day 3 of the week that starts Monday the 23rd
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 10, 26, 12));
    vi.mocked(listMealPlans).mockResolvedValue([summary]);
    vi.mocked(getMealPlan).mockResolvedValue({
      id: 1,
      household_id: 1,
      week_start_date: "2026-11-23",
      created_by_user_id: 2,
      ...stamp,
      planned_meals: [
        meal(1, 3, "dinner", "Lasagne"),
        meal(2, 3, "breakfast", "Porridge"),
        meal(3, 4, "dinner", "Tomorrow's Curry"),
      ],
    });
    vi.mocked(listShoppingLists).mockResolvedValue([
      listSummary(4, "Old list", "2026-11-01T00:00:00Z"),
      listSummary(5, "This week", "2026-11-23T00:00:00Z"),
    ]);
  });
  afterEach(() => vi.useRealTimers());

  it("links today's meals in meal order and leaves out other days", async () => {
    const { findByRole, getAllByRole, queryByText } = render(TodayCard);

    const lasagne = await findByRole("link", { name: "Lasagne" });
    expect(lasagne.getAttribute("href")).toBe("/recipes/10");
    const names = getAllByRole("listitem").map((li) => li.textContent);
    expect(names[0]).toContain("Porridge");
    expect(names[1]).toContain("Lasagne");
    expect(queryByText("Tomorrow's Curry")).toBeNull();
  });

  it("links the newest active shopping list with its progress", async () => {
    const { findByRole, getByText } = render(TodayCard);

    const list = await findByRole("link", { name: "This week" });
    expect(list.getAttribute("href")).toBe("/shopping-lists/5");
    expect(getByText("3 of 8 checked")).toBeTruthy();
    expect(listShoppingLists).toHaveBeenCalledWith("active");
  });

  it("says so when nothing is planned and there is no list", async () => {
    vi.mocked(listMealPlans).mockResolvedValue([]);
    vi.mocked(listShoppingLists).mockRejectedValue(new Error("offline"));
    const { findByText, getByText } = render(TodayCard);

    expect(await findByText("Nothing planned for today.")).toBeTruthy();
    expect(getByText("No active shopping list.")).toBeTruthy();
    expect(getMealPlan).not.toHaveBeenCalled();
  });
});
