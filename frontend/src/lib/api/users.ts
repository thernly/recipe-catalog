/**
 * User API endpoints
 */

import { apiRequest } from './client';

export interface User {
	id: number;
	email: string;
	display_name: string;
	is_active: boolean;
	created_at: string;
	updated_at: string;
}

export interface UserPreferences {
	theme: 'classic' | 'professional';
	default_view: 'grid' | 'list';
	default_sort: string;
	recipes_per_page: number;
	email_notifications: boolean;
	timezone: string;
	custom_cuisines: string[];
	custom_categories: string[];
}

export interface UserStats {
	total_recipes: number;
	total_collections: number;
	recipes_imported: number;
	recipes_manual: number;
	recipes_this_month: number;
}

export interface UserUpdate {
	email?: string;
	display_name?: string;
}

export interface PasswordChange {
	current_password: string;
	new_password: string;
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<User> {
	return apiRequest<User>('/api/users/me');
}

/**
 * Update current user profile
 */
export async function updateProfile(data: UserUpdate): Promise<User> {
	return apiRequest<User>('/api/users/me', {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

/**
 * Change password
 */
export async function changePassword(data: PasswordChange): Promise<void> {
	return apiRequest<void>('/api/users/me/change-password', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

/**
 * Get user preferences
 */
export async function getPreferences(): Promise<UserPreferences> {
	return apiRequest<UserPreferences>('/api/users/me/preferences');
}

/**
 * Update user preferences (partial update supported)
 */
export async function updatePreferences(data: Partial<UserPreferences>): Promise<UserPreferences> {
	return apiRequest<UserPreferences>('/api/users/me/preferences', {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

/**
 * Get user statistics
 */
export async function getUserStats(): Promise<UserStats> {
	return apiRequest<UserStats>('/api/users/me/stats');
}

/**
 * Delete current user account
 */
export async function deleteAccount(): Promise<void> {
	return apiRequest<void>('/api/users/me', {
		method: 'DELETE'
	});
}
