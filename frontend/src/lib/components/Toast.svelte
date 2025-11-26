<script lang="ts">
	import { toasts } from '$lib/stores/toast';
	import { fade, fly } from 'svelte/transition';

	function getIcon(type: string) {
		switch (type) {
			case 'success':
				return '✓';
			case 'error':
				return '✕';
			case 'warning':
				return '⚠';
			case 'info':
			default:
				return 'ℹ';
		}
	}

	function getColors(type: string) {
		switch (type) {
			case 'success':
				return 'bg-green-600 text-white';
			case 'error':
				return 'bg-red-600 text-white';
			case 'warning':
				return 'bg-yellow-600 text-white';
			case 'info':
			default:
				return 'bg-blue-600 text-white';
		}
	}
</script>

<div class="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md">
	{#each $toasts as toast (toast.id)}
		<div
			transition:fly={{ y: -20, duration: 300 }}
			class="rounded-lg shadow-lg px-4 py-3 flex items-center gap-3 {getColors(toast.type)}"
		>
			<span class="text-xl font-bold" aria-hidden="true">
				{getIcon(toast.type)}
			</span>
			<p class="flex-1">{toast.message}</p>
			<button
				type="button"
				on:click={() => toasts.remove(toast.id)}
				class="ml-2 hover:opacity-80 transition-opacity"
				aria-label="Close notification"
			>
				✕
			</button>
		</div>
	{/each}
</div>
