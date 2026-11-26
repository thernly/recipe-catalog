import type { MealPlan } from "#lib/api/meal-plans.js";

const MEAL_ORDER = ["breakfast", "lunch", "dinner", "snack", "other"];

// iCalendar text: backslash, semicolon, comma and line breaks are escaped
const text = (value: string) =>
  value
    .replace(/\\/g, "\\\\")
    .replace(/([;,])/g, "\\$1")
    .replace(/\r?\n/g, "\\n");

// YYYYMMDD for the day `offset` days after an ISO date, worked out in UTC so
// the viewer's timezone cannot move it
function day(isoDate: string, offset: number): string {
  const date = new Date(`${isoDate}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + offset);
  return date.toISOString().slice(0, 10).replace(/-/g, "");
}

/**
 * A week's meal plan as an iCalendar (.ics) file: one all-day event per meal,
 * "Dinner: Lasagne", linking back to the recipe at `origin`. Each event's id
 * is fixed, so importing the same week again updates it in calendars that
 * honour ids, rather than adding a second copy.
 */
export function mealPlanToIcs(
  plan: MealPlan,
  origin: string,
  now: Date = new Date(),
): string {
  const stamp = now.toISOString().replace(/[-:]|\.\d+/g, "");
  const meals = [...plan.planned_meals].sort(
    (a, b) =>
      a.day_of_week - b.day_of_week ||
      MEAL_ORDER.indexOf(a.meal_type) - MEAL_ORDER.indexOf(b.meal_type),
  );
  // ponytail: lines are not folded at 75 characters (the standard says
  // "should"); calendars accept long lines. Fold if one ever objects.
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Recipe Catalog//Meal Plan//EN",
    ...meals.flatMap((meal) => {
      const type = meal.meal_type[0].toUpperCase() + meal.meal_type.slice(1);
      // A free-text meal ("Leftovers") has no recipe to link to
      const url = meal.recipe_id ? `${origin}/recipes/${meal.recipe_id}` : "";
      const details = [
        meal.servings ? `Servings: ${meal.servings}` : "",
        meal.notes ?? "",
        url,
      ].filter(Boolean);
      return [
        "BEGIN:VEVENT",
        `UID:planned-meal-${meal.id}@recipe-catalog`,
        `DTSTAMP:${stamp}`,
        `DTSTART;VALUE=DATE:${day(plan.week_start_date, meal.day_of_week)}`,
        `DTEND;VALUE=DATE:${day(plan.week_start_date, meal.day_of_week + 1)}`,
        `SUMMARY:${text(`${type}: ${meal.recipe_name || meal.title || "Recipe"}`)}`,
        `DESCRIPTION:${text(details.join("\n"))}`,
        ...(url ? [`URL:${url}`] : []),
        "TRANSP:TRANSPARENT",
        "END:VEVENT",
      ];
    }),
    "END:VCALENDAR",
  ];
  return lines.join("\r\n") + "\r\n";
}
