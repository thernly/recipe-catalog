<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import {
		updatePlannedMeal,
		deletePlannedMeal,
		type PlannedMeal,
		type PlannedMealUpdate
	} from '$lib/api/meal-plans';
	import { searchRecipes, type RecipeSummary } from '$lib/api/recipes';

	export let meal: PlannedMeal;

	const dispatch = createEventDispatcher();

	let recipes: RecipeSummary[] = [];
	let loading = false;
	let error: string | null = null;
	let saving = false;
	let deleting = false;

	let selectedRecipeId: number = meal.recipe_id;
	let dayOfWeek: number = meal.day_of_week;
	let mealType: string = meal.meal_type;
	let servings: number | null = meal.servings || null;
	let notes: string = meal.notes || '';
	let searchQuery: string = '';

	const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
	const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack', 'other'];

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
		saving = true;
		error = null;

		try {
			const updates: PlannedMealUpdate = {};

			if (selectedRecipeId !== meal.recipe_id) {
				updates.recipe_id = selectedRecipeId;
			}
			if (dayOfWeek !== meal.day_of_week) {
				updates.day_of_week = dayOfWeek;
			}
			if (mealType !== meal.meal_type) {
				updates.meal_type = mealType as any;
			}
			if (servings !== meal.servings) {
				updates.servings = servings || undefined;
			}
			if (notes !== (meal.notes || '')) {
				updates.notes = notes || undefined;
			}

			if (Object.keys(updates).length > 0) {
				await updatePlannedMeal(meal.id, updates);
			}

			dispatch('mealUpdated');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update meal';
			console.error('Failed to update meal:', err);
		} finally {
			saving = false;
		}
	}

	async function handleDelete() {
		if (!confirm('Are you sure you want to remove this meal from the plan?')) {
			return;
		}

		deleting = true;
		error = null;

		try {
			await deletePlannedMeal(meal.id);
			dispatch('mealDeleted');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to delete meal';
			console.error('Failed to delete meal:', err);
		} finally {
			deleting = false;
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

<div class="modal-overlay" on:click={handleClose} on:keydown={(e) => e.key === 'Escape' && handleClose()} role="presentation">
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div class="modal-content" on:click|stopPropagation on:keydown|stopPropagation role="dialog" tabindex="0" aria-modal="true">
		<div class="modal-header">
			<h2>Edit Meal</h2>
			<button class="close-btn" on:click={handleClose}>&times;</button>
		</div>

		<div class="modal-body">
			{#if error}
				<div class="error">{error}</div>
			{/if}

			<div class="form-row">
				<div class="form-group">
					<label for="day-of-week">Day</label>
					<select id="day-of-week" bind:value={dayOfWeek} class="input">
						{#each dayNames as dayName, index}
							<option value={index}>{dayName}</option>
						{/each}
					</select>
				</div>

				<div class="form-group">
					<label for="meal-type">Meal Type</label>
					<select id="meal-type" bind:value={mealType} class="input">
						{#each mealTypes as type}
							<option value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
						{/each}
					</select>
				</div>
			</div>

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

			<div class="form-group">
				<label for="notes">Notes (optional)</label>
				<textarea
					id="notes"
					bind:value={notes}
					placeholder="Add any notes..."
					rows="3"
					class="input"
				></textarea>
			</div>
		</div>

		<div class="modal-footer">
			<button class="btn-danger" on:click={handleDelete} disabled={saving || deleting}>
				{deleting ? 'Deleting...' : 'Delete'}
			</button>
			<div class="spacer"></div>
			<button class="btn-secondary" on:click={handleClose} disabled={saving || deleting}>
				Cancel
			</button>
			<button class="btn-primary" on:click={handleSave} disabled={saving || deleting}>
				{saving ? 'Saving...' : 'Save Changes'}
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
		max-height: 200px;
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

	.spacer {
		flex: 1;
	}

	.btn-primary,
	.btn-secondary,
	.btn-danger {
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

	.btn-danger {
		background-color: #f44336;
		color: white;
	}

	.btn-danger:hover:not(:disabled) {
		background-color: #d32f2f;
	}

	.btn-danger:disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}
</style>
