<script lang="ts">
	import { onMount } from 'svelte';

	export let open = false;
	export let title = '';
	export let message = '';
	export let onConfirm: () => void = () => {};
	export let onCancel: () => void = () => {};

	let dialogElement: HTMLDialogElement;

	$: if (dialogElement) {
		if (open) {
			dialogElement.showModal();
		} else {
			dialogElement.close();
		}
	}

	function handleConfirm() {
		onConfirm();
		onCancel(); // Also close the dialog
	}

	function handleCancel() {
		onCancel();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			handleCancel();
		}
	}

	onMount(() => {
		if (open) {
			dialogElement.showModal();
		}
	});
</script>

<dialog
	bind:this={dialogElement}
	on:keydown={handleKeydown}
	class="rounded-lg shadow-xl border border-gray-300 dark:border-gray-700 p-0 backdrop:bg-black backdrop:bg-opacity-50 max-w-md w-full"
>
	<div class="p-6">
		<h2 class="text-xl font-semibold mb-3 text-gray-900 dark:text-gray-100">
			{title}
		</h2>
		<p class="text-gray-700 dark:text-gray-300 mb-6">
			{message}
		</p>
		<div class="flex gap-3 justify-end">
			<button
				type="button"
				on:click={handleCancel}
				class="px-4 py-2 rounded-md bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 font-medium transition-colors"
			>
				Cancel
			</button>
			<button
				type="button"
				on:click={handleConfirm}
				class="px-4 py-2 rounded-md bg-red-600 hover:bg-red-700 text-white font-medium transition-colors"
			>
				Confirm
			</button>
		</div>
	</div>
</dialog>

<style>
	dialog::backdrop {
		background: rgba(0, 0, 0, 0.5);
	}
</style>
