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

/**
 * Generate a recipe from ingredients using AI
 */
export async function generateRecipe(
	request: AIRecipeGenerateRequest
): Promise<AIRecipeGenerateResponse> {
	return apiRequest<AIRecipeGenerateResponse>('/api/ai/generate-recipe', {
		method: 'POST',
		body: JSON.stringify(request)
	});
}
