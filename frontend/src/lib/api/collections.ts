/**
 * Collections API endpoints
 */

import { apiRequest } from './client';

export interface Collection {
	id: number;
	user_id: number;
	name: string;
	description?: string;
	is_default: boolean;
	icon?: string;
	created_at: string;
	updated_at: string;
	creator_display_name?: string | null;
}

export interface CollectionWithCount extends Collection {
	recipe_count: number;
}

export interface CollectionCreate {
	name: string;
	description?: string;
	icon?: string;
}

export interface CollectionUpdate {
	name?: string;
	description?: string;
	icon?: string;
}

/**
 * Get all collections for the current user
 */
export async function getCollections(): Promise<CollectionWithCount[]> {
	return apiRequest<CollectionWithCount[]>('/api/collections/');
}

/**
 * Get a single collection by ID
 */
export async function getCollection(id: number): Promise<CollectionWithCount> {
	return apiRequest<CollectionWithCount>(`/api/collections/${id}`);
}

/**
 * Create a new collection
 */
export async function createCollection(data: CollectionCreate): Promise<Collection> {
	return apiRequest<Collection>('/api/collections/', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

/**
 * Update a collection
 */
export async function updateCollection(id: number, data: CollectionUpdate): Promise<Collection> {
	return apiRequest<Collection>(`/api/collections/${id}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

/**
 * Delete a collection
 */
export async function deleteCollection(id: number): Promise<void> {
	return apiRequest<void>(`/api/collections/${id}`, {
		method: 'DELETE'
	});
}

/**
 * Add recipes to a collection
 */
export async function addRecipesToCollection(
	collectionId: number,
	recipeIds: number[]
): Promise<void> {
	return apiRequest<void>(`/api/collections/${collectionId}/recipes`, {
		method: 'POST',
		body: JSON.stringify({ recipe_ids: recipeIds })
	});
}

/**
 * Remove recipes from a collection
 */
export async function removeRecipesFromCollection(
	collectionId: number,
	recipeIds: number[]
): Promise<void> {
	return apiRequest<void>(`/api/collections/${collectionId}/recipes`, {
		method: 'DELETE',
		body: JSON.stringify({ recipe_ids: recipeIds })
	});
}

/**
 * Get recipes in a collection
 */
export async function getCollectionRecipes(collectionId: number): Promise<any[]> {
	return apiRequest<any[]>(`/api/collections/${collectionId}/recipes`);
}

/**
 * Export a collection as PDF
 */
export async function exportCollectionPdf(collectionId: number): Promise<Blob> {
	const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
	
	const response = await fetch(`${API_URL}/api/collections/${collectionId}/export/pdf`, {
		credentials: 'include' // Send cookies for authentication
	});

	if (!response.ok) {
		const errorText = await response.text();
		throw new Error(`Export failed: ${response.statusText}${errorText ? ` - ${errorText}` : ''}`);
	}

	return response.blob();
}
