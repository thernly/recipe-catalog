/**
 * Meal Planning API endpoints
 */

import { apiRequest, buildQueryString } from './client';

export interface PlannedMeal {
	id: number;
	meal_plan_id: number;
	recipe_id: number;
	recipe_name?: string;
	day_of_week: number; // 0=Monday, 6=Sunday
	meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'other';
	servings?: number;
	notes?: string;
	created_at: string;
	updated_at: string;
}

export interface MealPlan {
	id: number;
	household_id: number;
	week_start_date: string; // ISO date string
	created_by_user_id: number;
	created_at: string;
	updated_at: string;
	planned_meals: PlannedMeal[];
}

export interface MealPlanSummary {
	id: number;
	household_id: number;
	week_start_date: string;
	created_at: string;
	meal_count: number;
}

export interface PlannedMealCreate {
	recipe_id: number;
	day_of_week: number;
	meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'other';
	servings?: number;
	notes?: string;
}

export interface PlannedMealUpdate {
	recipe_id?: number;
	day_of_week?: number;
	meal_type?: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'other';
	servings?: number;
	notes?: string;
}

/**
 * Get all meal plans for the household
 */
export async function listMealPlans(): Promise<MealPlanSummary[]> {
	return apiRequest<MealPlanSummary[]>('/meal-plans/');
}

/**
 * Get or create meal plan for current week
 */
export async function getCurrentWeekMealPlan(weekStart?: string): Promise<MealPlan> {
	const queryString = weekStart ? `?week_start=${weekStart}` : '';
	return apiRequest<MealPlan>(`/meal-plans/current${queryString}`);
}

/**
 * Get a specific meal plan by ID
 */
export async function getMealPlan(id: number): Promise<MealPlan> {
	return apiRequest<MealPlan>(`/meal-plans/${id}`);
}

/**
 * Delete a meal plan
 */
export async function deleteMealPlan(id: number): Promise<void> {
	return apiRequest<void>(`/meal-plans/${id}`, {
		method: 'DELETE'
	});
}

/**
 * Add a planned meal to a meal plan
 */
export async function addPlannedMeal(
	mealPlanId: number,
	data: PlannedMealCreate
): Promise<PlannedMeal> {
	return apiRequest<PlannedMeal>(`/meal-plans/${mealPlanId}/meals`, {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

/**
 * Update a planned meal
 */
export async function updatePlannedMeal(
	plannedMealId: number,
	data: PlannedMealUpdate
): Promise<PlannedMeal> {
	return apiRequest<PlannedMeal>(`/meal-plans/${plannedMealId}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

/**
 * Delete a planned meal
 */
export async function deletePlannedMeal(plannedMealId: number): Promise<void> {
	return apiRequest<void>(`/meal-plans/meals/${plannedMealId}`, {
		method: 'DELETE'
	});
}

/**
 * Get the Monday of the week containing the given date
 */
export function getWeekStart(date: Date = new Date()): Date {
	const d = new Date(date);
	const day = d.getDay();
	const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust for Sunday
	return new Date(d.setDate(diff));
}

/**
 * Format date as ISO date string (YYYY-MM-DD)
 */
export function formatDateISO(date: Date): string {
	return date.toISOString().split('T')[0];
}

/**
 * Get week dates (Monday to Sunday)
 */
export function getWeekDates(weekStart: Date): Date[] {
	const dates: Date[] = [];
	for (let i = 0; i < 7; i++) {
		const date = new Date(weekStart);
		date.setDate(weekStart.getDate() + i);
		dates.push(date);
	}
	return dates;
}
