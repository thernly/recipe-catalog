/**
 * Which shopping lists a week's meal plan has already been added to, so the
 * meal planner can warn before adding it again (which doubles the amounts).
 */
// ponytail: remembered per browser, so a housemate's add, or one made on another
// device, is not seen. Record the source meal plan on the list (server side) if
// that matters.
const KEY = "meal-plans-added-to-lists";
const MAX_ENTRIES = 100;

const entry = (mealPlanId: number, listId: number) => `${mealPlanId}:${listId}`;

function read(): string[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return []; // storage blocked or damaged: no warning, adding still works
  }
}

export function wasAddedToList(mealPlanId: number, listId: number): boolean {
  return read().includes(entry(mealPlanId, listId));
}

export function rememberAddedToList(mealPlanId: number, listId: number): void {
  const entries = read().filter((e) => e !== entry(mealPlanId, listId));
  entries.push(entry(mealPlanId, listId));
  try {
    localStorage.setItem(KEY, JSON.stringify(entries.slice(-MAX_ENTRIES)));
  } catch {
    // storage blocked or full
  }
}
