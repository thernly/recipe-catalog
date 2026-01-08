/**
 * Centralized type definitions for the Recipe Catalog application
 */

// Re-export User type from users API
export type { User, UserPreferences, UserStats } from "$lib/api/users";

/**
 * Schema.org Recipe format
 * @see https://schema.org/Recipe
 */
export interface RecipeData {
  "@context"?: "https://schema.org";
  "@type"?: "Recipe";
  name?: string;
  description?: string;
  recipeIngredient?: string[];
  recipeInstructions?: string | string[] | Array<{
    "@type": "HowToStep";
    text: string;
  }>;
  prepTime?: string;
  cookTime?: string;
  totalTime?: string;
  recipeYield?: string;
  recipeCuisine?: string;
  recipeCategory?: string;
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
export type RecipeSortBy = "recently_added" | "alphabetical" | "time_asc" | "time_desc";

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
 */
export type Theme = "garden-fresh" | "bistro" | "dark" | "high-contrast" | "classic" | "professional" | "light";

/**
 * View mode options
 */
export type ViewMode = "grid" | "list";

/**
 * Meal type for meal plans
 */
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";
