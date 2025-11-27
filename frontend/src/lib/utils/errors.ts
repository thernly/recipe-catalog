/**
 * Centralized error handling utility
 */

import { toast } from '$lib/stores/toast';
import { logger } from './logger';

/**
 * Extract error message from unknown error type
 */
export function getErrorMessage(error: unknown): string {
	if (error instanceof Error) {
		return error.message;
	}
	if (typeof error === 'string') {
		return error;
	}
	return 'An unknown error occurred';
}

/**
 * Handle errors consistently across the app
 * Logs the error and shows a toast message to the user
 */
export function handleError(error: unknown, userMessage?: string) {
	logger.error(error);
	const message = userMessage || getErrorMessage(error);
	toast.error(message);
}

/**
 * Handle async operations with consistent error handling
 */
export async function withErrorHandling<T>(
	operation: () => Promise<T>,
	errorMessage?: string
): Promise<T | null> {
	try {
		return await operation();
	} catch (err) {
		handleError(err, errorMessage);
		return null;
	}
}

/**
 * Handle async operations that should show a success message
 */
export async function withSuccessToast<T>(
	operation: () => Promise<T>,
	successMessage: string,
	errorMessage?: string
): Promise<T | null> {
	try {
		const result = await operation();
		toast.success(successMessage);
		return result;
	} catch (err) {
		handleError(err, errorMessage);
		return null;
	}
}
