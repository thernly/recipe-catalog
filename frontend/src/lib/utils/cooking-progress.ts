/**
 * Where you are in cooking a recipe: ticked ingredients, finished steps, the chosen
 * scale and whether cook mode is on. Kept in this browser so a reload, a locked phone
 * or a trip to the shopping list does not lose it.
 */
export interface CookingProgress {
  ingredients: number[];
  steps: number[];
  scale: number;
  cookMode: boolean;
}

/** After this long the ticks are from another day's cooking, so they are dropped. */
export const PROGRESS_MAX_AGE_MS = 12 * 60 * 60 * 1000;

const key = (recipeId: number) => `recipe-progress-${recipeId}`;
const indexes = (value: unknown): number[] =>
  Array.isArray(value) ? value.filter((n) => Number.isInteger(n)) : [];

export function loadProgress(
  recipeId: number,
  now = Date.now(),
): CookingProgress {
  let stored: Record<string, unknown> = {};
  try {
    const parsed = JSON.parse(localStorage.getItem(key(recipeId)) ?? "{}");
    const fresh =
      typeof parsed?.savedAt === "number" &&
      now - parsed.savedAt <= PROGRESS_MAX_AGE_MS;
    if (fresh) stored = parsed;
  } catch {
    // Storage blocked or the entry is damaged: start fresh
  }
  return {
    ingredients: indexes(stored.ingredients),
    steps: indexes(stored.steps),
    scale: typeof stored.scale === "number" ? stored.scale : 1,
    cookMode: stored.cookMode === true,
  };
}

export function saveProgress(
  recipeId: number,
  progress: CookingProgress,
  now = Date.now(),
): void {
  const nothing =
    progress.ingredients.length === 0 &&
    progress.steps.length === 0 &&
    progress.scale === 1 &&
    !progress.cookMode;
  try {
    if (nothing) localStorage.removeItem(key(recipeId));
    else
      localStorage.setItem(
        key(recipeId),
        JSON.stringify({ ...progress, savedAt: now }),
      );
  } catch {
    // Storage blocked or full: the page still works, it just will not remember
  }
}
