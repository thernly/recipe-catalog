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

<dialog bind:this={dialogElement} on:keydown={handleKeydown} class="confirm-dialog">
	<div class="dialog-content">
		<h2 class="dialog-title">
			{title}
		</h2>
		<p class="dialog-message">
			{message}
		</p>
		<div class="dialog-actions">
			<button type="button" on:click={handleCancel} class="btn-cancel">
				Cancel
			</button>
			<button type="button" on:click={handleConfirm} class="btn-confirm">
				Confirm
			</button>
		</div>
	</div>
</dialog>

<style>
	.confirm-dialog {
		max-width: 28rem;
		width: 100%;
		padding: 0;
		border: 1px solid var(--neutral-300);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-xl);
		background: var(--neutral-white);
	}

	.confirm-dialog::backdrop {
		background: rgba(0, 0, 0, 0.5);
	}

	.dialog-content {
		padding: 1.5rem;
	}

	.dialog-title {
		font-size: 1.25rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
		color: var(--text-900);
	}

	.dialog-message {
		color: var(--text-900);
		margin-bottom: 1.5rem;
		line-height: 1.5;
	}

	.dialog-actions {
		display: flex;
		gap: 0.75rem;
		justify-content: flex-end;
	}

	.btn-cancel {
		padding: 0.5rem 1rem;
		border-radius: var(--radius-md);
		background: var(--neutral-100);
		color: var(--text-900);
		font-weight: 500;
		border: 1px solid var(--neutral-300);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-cancel:hover {
		background: var(--neutral-200);
		border-color: var(--neutral-400);
	}

	.btn-confirm {
		padding: 0.5rem 1rem;
		border-radius: var(--radius-md);
		background: #EF4444;
		color: #FFFFFF;
		font-weight: 500;
		border: none;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-confirm:hover {
		background: #DC2626;
	}
</style>
