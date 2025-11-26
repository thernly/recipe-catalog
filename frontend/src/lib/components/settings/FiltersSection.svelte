<script lang="ts">
	import { onMount } from 'svelte';
	import { getPreferences, updatePreferences } from '$lib/api/users';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';

	// Custom filters
	let customCuisines: string[] = [];
	let customCategories: string[] = [];
	let newCuisine = '';
	let newCategory = '';
	let loading = false;
	let saving = false;

	const defaultCuisines = [
		'Italian',
		'Mexican',
		'Chinese',
		'Japanese',
		'Indian',
		'Thai',
		'French',
		'Greek',
		'Spanish',
		'Mediterranean',
		'American',
		'Korean',
		'Vietnamese',
		'Middle Eastern',
		'Other'
	];

	const defaultCategories = [
		'Breakfast',
		'Lunch',
		'Dinner',
		'Appetizer',
		'Main Course',
		'Side Dish',
		'Dessert',
		'Snack',
		'Beverage',
		'Salad',
		'Soup',
		'Pasta',
		'Bread',
		'Sauce',
		'Other'
	];

	onMount(async () => {
		// Load custom filters from user preferences
		loading = true;
		try {
			const prefs = await getPreferences();
			customCuisines = prefs.custom_cuisines || [];
			customCategories = prefs.custom_categories || [];
		} catch (err) {
			console.error('Failed to load custom filters:', err);
			customCuisines = [];
			customCategories = [];
		} finally {
			loading = false;
		}
	});

	async function saveToDatabase() {
		saving = true;
		try {
			await updatePreferences({
				custom_cuisines: customCuisines,
				custom_categories: customCategories
			});
		} catch (err) {
			toast.error('Failed to save custom filters: ' + (err instanceof Error ? err.message : 'Unknown error'));
			console.error('Failed to save custom filters:', err);
		} finally {
			saving = false;
		}
	}

	async function addCuisine() {
		const cuisine = newCuisine.trim();
		if (cuisine && !allCuisines.includes(cuisine)) {
			customCuisines = [...customCuisines, cuisine];
			await saveToDatabase();
			newCuisine = '';
		}
	}

	async function addCategory() {
		const category = newCategory.trim();
		if (category && !allCategories.includes(category)) {
			customCategories = [...customCategories, category];
			await saveToDatabase();
			newCategory = '';
		}
	}

	async function removeCuisine(cuisine: string) {
		customCuisines = customCuisines.filter((c) => c !== cuisine);
		await saveToDatabase();
	}

	async function removeCategory(category: string) {
		customCategories = customCategories.filter((c) => c !== category);
		await saveToDatabase();
	}

	async function resetToDefaults() {
		dialog.show({
			title: 'Reset to Defaults',
			message: 'Reset all custom cuisines and categories to defaults? This will remove any custom entries you\'ve added.',
			onConfirm: async () => {
				customCuisines = [];
				customCategories = [];
				await saveToDatabase();
				toast.success('Filters reset to defaults');
			}
		});
	}

	$: allCuisines = [...defaultCuisines, ...customCuisines];
	$: allCategories = [...defaultCategories, ...customCategories];
</script>

