import { API_V1_URL } from "#lib/config.js";
import type { RecipeSummary } from "#lib/api/recipes.js";

/**
 * Where a listed recipe's picture comes from: the stored photo, served by the
 * app, or else the picture's address on the recipe's site (which can vanish).
 */
export function recipeImageSrc(
  recipe: Pick<RecipeSummary, "id" | "has_photo" | "image_url">,
): string | null {
  if (recipe.has_photo) return `${API_V1_URL}/recipes/${recipe.id}/photo`;
  return recipe.image_url || null;
}
