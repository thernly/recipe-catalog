<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount } from 'svelte';
	import {
		addPlannedMeal,
		type MealPlan,
		type PlannedMealCreate,
	} from '#lib/api/meal-plans.js';
	import { searchRecipes, type RecipeSummary } from '#lib/api/recipes.js';

	export let mealPlan: MealPlan;
	export let day: number;
	export let mealType: string;

	const dispatch = createEventDispatcher();

	let dialogEl: HTMLDivElement;
	const previouslyFocused =
		typeof document !== 'undefined'
			? (document.activeElement as HTMLElement | null)
			: null;

	let recipes: RecipeSummary[] = [];
	let loading = false;
	let error: string | null = null;
	let saving = false;

	let selectedRecipeId: number | null = null;
	let servings: number | null = null;
	let notes: string = '';
	let searchQuery: string = '';

	const dayNames = [
		'Monday',
		'Tuesday',
		'Wednesday',
		'Thursday',
		'Friday',
		'Saturday',
		'Sunday',
	];

	async function loadRecipes() {
		loading = true;
		error = null;

		try {
			const result = await searchRecipes({
				query: searchQuery,
				per_page: 50,
				sort_by: 'recently_added',
			});
			recipes = result.recipes;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load recipes';
			console.error('Failed to load recipes:', err);
		} finally {
			loading = false;
		}
	}

	async function handleSave() {
		if (!selectedRecipeId) {
			error = 'Please select a recipe';
			return;
		}

		saving = true;
		error = null;

		try {
			const mealData: PlannedMealCreate = {
				recipe_id: selectedRecipeId,
				day_of_week: day,
				meal_type: mealType as PlannedMealCreate['meal_type'],
				servings: servings || undefined,
				notes: notes || undefined,
			};

			await addPlannedMeal(mealPlan.id, mealData);
			dispatch('mealAdded');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to add meal';
			console.error('Failed to add meal:', err);
		} finally {
			saving = false;
		}
	}

	function handleClose() {
		dispatch('close');
	}

	function handleSearchInput() {
		loadRecipes();
	}

	onMount(() => {
		dialogEl?.focus();
		loadRecipes();
	});

	onDestroy(() => {
		previouslyFocused?.focus?.();
	});
</script>

<div
	class="modal-overlay"
	on:click={handleClose}
	on:keydown={(e) => e.key === 'Escape' && handleClose()}
	role="presentation"
