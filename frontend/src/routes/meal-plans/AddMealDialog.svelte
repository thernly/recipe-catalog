<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { addPlannedMeal, type MealPlan, type PlannedMealCreate } from '$lib/api/meal-plans';
	import { searchRecipes, type RecipeSummary } from '$lib/api/recipes';

	export let mealPlan: MealPlan;
	export let day: number;
	export let mealType: string;

	const dispatch = createEventDispatcher();

	let recipes: RecipeSummary[] = [];
	let loading = false;
	let error: string | null = null;
	let saving = false;

	let selectedRecipeId: number | null = null;
	let servings: number | null = null;
	let notes: string = '';
	let searchQuery: string = '';

	const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

	async function loadRecipes() {
		loading = true;
		error = null;

		try {
			const result = await searchRecipes({
				query: searchQuery,
				per_page: 50,
				sort_by: 'recently_added'
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
				meal_type: mealType as any,
				servings: servings || undefined,
				notes: notes || undefined
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
		loadRecipes();
	});
</script>

<div class="modal-overlay" on:click={handleClose} on:keydown={(e) => e.key === 'Escape' && handleClose()} role="button" tabindex="-1">
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div class="modal-content" on:click|stopPropagation on:keydown|stopPropagation role="dialog">
		<div class="modal-header">
			<h2>Add Meal</h2>
			<button class="close-btn" on:click={handleClose}>&times;</button>
		</div>

		<div class="modal-body">
			<div class="meal-info">
				<p>
					<strong>{dayNames[day]}</strong> - {mealType.charAt(0).toUpperCase() + mealType.slice(1)}
				</p>
			</div>

			{#if error}
				<div class="error">{error}</div>
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
				<label for="recipe-select">Select Recipe</label>
				<div class="recipe-list">
					{#if loading}
						<div class="loading-small">Loading recipes...</div>
					{:else if recipes.length === 0}
						<div class="no-recipes">No recipes found</div>
					{:else}
						{#each recipes as recipe}
							<div
								class="recipe-item"
								class:selected={selectedRecipeId === recipe.id}
								on:click={() => (selectedRecipeId = recipe.id)}
								on:keydown={(e) => e.key === 'Enter' && (selectedRecipeId = recipe.id)}
								role="button"
								tabindex="0"
							>
								<div class="recipe-name">{recipe.name}</div>
								{#if recipe.cuisine || recipe.total_time_minutes}
									<div class="recipe-meta">
										{#if recipe.cuisine}<span>{recipe.cuisine}</span>{/if}
										{#if recipe.total_time_minutes}
											<span>{recipe.total_time_minutes} min</span>
										{/if}
									</div>
								{/if}
							</div>
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
					class="input"
				/>
			</div>
		</div>

		<div class="modal-footer">
			<button class="btn-secondary" on:click={handleClose} disabled={saving}>Cancel</button>
			<button class="btn-primary" on:click={handleSave} disabled={saving || !selectedRecipeId}>
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
		background-color: white;
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
		border-bottom: 1px solid #ddd;
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
		color: #666;
		padding: 0;
		width: 2rem;
		height: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-btn:hover {
		color: #333;
	}

	.modal-body {
		padding: 1.5rem;
		overflow-y: auto;
		flex: 1;
	}

	.meal-info {
		background-color: #f5f5f5;
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

	label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}

	.input {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		font-size: 1rem;
	}

	.input:focus {
		outline: none;
		border-color: #2196f3;
	}

	.recipe-list {
		max-height: 300px;
		overflow-y: auto;
		border: 1px solid #ddd;
		border-radius: 4px;
	}

	.recipe-item {
		padding: 0.75rem;
		cursor: pointer;
		border-bottom: 1px solid #eee;
		transition: background-color 0.2s;
	}

	.recipe-item:last-child {
		border-bottom: none;
	}

	.recipe-item:hover {
		background-color: #f9f9f9;
	}

	.recipe-item.selected {
		background-color: #e3f2fd;
		border-left: 3px solid #2196f3;
	}

	.recipe-item:focus {
		outline: 2px solid #2196f3;
		outline-offset: -2px;
	}

	.recipe-name {
		font-weight: 500;
		margin-bottom: 0.25rem;
	}

	.recipe-meta {
		font-size: 0.875rem;
		color: #666;
		display: flex;
		gap: 1rem;
	}

	.loading-small,
	.no-recipes {
		padding: 2rem;
		text-align: center;
		color: #666;
	}

	.error {
		background-color: #ffebee;
		color: #c62828;
		padding: 0.75rem;
		border-radius: 4px;
		margin-bottom: 1rem;
	}

	.modal-footer {
		padding: 1.5rem;
		border-top: 1px solid #ddd;
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
		background-color: #2196f3;
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background-color: #1976d2;
	}

	.btn-primary:disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}

	.btn-secondary {
		background-color: white;
		color: #333;
		border: 1px solid #ddd;
	}

	.btn-secondary:hover:not(:disabled) {
		background-color: #f5f5f5;
	}

	.btn-secondary:disabled {
		color: #999;
		cursor: not-allowed;
	}
</style>
