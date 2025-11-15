<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let ingredients: string[] = [''];
	export let error: string = '';

	const dispatch = createEventDispatcher();

	function addIngredient() {
		ingredients = [...ingredients, ''];
		dispatch('change', ingredients);
	}

	function removeIngredient(index: number) {
		ingredients = ingredients.filter((_, i) => i !== index);
		dispatch('change', ingredients);
	}

	function handleInput() {
		dispatch('change', ingredients);
	}
</script>

<section class="form-section">
	<h2 class="section-title required">Ingredients</h2>

	{#if error}
		<p class="error-message mb-4">{error}</p>
	{/if}

	<div class="dynamic-list">
		{#each ingredients as ingredient, index}
			<div class="dynamic-list-item">
				<span class="item-number">{index + 1}</span>
				<input
					type="text"
					bind:value={ingredients[index]}
					on:input={handleInput}
					placeholder="e.g., 2 cups all-purpose flour"
					class="form-input flex-1"
				/>
				<button
					type="button"
					on:click={() => removeIngredient(index)}
					class="btn-remove"
					title="Remove"
				>
					×
				</button>
			</div>
		{/each}
	</div>

	<button type="button" on:click={addIngredient} class="btn btn-secondary btn-sm mt-3">
		+ Add Ingredient
	</button>
</section>

<style>
	.form-section {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 2rem;
		margin-bottom: 2rem;
	}

	.section-title {
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--text-900);
		margin-bottom: 1.5rem;
	}

	.section-title.required::after {
		content: '*';
		color: #ef4444;
		margin-left: 0.25rem;
	}

	.error-message {
		font-size: 0.875rem;
		color: #ef4444;
		margin-top: 0.5rem;
	}

	.mb-4 {
		margin-bottom: 1rem;
	}

	.dynamic-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.dynamic-list-item {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.item-number {
		flex-shrink: 0;
		width: 2rem;
		height: 2.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-100);
		color: var(--text-600);
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		font-weight: 500;
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

	.flex-1 {
		flex: 1;
	}

	.btn-remove {
		flex-shrink: 0;
		width: 2.5rem;
		height: 2.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		color: var(--text-600);
		font-size: 1.5rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-remove:hover {
		background: #fee2e2;
		border-color: #ef4444;
		color: #ef4444;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}

	.mt-3 {
		margin-top: 0.75rem;
	}
</style>
