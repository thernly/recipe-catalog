import type { ImportResult, RestoredCounts } from "#lib/api/recipes.js";

export interface ImportOutcome {
  file: string;
  /** The server's result, or the reason the whole file was rejected. */
  result: ImportResult | string;
}

const MAX_PROBLEMS_SHOWN = 20;

function count(n: number, noun: string): string {
  return `${n} ${noun}${n === 1 ? "" : "s"}`;
}

/** What a backup restore added beyond recipes, and what it left out; "" for nothing. */
export function summarizeRestored(restored: RestoredCounts | null): string {
  if (!restored) return "";
  const added = [
    restored.collections && count(restored.collections, "collection"),
    restored.collection_recipes &&
      `${count(restored.collection_recipes, "recipe")} put back in collections`,
    restored.planned_meals && count(restored.planned_meals, "planned meal"),
    restored.shopping_lists && count(restored.shopping_lists, "shopping list"),
  ].filter(Boolean);
  const notes = [added.length ? `Also restored: ${added.join(", ")}.` : ""];
  if (restored.planned_meals_skipped) {
    notes.push(
      `${count(restored.planned_meals_skipped, "planned meal")} left out because the recipe is not in the backup.`,
    );
  }
  if (restored.shopping_lists_skipped) {
    notes.push(
      `${count(restored.shopping_lists_skipped, "shopping list")} already here.`,
    );
  }
  return notes.filter(Boolean).join(" ");
}

/** Turn per-file import results into what the user is told. */
export function summarizeImport(outcomes: ImportOutcome[]): {
  summary: string;
  problems: string[];
  imported: number;
} {
  let created = 0;
  let updated = 0;
  let skipped = 0;
  const problems: string[] = [];

  for (const { file, result } of outcomes) {
    if (typeof result === "string") {
      problems.push(`${file}: ${result}`);
      continue;
    }
    created += result.details.created;
    updated += result.details.updated;
    skipped += result.details.skipped;
    for (const failure of result.details.errors) {
      const { name, error } = failure as { name?: string; error?: string };
      problems.push(
        `${file}: "${name || "Unknown"}" – ${error || "could not be imported"}`,
      );
    }
  }

  const parts = [`${count(created, "new recipe")} added`];
  if (updated) parts.push(`${updated} updated`);
  if (skipped) parts.push(`${count(skipped, "duplicate")} skipped`);
  if (problems.length) parts.push(`${problems.length} failed`);

  const shown = problems.slice(0, MAX_PROBLEMS_SHOWN);
  if (problems.length > shown.length) {
    shown.push(`… and ${problems.length - shown.length} more`);
  }
  return {
    summary: parts.join(", "),
    problems: shown,
    imported: created + updated,
  };
}
