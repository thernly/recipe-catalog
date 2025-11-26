/**
 * AI API endpoints
 */

import { apiRequest } from './client';

export interface AIRecipeGenerateRequest {
	ingredients: string[];
	cuisine?: string;
	time_limit?: number;
	dietary_preferences?: string[];
	equipment?: string[];
}

export interface AIRecipeGenerateResponse {
	recipe: any;
	source_type: string;
}

export interface AIMenuGenerateRequest {
	days: number;
	meals_per_day: string[];
	dietary_preferences?: string[];
	cuisine?: string;
	mode: 'catalog-first' | 'ai-only';
	household_recipe_ids?: number[];
}

export interface MealSuggestion {
	day: number;
	meal_type: string;
	recipe_id: number | null;
	recipe_name: string;
	description?: string;
	prep_time?: string;
	cook_time?: string;
}

export interface AIMenuGenerateResponse {
	suggestions: MealSuggestion[];
	mode: string;
}

/**
 * Generate a recipe from ingredients using AI
 */
export async function generateRecipe(
	request: AIRecipeGenerateRequest
): Promise<AIRecipeGenerateResponse> {
	return apiRequest<AIRecipeGenerateResponse>('/ai/generate-recipe', {
		method: 'POST',
		body: JSON.stringify(request)
	});
}

/**
 * Generate menu suggestions for multiple days using AI
 */
export async function generateMenu(
	request: AIMenuGenerateRequest
): Promise<AIMenuGenerateResponse> {
	return apiRequest<AIMenuGenerateResponse>('/ai/generate-menu', {
		method: 'POST',
		body: JSON.stringify(request)
	});
}
