/**
 * Centralized type definitions for the Recipe Catalog application
 */

// Re-export User type from users API
export type { User, UserPreferences, UserStats } from "#lib/api/users.js";

/**
 * Schema.org Recipe format
 * @see https://schema.org/Recipe
 */
export interface ParsedIngredient {
  raw: string;
  header?: boolean;
  quantity?: number | null;
  quantityMax?: number | null;
  unit?: string | null;
  item?: string | null;
  note?: string | null;
  group?: string | null;
}

export interface RecipeData {
  "@context"?: "https://schema.org";
  "@type"?: "Recipe";
  name?: string;
  description?: string;
  recipeIngredient?: string[];
  /** Server-built, one entry per recipeIngredient line (header lines have `header: true`) */
  parsedIngredients?: ParsedIngredient[];
  recipeInstructions?:
    | string
    | string[]
    | Array<{
        "@type": "HowToStep";
        text: string;
      }>;
  prepTime?: string;
  cookTime?: string;
  totalTime?: string;
  recipeYield?: string;
  recipeCuisine?: string;
  /** schema.org allows a string or a list; the server stores a list */
  recipeCategory?: string | string[];
  keywords?: string;
  image?: string | string[];
  images?: Array<{
    data?: string;
    mimeType?: string;
    url?: string;
  }>;
  author?: {
    "@type": "Person";
    name: string;
  };
  nutrition?: {
    "@type": "NutritionInformation";
    calories?: string;
    carbohydrateContent?: string;
    proteinContent?: string;
    fatContent?: string;
    servingSize?: string;
  };
  aggregateRating?: {
    "@type": "AggregateRating";
    ratingValue?: number;
    reviewCount?: number;
  };
  datePublished?: string;
  url?: string;
  suitableForDiet?: string[];
  equipment?: string[];
  notes?: string;
}

/**
 * Sort options for recipe searches
 */
export type RecipeSortBy =
  | "recently_added"
  | "alphabetical"
  | "time_asc"
  | "time_desc"
  | "recently_cooked"
  | "rating_desc"
  | "random";

/**
 * Recipe source types
 */
export type RecipeSourceType = "imported" | "manual" | "ai-generated";

/**
 * Theme options
 * - garden-fresh: Herb green with terracotta (also matches: classic, light)
 * - bistro: Burgundy with champagne gold (also matches: professional)
 * - dark: Dark mode
 * - high-contrast: WCAG AAA compliant
 * - ember: Warm dark, charcoal with terracotta
 * - coastal: Deep teal with coral
 * - farmhouse: Slate blue with antique mustard
 */
export type Theme =
  | "garden-fresh"
  | "bistro"
  | "dark"
  | "high-contrast"
  | "ember"
  | "coastal"
  | "farmhouse"
  | "classic"
  | "professional"
  | "light";

/**
 * View mode options
 */
export type ViewMode = "grid" | "list";

/**
 * Meal type for meal plans
 */
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";
