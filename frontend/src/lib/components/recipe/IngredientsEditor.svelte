<script lang="ts">
	import { createEventDispatcher, tick } from 'svelte';

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

	function moveIngredient(index: number, by: -1 | 1) {
		const moved = [...ingredients];
		[moved[index], moved[index + by]] = [moved[index + by], moved[index]];
		ingredients = moved;
		dispatch('change', ingredients);
	}

	// A pasted list becomes one ingredient per line, starting at this box (which
	// is filled if empty, otherwise the lines go in after it). Pasting a single
	// line is left to the browser.
	function handlePaste(event: ClipboardEvent, index: number) {
		const lines = (event.clipboardData?.getData('text') ?? '')
			.split(/\r?\n/)
			.map((line) => line.trim())
			.filter(Boolean);
		if (lines.length < 2) return;
		event.preventDefault();
		const keep = ingredients[index].trim() ? 1 : 0;
		ingredients = [
			...ingredients.slice(0, index + keep),
			...lines,
			...ingredients.slice(index + 1),
		];
		dispatch('change', ingredients);
	}

	let listEl: HTMLDivElement;

	// Enter moves to the next line (adding one after the last) rather than
	// submitting the whole recipe form.
	async function handleKeydown(event: KeyboardEvent, index: number) {
		if (event.key !== 'Enter' || event.isComposing) return;
		event.preventDefault();
		if (index === ingredients.length - 1) addIngredient();
		await tick();
		listEl.querySelectorAll('input')[index + 1]?.focus();
	}
</script>

<section class="form-section">
	<h2 class="section-title required">Ingredients</h2>

	{#if error}
		<p class="error-message mb-4">{error}</p>
	{/if}

	<div class="dynamic-list" bind:this={listEl}>
		{#each ingredients as _ingredient, index (index)}
			<div class="dynamic-list-item">
				<span class="item-number">{index + 1}</span>
				<div class="reorder">
					<button
						type="button"
						on:click={() => moveIngredient(index, -1)}
						disabled={index === 0}
						class="btn-reorder"
						title="Move up"
						aria-label="Move ingredient {index + 1} up"
					>
						↑
					</button>
					<button
						type="button"
						on:click={() => moveIngredient(index, 1)}
						disabled={index === ingredients.length - 1}
						class="btn-reorder"
						title="Move down"
						aria-label="Move ingredient {index + 1} down"
					>
						↓
					</button>
				</div>
				<input
					type="text"
					bind:value={ingredients[index]}
					on:input={handleInput}
					on:keydown={(e) => handleKeydown(e, index)}
					on:paste={(e) => handlePaste(e, index)}
					placeholder="e.g., 2 cups all-purpose flour"
					class="form-input flex-1"
					aria-label="Ingredient {index + 1}"
				/>
				<button
					type="button"
					on:click={() => removeIngredient(index)}
					class="btn-remove"
					title="Remove"
					aria-label="Remove ingredient {index + 1}"
				>
					×
				</button>
			</div>
		{/each}
	</div>

	<button
		type="button"
		on:click={addIngredient}
		class="btn btn-secondary btn-sm mt-3"
	>
		+ Add Ingredient
	</button>
	<p class="paste-help">
		Tip: paste a whole list into any box to get one ingredient per line.
	</p>
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
		color: var(--color-error);
		margin-left: 0.25rem;
	}

	.error-message {
		font-size: 0.875rem;
		color: var(--color-error-text);
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
		background: var(--color-error-bg);
		border-color: var(--color-error);
		color: var(--color-error-text);
	}

	.paste-help {
		font-size: 0.875rem;
		color: var(--text-500);
		margin-top: 0.5rem;
	}

	/* Side by side and as tall as the row, so a finger can hit them */
	.reorder {
		display: flex;
		gap: 0.25rem;
	}

	/* On a phone the row number gives its room to the arrows, and the
	   section padding gives its room to the input box */
	@media (max-width: 480px) {
		.item-number {
			display: none;
		}

		.form-section {
			padding: 1rem;
		}

		.dynamic-list-item {
			gap: 0.5rem;
		}
	}

	.btn-reorder {
		flex-shrink: 0;
		width: 2rem;
		height: 2.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-100);
		border: 1px solid var(--neutral-200);
		border-radius: 0.25rem;
		color: var(--text-600);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-reorder:hover:not(:disabled) {
		background: var(--accent-50);
		border-color: var(--accent-300);
		color: var(--accent-700);
	}

	.btn-reorder:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}

	.mt-3 {
		margin-top: 0.75rem;
	}
</style>
