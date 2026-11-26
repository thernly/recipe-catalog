import { describe, expect, it } from "vitest";
import { mealPlanToIcs } from "./meal-plan-calendar.js";
import type { MealPlan, PlannedMeal } from "#lib/api/meal-plans.js";

const meal = (fields: Partial<PlannedMeal>): PlannedMeal => ({
  id: 1,
  meal_plan_id: 9,
  recipe_id: 40,
  recipe_name: "Lasagne",
  day_of_week: 0,
  meal_type: "dinner",
  created_at: "",
  updated_at: "",
  ...fields,
});

const plan = (planned_meals: PlannedMeal[]): MealPlan => ({
  id: 9,
  household_id: 1,
  week_start_date: "2026-11-30",
  created_by_user_id: 1,
  created_at: "",
  updated_at: "",
  planned_meals,
});

const now = new Date("2026-11-26T12:34:56Z");

describe("mealPlanToIcs", () => {
  it("makes one all-day event per meal, on the right day", () => {
    const ics = mealPlanToIcs(
      plan([
        // Wednesday; the week runs over the end of the month
        meal({
          id: 5,
          day_of_week: 2,
          servings: 6,
          notes: "double; the garlic",
        }),
      ]),
      "https://recipes.example",
      now,
    );

    expect(ics.split("\r\n")).toEqual([
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//Recipe Catalog//Meal Plan//EN",
      "BEGIN:VEVENT",
      "UID:planned-meal-5@recipe-catalog",
      "DTSTAMP:20261126T123456Z",
      "DTSTART;VALUE=DATE:20261202",
      "DTEND;VALUE=DATE:20261203",
      "SUMMARY:Dinner: Lasagne",
      "DESCRIPTION:Servings: 6\\ndouble\\; the garlic\\nhttps://recipes.example/recipes/40",
      "URL:https://recipes.example/recipes/40",
      "TRANSP:TRANSPARENT",
      "END:VEVENT",
      "END:VCALENDAR",
      "",
    ]);
  });

  it("lists meals by day, then breakfast before dinner", () => {
    const ics = mealPlanToIcs(
      plan([
        meal({ id: 1, day_of_week: 1, recipe_name: "Curry" }),
        meal({ id: 2, day_of_week: 0, recipe_name: "Stew, with dumplings" }),
        meal({
          id: 3,
          day_of_week: 0,
          meal_type: "breakfast",
          recipe_name: "",
        }),
      ]),
      "",
      now,
    );

    expect(ics.match(/^SUMMARY:.*$/gm)).toEqual([
      "SUMMARY:Breakfast: Recipe",
      "SUMMARY:Dinner: Stew\\, with dumplings",
      "SUMMARY:Dinner: Curry",
    ]);
  });
});
