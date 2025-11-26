import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastItem {
	id: number;
	type: ToastType;
	message: string;
}

const TOAST_DURATION = 5000; // 5 seconds

function createToastStore() {
	const { subscribe, update } = writable<ToastItem[]>([]);
	let nextId = 0;

	function addToast(type: ToastType, message: string) {
		const id = nextId++;
		update(toasts => [...toasts, { id, type, message }]);

		// Auto-dismiss after duration
		setTimeout(() => {
			update(toasts => toasts.filter(t => t.id !== id));
		}, TOAST_DURATION);
	}

	return {
		subscribe,
		success: (message: string) => addToast('success', message),
		error: (message: string) => addToast('error', message),
		info: (message: string) => addToast('info', message),
		warning: (message: string) => addToast('warning', message),
		remove: (id: number) => {
			update(toasts => toasts.filter(t => t.id !== id));
		}
	};
}

export const toast = createToastStore();
export const toasts = toast;
