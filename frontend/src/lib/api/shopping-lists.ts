/**
 * Shopping Lists API endpoints
 */

import { apiRequest } from "./client";

export interface ShoppingListItem {
  id: number;
  list_id: number;
  item_name: string;
  quantity?: string;
  unit?: string;
  category?: string;
  notes?: string;
  checked: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ShoppingList {
  id: number;
  household_id: number;
  name: string;
  description?: string;
  status: "active" | "archived";
  created_by_user_id: number;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
  items: ShoppingListItem[];
}

export interface ShoppingListSummary {
  id: number;
  household_id: number;
  name: string;
  description?: string;
  status: "active" | "archived";
  created_by_user_id: number;
  created_by_name?: string | null;
  created_at: string;
  item_count: number;
  checked_count: number;
}

export interface ShoppingListCreate {
  name: string;
  description?: string;
}

export interface ShoppingListUpdate {
  name?: string;
  description?: string;
  status?: "active" | "archived";
}

export interface ShoppingListItemCreate {
  item_name: string;
  quantity?: string;
  unit?: string;
  category?: string;
  notes?: string;
}

export interface ShoppingListItemUpdate {
  item_name?: string;
  quantity?: string;
  unit?: string;
  category?: string;
  notes?: string;
  checked?: boolean;
  display_order?: number;
}

export interface GenerateFromRecipeRequest {
  recipe_id: number;
  list_name?: string;
  servings?: number;
  /** Add to this existing list (merging duplicates) instead of creating one */
  shopping_list_id?: number;
  /** Add only this recipeIngredient line */
  ingredient_index?: number;
}

export interface GenerateFromMealPlanRequest {
  meal_plan_id: number;
  list_name?: string;
  selected_meal_ids?: number[];
  shopping_list_id?: number;
}

const LAST_LIST_KEY = "lastShoppingListId";

/** The list last added to in this browser session, for one-click adds. */
export function getLastShoppingListId(): number | null {
  try {
    return Number(sessionStorage.getItem(LAST_LIST_KEY)) || null;
  } catch {
    return null;
  }
}

export function setLastShoppingListId(id: number | null): void {
  try {
    if (id) sessionStorage.setItem(LAST_LIST_KEY, String(id));
    else sessionStorage.removeItem(LAST_LIST_KEY);
  } catch {
    // storage unavailable: one-click adds just fall back to the picker
  }
}

/** "Created by you" for the current user, else the creator's name. */
export function createdByLabel(
  list: { created_by_user_id: number; created_by_name?: string | null },
  currentUserId: number | undefined,
): string {
  if (list.created_by_user_id === currentUserId) return "Created by you";
  return `Created by ${list.created_by_name || "a household member"}`;
}

/** "2 cup flour" -> "2 cups flour": units are stored singular. */
export function formatQuantityUnit(
  quantity?: string | null,
  unit?: string | null,
): string {
  if (!unit) return quantity ?? "";
  const plural =
    quantity && quantity.trim() !== "1" && !/^\d+\/\d+$/.test(quantity.trim());
  let shown = unit;
  if (plural && !unit.endsWith("s")) {
    shown = /(ch|sh|x)$/.test(unit) ? `${unit}es` : `${unit}s`;
  }
  return quantity ? `${quantity} ${shown}` : shown;
}

/**
 * One group per store category, in the order of `categories` (the shop's
 * sections); an item with no category goes under "Other". Items keep their
 * order inside a group.
 */
export function groupByCategory(
  items: ShoppingListItem[],
  categories: string[],
): { category: string; items: ShoppingListItem[] }[] {
  const groups: Record<string, ShoppingListItem[]> = {};
  for (const item of items)
    (groups[item.category || "Other"] ??= []).push(item);
  const rank = (category: string) => {
    const index = categories.indexOf(category);
    return index === -1 ? categories.length : index;
  };
  return Object.entries(groups)
    .sort(([a], [b]) => rank(a) - rank(b) || a.localeCompare(b))
    .map(([category, items]) => ({ category, items }));
}

/**
 * Get default shopping list categories
 */
export async function getCategories(): Promise<string[]> {
  const response = await apiRequest<{ categories: string[] }>(
    "/shopping-lists/categories",
  );
  return response.categories;
}

/**
 * Create a new shopping list
 */
export async function createShoppingList(
  data: ShoppingListCreate,
): Promise<ShoppingList> {
  return apiRequest<ShoppingList>("/shopping-lists/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * List all shopping lists (optionally filtered by status)
 */
export async function listShoppingLists(
  statusFilter?: "active" | "archived",
): Promise<ShoppingListSummary[]> {
  const url = statusFilter
    ? `/shopping-lists/?status_filter=${statusFilter}`
    : "/shopping-lists/";
  return apiRequest<ShoppingListSummary[]>(url);
}

/**
 * Get a specific shopping list with all items
 */
export async function getShoppingList(id: number): Promise<ShoppingList> {
  return apiRequest<ShoppingList>(`/shopping-lists/${id}`);
}

/**
 * Update a shopping list
 */
export async function updateShoppingList(
  id: number,
  data: ShoppingListUpdate,
): Promise<ShoppingList> {
  return apiRequest<ShoppingList>(`/shopping-lists/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a shopping list
 */
export async function deleteShoppingList(id: number): Promise<void> {
  return apiRequest<void>(`/shopping-lists/${id}`, {
    method: "DELETE",
  });
}

/**
 * Archive a shopping list
 */
export async function archiveShoppingList(id: number): Promise<ShoppingList> {
  return apiRequest<ShoppingList>(`/shopping-lists/${id}/archive`, {
    method: "POST",
  });
}

/**
 * Duplicate a shopping list
 */
export async function duplicateShoppingList(id: number): Promise<ShoppingList> {
  return apiRequest<ShoppingList>(`/shopping-lists/${id}/duplicate`, {
    method: "POST",
  });
}

/**
 * Add an item to a shopping list
 */
export async function addShoppingListItem(
  listId: number,
  data: ShoppingListItemCreate,
): Promise<ShoppingListItem> {
  return apiRequest<ShoppingListItem>(`/shopping-lists/${listId}/items`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a shopping list item
 */
export async function updateShoppingListItem(
  itemId: number,
  data: ShoppingListItemUpdate,
): Promise<ShoppingListItem> {
  return apiRequest<ShoppingListItem>(`/shopping-lists/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a shopping list item
 */
export async function deleteShoppingListItem(itemId: number): Promise<void> {
  return apiRequest<void>(`/shopping-lists/items/${itemId}`, {
    method: "DELETE",
  });
}

/**
 * Generate a shopping list from a recipe
 */
export async function generateFromRecipe(
  data: GenerateFromRecipeRequest,
): Promise<ShoppingList> {
  return apiRequest<ShoppingList>("/shopping-lists/from-recipe", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Generate a shopping list from a meal plan
 */
export async function generateFromMealPlan(
  data: GenerateFromMealPlanRequest,
): Promise<ShoppingList> {
  return apiRequest<ShoppingList>("/shopping-lists/from-meal-plan", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
