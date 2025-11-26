import { writable } from 'svelte/store';

interface DialogState {
	open: boolean;
	title: string;
	message: string;
	onConfirm: () => void;
}

const dialogStore = writable<DialogState>({
	open: false,
	title: '',
	message: '',
	onConfirm: () => {}
});

export const dialog = {
	subscribe: dialogStore.subscribe,
	show: (options: { title: string; message: string; onConfirm: () => void }) => {
		dialogStore.set({
			open: true,
			title: options.title,
			message: options.message,
			onConfirm: options.onConfirm
		});
	},
	close: () => {
		dialogStore.update(state => ({ ...state, open: false }));
	}
};