>
	<div
		class="modal-content"
		bind:this={dialogEl}
		on:click|stopPropagation
		on:keydown|stopPropagation={(e) => e.key === 'Escape' && handleClose()}
		role="dialog"
		tabindex="-1"
		aria-modal="true"
		aria-labelledby="add-meal-title"
	>
		<div class="modal-header">
			<h2 id="add-meal-title">Add Meal</h2>
			<button
				type="button"
				class="close-btn"
				on:click={handleClose}
				aria-label="Close dialog"
				><span aria-hidden="true">&times;</span></button
			>
		</div>

		<div class="modal-body">
			<div class="meal-info">
				<p>
					<strong>{dayNames[day]}</strong> - {mealType.charAt(0).toUpperCase() +
						mealType.slice(1)}
				</p>
			</div>

			{#if error}
				<div class="error" role="alert">{error}</div>
			{/if}

			<div class="form-group">
				<label for="recipe-search">Search Recipes</label>
				<input
					id="recipe-search"
					type="text"
					bind:value={searchQuery}
					on:input={handleSearchInput}
					placeholder="Search recipes..."
					class="input"
				/>
			</div>

			<div class="form-group">
				<span class="label" id="add-recipe-select-label">Select Recipe</span>
				<div
					class="recipe-list"
					role="group"
					aria-labelledby="add-recipe-select-label"
				>
					{#if loading}
						<div class="loading-small">Loading recipes...</div>
					{:else if recipes.length === 0}
						<div class="no-recipes">No recipes found</div>
					{:else}
						{#each recipes as recipe (recipe.id)}
							<button
								type="button"
								class="recipe-item"
								class:selected={selectedRecipeId === recipe.id}
								aria-pressed={selectedRecipeId === recipe.id}
								on:click={() => (selectedRecipeId = recipe.id)}
							>
								<span class="recipe-name">{recipe.name}</span>
								{#if recipe.cuisine || recipe.total_time_minutes}
									<span class="recipe-meta">
										{#if recipe.cuisine}<span>{recipe.cuisine}</span>{/if}
										{#if recipe.total_time_minutes}
											<span>{recipe.total_time_minutes} min</span>
										{/if}
									</span>
								{/if}
							</button>
						{/each}
					{/if}
				</div>
			</div>

			<div class="form-row">
				<div class="form-group">
					<label for="servings">Servings (optional)</label>
					<input
						id="servings"
						type="number"
						bind:value={servings}
						min="1"
						placeholder="Servings"
						class="input"
					/>
				</div>
			</div>

			<div class="form-group">
				<label for="notes">Notes (optional)</label>
				<textarea
					id="notes"
					bind:value={notes}
					placeholder="Add any notes..."
					rows="3"
					class="input"></textarea>
			</div>
		</div>

		<div class="modal-footer">
			<button class="btn-secondary" on:click={handleClose} disabled={saving}
				>Cancel</button
			>
			<button
				class="btn-primary"
				on:click={handleSave}
				disabled={saving || !selectedRecipeId}
			>
				{saving ? 'Adding...' : 'Add Meal'}
			</button>
		</div>
	</div>
</div>

<style>
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}

	.modal-content {
		background-color: var(--neutral-white);
		border-radius: 8px;
		max-width: 600px;
		width: 100%;
		max-height: 90vh;
		display: flex;
		flex-direction: column;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid var(--neutral-300);
	}

	.modal-header h2 {
		margin: 0;
		font-size: 1.5rem;
	}

	.close-btn {
		background: none;
		border: none;
		font-size: 2rem;
		cursor: pointer;
		color: var(--text-600);
		padding: 0;
		width: 2rem;
		height: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-btn:hover {
		color: var(--text-900);
	}

	.modal-body {
		padding: 1.5rem;
		overflow-y: auto;
		flex: 1;
	}

	.meal-info {
		background-color: var(--neutral-100);
		padding: 1rem;
		border-radius: 4px;
		margin-bottom: 1.5rem;
	}

	.meal-info p {
		margin: 0;
	}

	.form-group {
		margin-bottom: 1.5rem;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	label,
	.label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}

	.input {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid var(--neutral-300);
		border-radius: 4px;
		font-size: 1rem;
	}

	.input:focus {
		outline: none;
		border-color: var(--primary-500);
	}

	.recipe-list {
		max-height: 300px;
		overflow-y: auto;
		border: 1px solid var(--neutral-300);
		border-radius: 4px;
	}

	.recipe-item {
		display: block;
		width: 100%;
		text-align: left;
		background: none;
		border: none;
		font: inherit;
		color: inherit;
		padding: 0.75rem;
		cursor: pointer;
		border-bottom: 1px solid var(--neutral-200);
		transition: background-color 0.2s;
	}

	.recipe-item:last-child {
		border-bottom: none;
	}

	.recipe-item:hover {
		background-color: var(--neutral-100);
	}

	.recipe-item.selected {
		background-color: var(--primary-50);
		border-left: 3px solid var(--primary-500);
	}

	.recipe-item:focus {
		outline: 2px solid var(--primary-500);
		outline-offset: -2px;
	}

	.recipe-name {
		display: block;
		font-weight: 500;
		margin-bottom: 0.25rem;
	}

	.recipe-meta {
		font-size: 0.875rem;
		color: var(--text-600);
		display: flex;
		gap: 1rem;
	}

	.loading-small,
	.no-recipes {
		padding: 2rem;
		text-align: center;
		color: var(--text-600);
	}

	.error {
		background-color: var(--color-error-bg);
		color: var(--color-error-text);
		padding: 0.75rem;
		border-radius: 4px;
		margin-bottom: 1rem;
	}

	.modal-footer {
		padding: 1.5rem;
		border-top: 1px solid var(--neutral-300);
		display: flex;
		justify-content: flex-end;
		gap: 1rem;
	}

	.btn-primary,
	.btn-secondary {
		padding: 0.5rem 1.5rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 1rem;
		border: none;
		transition: all 0.2s;
	}

	.btn-primary {
		background-color: var(--primary-500);
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background-color: var(--primary-600);
	}

	.btn-primary:disabled {
		background-color: var(--neutral-300);
		cursor: not-allowed;
	}

	.btn-secondary {
		background-color: var(--neutral-white);
		color: var(--text-900);
		border: 1px solid var(--neutral-300);
	}

	.btn-secondary:hover:not(:disabled) {
		background-color: var(--neutral-100);
	}

	.btn-secondary:disabled {
		color: var(--text-500);
		cursor: not-allowed;
	}
</style>