<div class="settings-section">
	<h2 class="section-title">Recipe Filters</h2>
	<p class="section-description">Customize cuisine and category options for filtering recipes</p>

	<!-- Cuisines -->
	<div class="filter-group">
		<h3 class="filter-group-title">Cuisines</h3>
		<p class="filter-group-description">
			Default cuisines are provided, but you can add your own custom options below.
		</p>

		<div class="tags-container">
			{#each defaultCuisines as cuisine}
				<span class="tag tag-default">{cuisine}</span>
			{/each}
			{#each customCuisines as cuisine}
				<span class="tag tag-custom">
					{cuisine}
					<button
						on:click={() => removeCuisine(cuisine)}
						class="tag-remove"
						aria-label="Remove {cuisine}"
					>
						×
					</button>
				</span>
			{/each}
		</div>

		<form on:submit|preventDefault={addCuisine} class="add-form">
			<input
				type="text"
				bind:value={newCuisine}
				placeholder="Add custom cuisine..."
				class="add-input"
				maxlength="30"
			/>
			<button type="submit" class="btn btn-secondary btn-sm" disabled={!newCuisine.trim()}>
				Add
			</button>
		</form>
	</div>

	<!-- Categories -->
	<div class="filter-group">
		<h3 class="filter-group-title">Categories</h3>
		<p class="filter-group-description">
			Default categories are provided, but you can add your own custom options below.
		</p>

		<div class="tags-container">
			{#each defaultCategories as category}
				<span class="tag tag-default">{category}</span>
			{/each}
			{#each customCategories as category}
				<span class="tag tag-custom">
					{category}
					<button
						on:click={() => removeCategory(category)}
						class="tag-remove"
						aria-label="Remove {category}"
					>
						×
					</button>
				</span>
			{/each}
		</div>

		<form on:submit|preventDefault={addCategory} class="add-form">
			<input
				type="text"
				bind:value={newCategory}
				placeholder="Add custom category..."
				class="add-input"
				maxlength="30"
			/>
			<button type="submit" class="btn btn-secondary btn-sm" disabled={!newCategory.trim()}>
				Add
			</button>
		</form>
	</div>

	<!-- Reset button -->
	<div class="reset-section">
		<button on:click={resetToDefaults} class="btn btn-secondary">
			Reset to Defaults
		</button>
		<p class="help-text">This will remove all custom cuisines and categories</p>
	</div>

	<!-- Info note -->
	<div class="info-note">
		<p>
			<strong>Note:</strong> Custom filters are stored in your account and synced across all your
			devices. Default options cannot be removed, but you can add your own custom options to
			better organize your recipes.
		</p>
	</div>
</div>

<style>
	.settings-section {
		max-width: 700px;
	}

	.section-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0 0 0.5rem 0;
	}

	.section-description {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 2rem 0;
	}

	.filter-group {
		margin-bottom: 2rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid var(--neutral-200);
	}

	.filter-group:last-of-type {
		border-bottom: none;
	}

	.filter-group-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.5rem 0;
	}

	.filter-group-description {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 1rem 0;
	}

	.tags-container {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.tag {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		border-radius: var(--radius-full);
		font-size: 0.875rem;
		font-weight: 500;
	}

	.tag-default {
		background: var(--neutral-100);
		color: var(--text-700);
		border: 1px solid var(--neutral-200);
	}

	.tag-custom {
		background: var(--accent-50);
		color: var(--accent-800);
		border: 1px solid var(--accent-200);
	}

	.tag-remove {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 1.25rem;
		height: 1.25rem;
		background: var(--accent-100);
		border: none;
		border-radius: 50%;
		color: var(--accent-700);
		font-size: 1rem;
		line-height: 1;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.tag-remove:hover {
		background: var(--accent-200);
		color: var(--accent-900);
	}

	.add-form {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}

	.add-input {
		flex: 1;
		padding: 0.75rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		color: var(--text-900);
		background: var(--neutral-white);
		transition: all var(--transition-fast);
	}

	.add-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.btn-sm {
		padding: 0.75rem 1.5rem;
		font-size: 0.875rem;
	}

	.reset-section {
		margin-top: 2rem;
		padding-top: 2rem;
		border-top: 1px solid var(--neutral-200);
	}

	.help-text {
		font-size: 0.875rem;
		color: var(--text-600);
		margin-top: 0.5rem;
	}

	.info-note {
		margin-top: 2rem;
		padding: 1rem;
		background: var(--accent-50);
		border-left: 3px solid var(--accent-500);
		border-radius: var(--radius-md);
	}

	.info-note p {
		font-size: 0.875rem;
		color: var(--accent-800);
		margin: 0;
		line-height: 1.5;
	}
</style>
