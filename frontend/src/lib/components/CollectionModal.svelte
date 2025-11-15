<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Collection } from '$lib/api/collections';

	export let isOpen = false;
	export let collection: Collection | null = null; // null for create, collection for edit

	const dispatch = createEventDispatcher();

	let name = collection?.name || '';
	let description = collection?.description || '';
	let icon = collection?.icon || '';
	let error = '';

	// Update values when collection prop changes
	$: if (collection) {
		name = collection.name;
		description = collection.description || '';
		icon = collection.icon || '';
	}

	const iconOptions = [
		'📚',
		'⭐',
		'❤️',
		'🍕',
		'🍰',
		'🥗',
		'🍜',
		'☕',
		'🍷',
		'🎂',
		'🥘',
		'🌮',
		'🍱',
		'🍲',
		'⚡',
		'🔥',
		'🎉',
		'🌟',
		'💚',
		'🧡'
	];

	function handleSubmit() {
		error = '';

		if (!name.trim()) {
			error = 'Collection name is required';
			return;
		}

		if (name.trim().length > 50) {
			error = 'Collection name must be 50 characters or less';
			return;
		}

		dispatch('submit', {
			name: name.trim(),
			description: description.trim() || undefined,
			icon: icon || undefined
		});

		// Reset form if creating new
		if (!collection) {
			name = '';
			description = '';
			icon = '';
		}
	}

	function handleCancel() {
		dispatch('cancel');
		error = '';

		// Reset form if creating new
		if (!collection) {
			name = '';
			description = '';
			icon = '';
		}
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			handleCancel();
		}
	}
</script>

{#if isOpen}
	<div class="modal-backdrop" on:click={handleBackdropClick} on:keydown={(e) => e.key === 'Escape' && handleCancel()}>
		<div class="modal" role="dialog" aria-modal="true">
			<div class="modal-header">
				<h2 class="modal-title">
					{collection ? 'Edit Collection' : 'Create Collection'}
				</h2>
				<button on:click={handleCancel} class="btn-close" aria-label="Close">×</button>
			</div>

			<form on:submit|preventDefault={handleSubmit}>
				<div class="modal-body">
					{#if error}
						<div class="error-banner">
							{error}
						</div>
					{/if}

					<div class="form-group">
						<label for="collection-name" class="form-label">
							Collection Name <span class="required">*</span>
						</label>
						<input
							type="text"
							id="collection-name"
							bind:value={name}
							placeholder="e.g., Favorite Desserts, Quick Meals"
							class="form-input"
							maxlength="50"
							required
							autofocus
						/>
						<p class="form-help">{name.length}/50 characters</p>
					</div>

					<div class="form-group">
						<label for="collection-desc" class="form-label">Description (Optional)</label>
						<textarea
							id="collection-desc"
							bind:value={description}
							placeholder="Add a description for this collection..."
							rows="3"
							class="form-input"
						/>
					</div>

					<div class="form-group">
						<label class="form-label">Icon (Optional)</label>
						<div class="icon-grid">
							{#each iconOptions as iconOption}
								<button
									type="button"
									class="icon-option"
									class:selected={icon === iconOption}
									on:click={() => (icon = iconOption)}
								>
									{iconOption}
								</button>
							{/each}
						</div>
						{#if icon}
							<button type="button" on:click={() => (icon = '')} class="btn-sm btn-secondary mt-2">
								Clear Icon
							</button>
						{/if}
					</div>
				</div>

				<div class="modal-footer">
					<button type="button" on:click={handleCancel} class="btn btn-secondary">
						Cancel
					</button>
					<button type="submit" class="btn btn-primary">
						{collection ? 'Update' : 'Create'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
		animation: fadeIn 0.2s ease-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.modal {
		background: var(--neutral-white);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-xl);
		width: 100%;
		max-width: 500px;
		max-height: 90vh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		animation: slideUp 0.2s ease-out;
	}

	@keyframes slideUp {
		from {
			transform: translateY(20px);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1.5rem;
		border-bottom: 1px solid var(--neutral-200);
	}

	.modal-title {
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--text-900);
	}

	.btn-close {
		width: 2rem;
		height: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: none;
		border-radius: var(--radius-md);
		color: var(--text-600);
		font-size: 2rem;
		cursor: pointer;
		transition: all var(--transition-fast);
		line-height: 1;
	}

	.btn-close:hover {
		background: var(--neutral-100);
		color: var(--text-900);
	}

	.modal-body {
		padding: 1.5rem;
		overflow-y: auto;
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: 0.75rem;
		padding: 1.5rem;
		border-top: 1px solid var(--neutral-200);
	}

	.form-group {
		margin-bottom: 1.5rem;
	}

	.form-group:last-child {
		margin-bottom: 0;
	}

	.form-label {
		display: block;
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-700);
		margin-bottom: 0.5rem;
	}

	.required {
		color: #EF4444;
	}

	.form-input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 1rem;
		color: var(--text-900);
		background: var(--neutral-white);
		transition: all var(--transition-fast);
	}

	.form-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.form-help {
		font-size: 0.875rem;
		color: var(--text-500);
		margin-top: 0.5rem;
	}

	.error-banner {
		padding: 0.75rem 1rem;
		background: #FEE2E2;
		color: #991B1B;
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		margin-bottom: 1.5rem;
	}

	.icon-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(3rem, 1fr));
		gap: 0.5rem;
	}

	.icon-option {
		width: 3rem;
		height: 3rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-50);
		border: 2px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 1.5rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.icon-option:hover {
		background: var(--accent-50);
		border-color: var(--accent-300);
		transform: scale(1.1);
	}

	.icon-option.selected {
		background: var(--accent-100);
		border-color: var(--accent-500);
		transform: scale(1.05);
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}

	textarea.form-input {
		resize: vertical;
	}
</style>
