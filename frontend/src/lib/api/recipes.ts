/**
 * Recipe API endpoints
 */

import { apiRequest, buildQueryString } from "./client";
import type {
  RecipeData,
  RecipeSortBy,
  RecipeSourceType,
} from "#lib/types/index.js";

export interface Recipe {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  image_url?: string;
  recipe_data: RecipeData;
  source_url?: string;
  source_type: RecipeSourceType;
  is_modified: boolean;
  created_at: string;
  updated_at: string;
  imported_at?: string;
  deleted_at?: string;
  cuisine?: string;
  category?: string;
  total_time_minutes?: number;
  creator_display_name?: string | null;
  rating?: number | null;
  last_cooked_on?: string | null;
}

/** Shared by the household: a 1-5 rating and the day last cooked (YYYY-MM-DD). */
export interface RecipeCooking {
  rating: number | null;
  last_cooked_on: string | null;
}

export interface RecipeSummary {
  id: number;
  /** Who added it; only they can edit or delete it. */
  user_id?: number;
  name: string;
  description?: string;
  image_url?: string;
  recipe_data?: RecipeData;
  cuisine?: string;
  category?: string;
  total_time_minutes?: number;
  source_type: RecipeSourceType;
  created_at: string;
  creator_display_name?: string | null;
  deleted_at?: string;
  rating?: number | null;
  last_cooked_on?: string | null;
}

export interface RecipeSearchResult {
  recipes: RecipeSummary[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface RecipeSearchParams {
  query?: string;
  cuisine?: string[];
  category?: string[];
  source_type?: string[];
  collection_ids?: number[];
  max_time_minutes?: number;
  min_time_minutes?: number;
  sort_by?: RecipeSortBy;
  /** With sort_by "random": which shuffle. Keep one seed while paging. */
  seed?: number;
  page?: number;
  per_page?: number;
}

export interface RecipeCreate {
  name: string;
  description?: string;
  image_url?: string;
  recipe_data: RecipeData;
  source_url?: string;
  source_type?: RecipeSourceType;
  cuisine?: string;
  category?: string;
  total_time_minutes?: number;
  collection_ids?: number[];
}

export interface RecipeUpdate {
  name?: string;
  description?: string;
  image_url?: string;
  recipe_data?: RecipeData;
  cuisine?: string;
  category?: string;
  total_time_minutes?: number;
  collection_ids?: number[];
}

/**
 * Search and filter recipes
 */
export async function searchRecipes(
  params: RecipeSearchParams = {},
): Promise<RecipeSearchResult> {
  const queryString = buildQueryString(params);
  return apiRequest<RecipeSearchResult>(`/recipes/search${queryString}`);
}

/**
 * Get a single recipe by ID
 */
export async function getRecipe(id: number): Promise<Recipe> {
  return apiRequest<Recipe>(`/recipes/${id}`);
}

/**
 * Create a new recipe
 */
export async function createRecipe(data: RecipeCreate): Promise<Recipe> {
  return apiRequest<Recipe>("/recipes/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update an existing recipe
 */
export async function updateRecipe(
  id: number,
  data: RecipeUpdate,
): Promise<Recipe> {
  return apiRequest<Recipe>(`/recipes/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a recipe (soft delete by default)
 */
export async function deleteRecipe(
  id: number,
  permanent: boolean = false,
): Promise<void> {
  const queryString = permanent ? "?permanent=true" : "";
  return apiRequest<void>(`/recipes/${id}${queryString}`, {
    method: "DELETE",
  });
}

/**
 * Restore a soft-deleted recipe
 */
export async function restoreRecipe(id: number): Promise<Recipe> {
  return apiRequest<Recipe>(`/recipes/${id}/restore`, {
    method: "POST",
  });
}

/**
 * Duplicate a recipe
 */
export async function duplicateRecipe(id: number): Promise<Recipe> {
  return apiRequest<Recipe>(`/recipes/${id}/duplicate`, {
    method: "POST",
  });
}

/**
 * Set or clear a recipe's rating and/or last-cooked date. Any household member
 * may; a field left out is not changed.
 */
export async function updateCooking(
  id: number,
  data: Partial<RecipeCooking>,
): Promise<RecipeCooking> {
  return apiRequest<RecipeCooking>(`/recipes/${id}/cooking`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Get trashed recipes
 */
export async function getTrashedRecipes(): Promise<RecipeSummary[]> {
  return apiRequest<RecipeSummary[]>("/recipes/trash/list");
}

export interface ImportResult {
  success: boolean;
  message: string;
  details: {
    total: number;
    created: number;
    updated: number;
    skipped: number;
    failed: number;
    errors: unknown[];
    items: unknown[];
  };
}

/**
 * Import recipes from JSON file
 */
export async function importRecipes(
  file: File,
  duplicateHandling: "skip" | "update" | "create" = "skip",
  collectionId?: number,
): Promise<ImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("duplicate_handling", duplicateHandling);
  if (collectionId) {
    formData.append("collection_id", collectionId.toString());
  }

  return apiRequest<ImportResult>("/import/recipes", {
    method: "POST",
    body: formData,
    headers: {}, // Let browser set Content-Type for FormData
  });
}

export interface UrlImportResult {
  status: "created" | "skipped";
  id: number;
  message: string;
}

/**
 * Save the recipe on a web page. The server fetches the page and reads its recipe.
 */
export async function importRecipeFromUrl(
  url: string,
): Promise<UrlImportResult> {
  return apiRequest<UrlImportResult>("/import/url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

/** Counts of what a restore added beyond recipes; null for a recipes-only restore. */
export interface RestoredCounts {
  collections: number;
  collection_recipes: number;
  meal_plans: number;
  planned_meals: number;
  planned_meals_skipped: number;
  shopping_lists: number;
  shopping_lists_skipped: number;
}

export interface RestoreResult extends ImportResult {
  restored: RestoredCounts | null;
}

/**
 * Restore a Complete Backup file. Only adds what is missing.
 */
export async function restoreBackup(
  file: File,
  scope: "everything" | "recipes",
): Promise<RestoreResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("scope", scope);

  return apiRequest<RestoreResult>("/import/backup", {
    method: "POST",
    body: formData,
    headers: {}, // Let browser set Content-Type for FormData
  });
}

/**
 * Export a single recipe
 */
export async function exportRecipe(
  id: number,
  format: "json" | "markdown" | "text" | "pdf",
): Promise<Blob> {
  return apiRequest<Blob>(`/recipes/${id}/export?format=${format}`, {
    responseType: "blob",
  });
}
