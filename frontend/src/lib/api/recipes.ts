/**
 * Recipe API endpoints
 */

import { apiRequest, buildQueryString } from './client';

export interface Recipe {
	id: number;
	user_id: number;
	name: string;
	description?: string;
	image_url?: string;
	recipe_data: any;
	source_url?: string;
	source_type: 'imported' | 'manual';
	is_modified: boolean;
	created_at: string;
	updated_at: string;
	imported_at?: string;
	deleted_at?: string;
	cuisine?: string;
	category?: string;
	total_time_minutes?: number;
}

export interface RecipeSummary {
	id: number;
	name: string;
	description?: string;
	image_url?: string;
	cuisine?: string;
	category?: string;
	total_time_minutes?: number;
	source_type: 'imported' | 'manual';
	created_at: string;
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
	sort_by?: 'recently_added' | 'alphabetical' | 'time_asc' | 'time_desc';
	page?: number;
	per_page?: number;
}

export interface RecipeCreate {
	name: string;
	description?: string;
	image_url?: string;
	recipe_data: any;
	source_url?: string;
	source_type?: 'imported' | 'manual';
	cuisine?: string;
	category?: string;
	total_time_minutes?: number;
	collection_ids?: number[];
}

export interface RecipeUpdate {
	name?: string;
	description?: string;
	image_url?: string;
	recipe_data?: any;
	cuisine?: string;
	category?: string;
	total_time_minutes?: number;
	collection_ids?: number[];
}

/**
 * Search and filter recipes
 */
export async function searchRecipes(params: RecipeSearchParams = {}): Promise<RecipeSearchResult> {
	const queryString = buildQueryString(params);
	return apiRequest<RecipeSearchResult>(`/api/recipes/search${queryString}`);
}

/**
 * Get a single recipe by ID
 */
export async function getRecipe(id: number): Promise<Recipe> {
	return apiRequest<Recipe>(`/api/recipes/${id}`);
}

/**
 * Create a new recipe
 */
export async function createRecipe(data: RecipeCreate): Promise<Recipe> {
	return apiRequest<Recipe>('/api/recipes/', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

/**
 * Update an existing recipe
 */
export async function updateRecipe(id: number, data: RecipeUpdate): Promise<Recipe> {
	return apiRequest<Recipe>(`/api/recipes/${id}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

/**
 * Delete a recipe (soft delete by default)
 */
export async function deleteRecipe(id: number, permanent: boolean = false): Promise<void> {
	const queryString = permanent ? '?permanent=true' : '';
	return apiRequest<void>(`/api/recipes/${id}${queryString}`, {
		method: 'DELETE'
	});
}

/**
 * Restore a soft-deleted recipe
 */
export async function restoreRecipe(id: number): Promise<Recipe> {
	return apiRequest<Recipe>(`/api/recipes/${id}/restore`, {
		method: 'POST'
	});
}

/**
 * Duplicate a recipe
 */
export async function duplicateRecipe(id: number): Promise<Recipe> {
	return apiRequest<Recipe>(`/api/recipes/${id}/duplicate`, {
		method: 'POST'
	});
}

/**
 * Get trashed recipes
 */
export async function getTrashedRecipes(): Promise<RecipeSummary[]> {
	return apiRequest<RecipeSummary[]>('/api/recipes/trash/list');
}
