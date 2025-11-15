<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { getRecipe, deleteRecipe, duplicateRecipe, type Recipe } from '$lib/api/recipes';

	let recipe: Recipe | null = null;
	let loading = true;
	let error: string | null = null;
	let checkedIngredients = new Set<number>();

	// Get recipe ID from URL
	$: recipeId = parseInt($page.params.id);

	async function loadRecipe() {
		loading = true;
		error = null;

		try {
			recipe = await getRecipe(recipeId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load recipe';
			console.error('Failed to load recipe:', err);
		} finally {
			loading = false;
		}
	}

	function toggleIngredient(index: number) {
		if (checkedIngredients.has(index)) {
			checkedIngredients.delete(index);
		} else {
			checkedIngredients.add(index);
		}
		checkedIngredients = checkedIngredients; // Trigger reactivity
	}

	function getIngredients(recipe: Recipe): string[] {
		if (recipe.recipe_data?.recipeIngredient) {
			return recipe.recipe_data.recipeIngredient;
		}
		return [];
	}

	function getInstructions(recipe: Recipe): string[] {
		if (recipe.recipe_data?.recipeInstructions) {
			const instructions = recipe.recipe_data.recipeInstructions;
			if (Array.isArray(instructions)) {
				return instructions.map((item: any) => {
					if (typeof item === 'string') return item;
					if (item?.text) return item.text;
					return JSON.stringify(item);
				});
			}
		}
		return [];
	}

	function formatTime(duration: string | undefined): string {
		if (!duration) return '';
		// Parse ISO 8601 duration (PT1H30M format)
		const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
		if (!match) return duration;

		const hours = parseInt(match[1] || '0');
		const minutes = parseInt(match[2] || '0');

		if (hours && minutes) return `${hours}h ${minutes}min`;
		if (hours) return `${hours}h`;
		if (minutes) return `${minutes}min`;
		return '';
	}

	async function handleDelete() {
		if (!recipe) return;

		if (confirm(`Are you sure you want to delete "${recipe.name}"? It will be moved to trash.`)) {
			try {
				await deleteRecipe(recipe.id);
				goto('/recipes');
			} catch (err) {
				alert('Failed to delete recipe');
				console.error('Delete failed:', err);
			}
		}
	}

	async function handleDuplicate() {
		if (!recipe) return;

		try {
			const duplicated = await duplicateRecipe(recipe.id);
			goto(`/recipes/${duplicated.id}/edit`);
		} catch (err) {
			alert('Failed to duplicate recipe');
			console.error('Duplicate failed:', err);
		}
	}

	function handlePrint() {
		window.print();
	}

	onMount(() => {
		loadRecipe();
	});
</script>

<svelte:head>
	<title>{recipe?.name || 'Loading...'} - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	{#if loading}
		<!-- Loading state -->
		<div class="container-custom py-16 text-center">
			<div class="text-4xl mb-4">⏳</div>
			<p class="text-lg" style="color: var(--text-600);">Loading recipe...</p>
		</div>
	{:else if error || !recipe}
		<!-- Error state -->
		<div class="container-custom py-16 text-center">
			<div class="text-4xl mb-4">⚠️</div>
			<p class="text-lg mb-2" style="color: var(--text-900);">Recipe not found</p>
			<p class="text-sm mb-4" style="color: var(--text-600);">{error || 'This recipe may have been deleted.'}</p>
			<button on:click={() => goto('/recipes')} class="btn btn-primary">Back to Recipes</button>
		</div>
	{:else}
		<!-- Recipe content -->
		<div class="recipe-detail-container">
			<!-- Header -->
			<div class="recipe-header">
				<div class="container-custom py-6">
					<button
						on:click={() => goto('/recipes')}
						class="text-sm mb-4 flex items-center gap-2"
						style="color: var(--text-600);"
					>
						← Back to Recipes
					</button>

					<div class="flex justify-between items-start">
						<div class="flex-1">
							<h1 class="text-4xl font-bold mb-2" style="color: var(--text-900);">
								{recipe.name}
							</h1>

							{#if recipe.source_url}
								<p class="text-sm mb-2" style="color: var(--text-600);">
									Source: <a href={recipe.source_url} target="_blank" class="link">
										{new URL(recipe.source_url).hostname}
									</a>
								</p>
							{:else}
								<p class="text-sm mb-2" style="color: var(--text-600);">Personal Recipe</p>
							{/if}

							<div class="flex items-center gap-3 text-xs" style="color: var(--text-500);">
								<span>{recipe.source_type === 'imported' ? '📥 Imported' : '✏️ Manual'}</span>
								{#if recipe.is_modified && recipe.source_type === 'imported'}
									<span>• Modified</span>
								{/if}
								<span>• Added {new Date(recipe.created_at).toLocaleDateString()}</span>
							</div>
						</div>

						<!-- Actions -->
						<div class="flex gap-2">
							<button on:click={() => goto(`/recipes/${recipe.id}/edit`)} class="btn btn-secondary">
								✏️ Edit
							</button>
							<button on:click={handleDuplicate} class="btn btn-secondary">📋 Duplicate</button>
							<button on:click={handlePrint} class="btn btn-secondary">🖨️ Print</button>
							<button on:click={handleDelete} class="btn btn-danger">🗑️ Delete</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Hero Image -->
			{#if recipe.image_url}
				<div class="recipe-hero-image">
					<img src={recipe.image_url} alt={recipe.name} />
				</div>
			{/if}

			<!-- Main content -->
			<div class="container-custom py-8">
				<!-- Description -->
				{#if recipe.description}
					<p class="text-lg mb-8" style="color: var(--text-700);">{recipe.description}</p>
				{/if}

				<!-- Metadata cards -->
				<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
					{#if recipe.recipe_data?.prepTime}
						<div class="metadata-card">
							<div class="metadata-label">Prep Time</div>
							<div class="metadata-value">{formatTime(recipe.recipe_data.prepTime)}</div>
						</div>
					{/if}

					{#if recipe.recipe_data?.cookTime}
						<div class="metadata-card">
							<div class="metadata-label">Cook Time</div>
							<div class="metadata-value">{formatTime(recipe.recipe_data.cookTime)}</div>
						</div>
					{/if}

					{#if recipe.recipe_data?.totalTime || recipe.total_time_minutes}
						<div class="metadata-card">
							<div class="metadata-label">Total Time</div>
							<div class="metadata-value">
								{recipe.recipe_data?.totalTime ? formatTime(recipe.recipe_data.totalTime) : `${recipe.total_time_minutes}min`}
							</div>
						</div>
					{/if}

					{#if recipe.recipe_data?.recipeYield}
						<div class="metadata-card">
							<div class="metadata-label">Yield</div>
							<div class="metadata-value">{recipe.recipe_data.recipeYield}</div>
						</div>
					{/if}
				</div>

				<!-- Tags -->
				{#if recipe.cuisine || recipe.category || recipe.recipe_data?.keywords}
					<div class="flex flex-wrap gap-2 mb-8">
						{#if recipe.cuisine}
							<span class="tag">{recipe.cuisine}</span>
						{/if}
						{#if recipe.category}
							<span class="tag tag-secondary">{recipe.category}</span>
						{/if}
						{#if recipe.recipe_data?.keywords}
							{#each recipe.recipe_data.keywords.split(',').slice(0, 5) as keyword}
								<span class="tag tag-outline">{keyword.trim()}</span>
							{/each}
						{/if}
					</div>
				{/if}

				<!-- Ingredients and Instructions -->
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
					<!-- Ingredients -->
					<div class="card">
						<h2 class="text-2xl font-semibold mb-4" style="color: var(--text-900);">
							Ingredients
						</h2>

						<ul class="space-y-3">
							{#each getIngredients(recipe) as ingredient, index}
								<li class="flex items-start gap-3">
									<input
										type="checkbox"
										id="ingredient-{index}"
										checked={checkedIngredients.has(index)}
										on:change={() => toggleIngredient(index)}
										class="ingredient-checkbox"
									/>
									<label
										for="ingredient-{index}"
										class="flex-1 cursor-pointer"
										class:line-through={checkedIngredients.has(index)}
										class:opacity-50={checkedIngredients.has(index)}
										style="color: var(--text-700);"
									>
										{ingredient}
									</label>
								</li>
							{/each}
						</ul>
					</div>

					<!-- Instructions -->
					<div class="card">
						<h2 class="text-2xl font-semibold mb-4" style="color: var(--text-900);">
							Instructions
						</h2>

						<ol class="space-y-4">
							{#each getInstructions(recipe) as instruction, index}
								<li class="flex gap-3">
									<span
										class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold"
										style="background: var(--accent-100); color: var(--accent-800);"
									>
										{index + 1}
									</span>
									<p class="flex-1 pt-1" style="color: var(--text-700);">
										{instruction}
									</p>
								</li>
							{/each}
						</ol>
					</div>
				</div>

				<!-- Notes (if any) -->
				{#if recipe.recipe_data?.notes}
					<div class="card mt-8">
						<h2 class="text-xl font-semibold mb-3" style="color: var(--text-900);">Notes & Tips</h2>
						<p style="color: var(--text-700);">{recipe.recipe_data.notes}</p>
					</div>
				{/if}

				<!-- Nutrition (if any) -->
				{#if recipe.recipe_data?.nutrition}
					<details class="card mt-8">
						<summary class="text-xl font-semibold cursor-pointer" style="color: var(--text-900);">
							Nutrition Information
						</summary>
						<div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
							{#each Object.entries(recipe.recipe_data.nutrition) as [key, value]}
								<div>
									<div class="text-sm" style="color: var(--text-600);">{key}</div>
									<div class="font-semibold" style="color: var(--text-900);">{value}</div>
								</div>
							{/each}
						</div>
					</details>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.recipe-detail-container {
		background: var(--neutral-white);
		min-height: 100vh;
	}

	.recipe-header {
		background: var(--neutral-50);
		border-bottom: 1px solid var(--neutral-200);
	}

	.recipe-hero-image {
		width: 100%;
		max-height: 500px;
		overflow: hidden;
		background: var(--neutral-100);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.recipe-hero-image img {
		width: 100%;
		height: auto;
		object-fit: cover;
	}

	.metadata-card {
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		padding: 1rem;
		text-align: center;
	}

	.metadata-label {
		font-size: 0.875rem;
		color: var(--text-600);
		margin-bottom: 0.25rem;
	}

	.metadata-value {
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text-900);
	}

	.tag {
		display: inline-flex;
		align-items: center;
		padding: 0.5rem 1rem;
		background: var(--color-badge-bg);
		color: var(--color-badge-text);
		border-radius: var(--radius-full);
		font-size: 0.875rem;
		font-weight: 500;
	}

	.tag-secondary {
		background: var(--neutral-100);
		color: var(--text-700);
	}

	.tag-outline {
		background: transparent;
		border: 1px solid var(--neutral-300);
		color: var(--text-600);
	}

	.ingredient-checkbox {
		margin-top: 0.25rem;
		width: 1.25rem;
		height: 1.25rem;
		cursor: pointer;
		accent-color: var(--accent-500);
	}

	.link {
		color: var(--accent-500);
		text-decoration: underline;
		transition: color var(--transition-fast);
	}

	.link:hover {
		color: var(--accent-600);
	}

	.btn-danger {
		background: #EF4444;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		cursor: pointer;
		border: none;
		transition: all var(--transition-fast);
	}

	.btn-danger:hover {
		background: #DC2626;
	}

	/* Print styles */
	@media print {
		.recipe-header button,
		.btn,
		.btn-danger {
			display: none;
		}

		.recipe-detail-container {
			background: white;
		}

		.ingredient-checkbox {
			display: none;
		}
	}
</style>
