/**
 * Shopping Lists API endpoints
 */

import { apiRequest } from './client';

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
	status: 'active' | 'archived';
	created_by_user_id: number;
	created_at: string;
	updated_at: string;
	items: ShoppingListItem[];
}

export interface ShoppingListSummary {
	id: number;
	household_id: number;
	name: string;
	description?: string;
	status: 'active' | 'archived';
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
	status?: 'active' | 'archived';
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
}

export interface GenerateFromMealPlanRequest {
	meal_plan_id: number;
	list_name?: string;
	selected_meal_ids?: number[];
}

/**
 * Get default shopping list categories
 */
export async function getCategories(): Promise<string[]> {
	const response = await apiRequest<{ categories: string[] }>('/api/shopping-lists/categories');
	return response.categories;
}

/**
 * Create a new shopping list
 */
export async function createShoppingList(data: ShoppingListCreate): Promise<ShoppingList> {
	return apiRequest<ShoppingList>('/api/shopping-lists/', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

/**
 * List all shopping lists (optionally filtered by status)
 */
export async function listShoppingLists(
	statusFilter?: 'active' | 'archived'
): Promise<ShoppingListSummary[]> {
	const url = statusFilter
		? `/api/shopping-lists/?status_filter=${statusFilter}`
		: '/api/shopping-lists/';
	return apiRequest<ShoppingListSummary[]>(url);
}

/**
 * Get a specific shopping list with all items
 */
export async function getShoppingList(id: number): Promise<ShoppingList> {
	return apiRequest<ShoppingList>(`/api/shopping-lists/${id}`);
}

/**
 * Update a shopping list
 */
export async function updateShoppingList(
	id: number,
	data: ShoppingListUpdate
): Promise<ShoppingList> {
	return apiRequest<ShoppingList>(`/api/shopping-lists/${id}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

/**
 * Delete a shopping list
 */
export async function deleteShoppingList(id: number): Promise<void> {
	return apiRequest<void>(`/api/shopping-lists/${id}`, {
		method: 'DELETE'
	});
}

/**
 * Archive a shopping list
 */
export async function archiveShoppingList(id: number): Promise<ShoppingList> {
	return apiRequest<ShoppingList>(`/api/shopping-lists/${id}/archive`, {
		method: 'POST'
	});
}

/**
 * Duplicate a shopping list
 */
export async function duplicateShoppingList(id: number): Promise<ShoppingList> {
	return apiRequest<ShoppingList>(`/api/shopping-lists/${id}/duplicate`, {
		method: 'POST'
	});
}

/**
 * Add an item to a shopping list
 */
export async function addShoppingListItem(
	listId: number,
	data: ShoppingListItemCreate
): Promise<ShoppingListItem> {
	return apiRequest<ShoppingListItem>(`/api/shopping-lists/${listId}/items`, {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

/**
 * Update a shopping list item
 */
export async function updateShoppingListItem(
	itemId: number,
	data: ShoppingListItemUpdate
): Promise<ShoppingListItem> {
	return apiRequest<ShoppingListItem>(`/api/shopping-lists/items/${itemId}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

/**
 * Delete a shopping list item
 */
export async function deleteShoppingListItem(itemId: number): Promise<void> {
	return apiRequest<void>(`/api/shopping-lists/items/${itemId}`, {
		method: 'DELETE'
	});
}

/**
 * Generate a shopping list from a recipe
 */
export async function generateFromRecipe(
	data: GenerateFromRecipeRequest
): Promise<ShoppingList> {
	return apiRequest<ShoppingList>('/api/shopping-lists/from-recipe', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

/**
 * Generate a shopping list from a meal plan
 */
export async function generateFromMealPlan(
	data: GenerateFromMealPlanRequest
): Promise<ShoppingList> {
	return apiRequest<ShoppingList>('/api/shopping-lists/from-meal-plan', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}
