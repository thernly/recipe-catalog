<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount } from 'svelte';
	import {
		updatePlannedMeal,
		deletePlannedMeal,
		type PlannedMeal,
		type PlannedMealUpdate,
	} from '#lib/api/meal-plans.js';
	import { searchRecipes, type RecipeSummary } from '#lib/api/recipes.js';
	import { dialog } from '#lib/stores/dialog.js';
	import { toast } from '#lib/stores/toast.js';
	import { trapFocus } from '#lib/actions/trapFocus.js';

	export let meal: PlannedMeal;

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
	let deleting = false;

	let selectedRecipeId: number = meal.recipe_id;
	let dayOfWeek: number = meal.day_of_week;
	let mealType: string = meal.meal_type;
	let servings: number | null = meal.servings || null;
	let notes: string = meal.notes || '';
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
	const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack', 'other'];

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
				updates.meal_type = mealType as PlannedMealUpdate['meal_type'];
			}
			// null (not undefined) so that emptying a field clears it on the server
			if ((servings || null) !== (meal.servings || null)) {
				updates.servings = servings || null;
			}
			if (notes !== (meal.notes || '')) {
				updates.notes = notes || null;
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
		dialog.show({
			title: 'Remove Meal',
			message: 'Are you sure you want to remove this meal from the plan?',
			onConfirm: async () => {
				deleting = true;
				error = null;

				try {
					await deletePlannedMeal(meal.id);
					toast.success('Meal removed from plan');
					dispatch('mealDeleted');
				} catch (err) {
					error = err instanceof Error ? err.message : 'Failed to delete meal';
					toast.error('Failed to delete meal');
					console.error('Failed to delete meal:', err);
				} finally {
					deleting = false;
				}
			},
		});
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
		aria-labelledby="edit-meal-title"
		use:trapFocus
	>
		<div class="modal-header">
			<h2 id="edit-meal-title">Edit Meal</h2>
			<button
				type="button"
				class="close-btn"
				on:click={handleClose}
				aria-label="Close dialog"
			>
				<span aria-hidden="true">&times;</span>
			</button>
		</div>

		<div class="modal-body">
			{#if error}
				<div class="error" role="alert">{error}</div>
			{/if}

			<p style="margin-bottom: 1rem;">
				<a
					href="/recipes/{meal.recipe_id}"
					style="color: var(--accent-600); text-decoration: underline;"
				>
					View recipe{meal.recipe_name ? `: ${meal.recipe_name}` : ''}
				</a>
			</p>

			<div class="form-row">
				<div class="form-group">
					<label for="day-of-week">Day</label>
					<select id="day-of-week" bind:value={dayOfWeek} class="input">
						{#each dayNames as dayName, index (dayName)}
							<option value={index}>{dayName}</option>
						{/each}
					</select>
				</div>

				<div class="form-group">
					<label for="meal-type">Meal Type</label>
					<select id="meal-type" bind:value={mealType} class="input">
						{#each mealTypes as type (type)}
							<option value={type}>
								{type.charAt(0).toUpperCase() + type.slice(1)}
							</option>
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
				<span class="label" id="edit-recipe-select-label">Select Recipe</span>
				<div
					class="recipe-list"
					role="group"
					aria-labelledby="edit-recipe-select-label"
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
					class="input"></textarea>
			</div>
		</div>

		<div class="modal-footer">
			<button
				class="btn-danger"
				on:click={handleDelete}
				disabled={saving || deleting}
			>
				{deleting ? 'Deleting...' : 'Delete'}
			</button>
			<div class="spacer"></div>
			<button
				class="btn-secondary"
				on:click={handleClose}
				disabled={saving || deleting}
			>
				Cancel
			</button>
			<button
				class="btn-primary"
				on:click={handleSave}
				disabled={saving || deleting}
			>
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
		max-height: 200px;
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

	.btn-danger {
		background-color: var(--color-error);
		color: white;
	}

	.btn-danger:hover:not(:disabled) {
		filter: brightness(0.9);
	}

	.btn-danger:disabled {
		background-color: var(--neutral-300);
		cursor: not-allowed;
	}
</style>
