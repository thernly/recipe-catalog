<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { searchRecipes, deleteRecipe, type RecipeSearchParams } from '$lib/api/recipes';
	import type { RecipeSearchResult, RecipeSummary } from '$lib/api/recipes';
	import RecipeCard from '$lib/components/RecipeCard.svelte';
	import RecipeListItem from '$lib/components/RecipeListItem.svelte';
	import FilterSidebar from '$lib/components/FilterSidebar.svelte';
	import Navbar from '$lib/components/Navbar.svelte';

	let searchResult: RecipeSearchResult | null = null;
	let loading = true;
	let error: string | null = null;

	// View mode
	let viewMode: 'grid' | 'list' = 'grid';

	// Show/hide filters
	let showFilters = true;

	// Search and filter params
	let searchParams: RecipeSearchParams = {
		query: '',
		sort_by: 'recently_added',
		page: 1,
		per_page: 24
	};

	// Filter values
	let selectedCuisines: string[] = [];
	let selectedCategories: string[] = [];
	let selectedSourceTypes: string[] = [];
	let maxTime: number | undefined;
	let minTime: number | undefined;

	// Load recipes
	async function loadRecipes() {
		loading = true;
		error = null;

		try {
			const params: RecipeSearchParams = {
				...searchParams,
				cuisine: selectedCuisines.length > 0 ? selectedCuisines : undefined,
				category: selectedCategories.length > 0 ? selectedCategories : undefined,
				source_type: selectedSourceTypes.length > 0 ? selectedSourceTypes : undefined,
				max_time_minutes: maxTime,
				min_time_minutes: minTime
			};

			searchResult = await searchRecipes(params);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load recipes';
			console.error('Failed to load recipes:', err);
		} finally {
			loading = false;
		}
	}

	// Handle search
	let searchTimeout: number;
	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		searchParams.query = target.value;

		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			searchParams.page = 1;
			loadRecipes();
		}, 300);
	}

	// Handle sort change
	function handleSortChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		searchParams.sort_by = target.value as any;
		searchParams.page = 1;
		loadRecipes();
	}

	// Handle pagination
	function goToPage(page: number) {
		searchParams.page = page;
		loadRecipes();
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	// Handle recipe actions
	function handleViewRecipe(e: CustomEvent) {
		const recipe = e.detail as RecipeSummary;
		goto(`/recipes/${recipe.id}`);
	}

	function handleEditRecipe(e: CustomEvent) {
		const recipe = e.detail as RecipeSummary;
		goto(`/recipes/${recipe.id}/edit`);
	}

	async function handleDeleteRecipe(e: CustomEvent) {
		const recipe = e.detail as RecipeSummary;

		if (
			confirm(`Are you sure you want to delete "${recipe.name}"? It will be moved to trash.`)
		) {
			try {
				await deleteRecipe(recipe.id);
				loadRecipes();
			} catch (err) {
				alert('Failed to delete recipe');
				console.error('Delete failed:', err);
			}
		}
	}

	function handleFavoriteRecipe(e: CustomEvent) {
		const recipe = e.detail as RecipeSummary;
		// TODO: Implement favorites
		console.log('Favorite:', recipe);
	}

	// Toggle view mode
	function toggleViewMode(mode: 'grid' | 'list') {
		viewMode = mode;
		localStorage.setItem('recipe-view-mode', mode);
	}

	// Handle filter changes
	function handleFilterChange(e: CustomEvent) {
		const filters = e.detail;
		selectedCuisines = filters.selectedCuisines;
		selectedCategories = filters.selectedCategories;
		selectedSourceTypes = filters.selectedSourceTypes;
		maxTime = filters.maxTime;
		minTime = filters.minTime;
		searchParams.page = 1; // Reset to first page when filters change
		loadRecipes();
	}

	// Initialize
	onMount(() => {
		// Restore view mode from localStorage
		const savedViewMode = localStorage.getItem('recipe-view-mode');
		if (savedViewMode === 'grid' || savedViewMode === 'list') {
			viewMode = savedViewMode;
		}

		loadRecipes();
	});
</script>

<svelte:head>
	<title>My Recipes - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	<!-- Navbar -->
	<Navbar />

	<!-- Header -->
	<div class="sticky top-16 z-40 bg-white border-b border-neutral-200">
		<div class="container-custom py-4">
			<!-- Top row: Title and View toggle -->
			<div class="flex items-center justify-between mb-4">
				<h1 class="text-3xl font-bold" style="color: var(--text-900);">My Recipes</h1>

				<div class="flex items-center gap-2">
					<button
						on:click={() => goto('/import')}
						class="import-btn"
						title="Import recipes"
					>
						📥 Import
					</button>
					<button
						on:click={() => (showFilters = !showFilters)}
						class="filter-toggle-btn"
						title={showFilters ? 'Hide filters' : 'Show filters'}
					>
						🔍 {showFilters ? 'Hide' : 'Show'} Filters
					</button>
					<button
						on:click={() => toggleViewMode('grid')}
						class="view-btn"
						class:active={viewMode === 'grid'}
						title="Grid view"
					>
						⊞
					</button>
					<button
						on:click={() => toggleViewMode('list')}
						class="view-btn"
						class:active={viewMode === 'list'}
						title="List view"
					>
						≡
					</button>
				</div>
			</div>

			<!-- Search and Sort -->
			<div class="flex flex-col sm:flex-row gap-4">
				<!-- Search bar -->
				<div class="flex-1">
					<input
						type="search"
						placeholder="Search recipes..."
						value={searchParams.query}
						on:input={handleSearch}
						class="search-input"
					/>
				</div>

				<!-- Sort dropdown -->
				<select
					value={searchParams.sort_by}
					on:change={handleSortChange}
					class="sort-select"
				>
					<option value="recently_added">Recently Added</option>
					<option value="alphabetical">A-Z</option>
					<option value="time_asc">Shortest Time</option>
					<option value="time_desc">Longest Time</option>
				</select>
			</div>

			<!-- Active count -->
			{#if searchResult}
				<p class="mt-3 text-sm" style="color: var(--text-600);">
					Showing {searchResult.recipes.length} of {searchResult.total} recipes
				</p>
			{/if}
		</div>
	</div>

	<!-- Main content -->
	<div class="container-custom py-8">
		<div class="recipes-layout">
			<!-- Filter Sidebar -->
			{#if showFilters}
				<div class="filter-column">
					<FilterSidebar
						bind:selectedCuisines
						bind:selectedCategories
						bind:selectedSourceTypes
						bind:maxTime
						bind:minTime
						on:change={handleFilterChange}
					/>
				</div>
			{/if}

			<!-- Recipes Column -->
			<div class="recipes-column">
		{#if loading}
			<!-- Loading state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⏳</div>
				<p class="text-lg" style="color: var(--text-600);">Loading recipes...</p>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⚠️</div>
				<p class="text-lg mb-2" style="color: var(--text-900);">Failed to load recipes</p>
				<p class="text-sm mb-4" style="color: var(--text-600);">{error}</p>
				<button on:click={loadRecipes} class="btn btn-primary">Try Again</button>
			</div>
		{:else if searchResult && searchResult.recipes.length === 0}
			<!-- Empty state -->
			<div class="text-center py-16">
				<div class="text-6xl mb-4">🍽️</div>
				<h2 class="text-2xl font-semibold mb-2" style="color: var(--text-900);">
					No recipes yet
				</h2>
				<p class="text-lg mb-6" style="color: var(--text-600);">
					Start building your collection
				</p>
				<div class="flex flex-col sm:flex-row gap-4 justify-center">
					<button on:click={() => goto('/recipes/new')} class="btn btn-primary">
						+ Add Recipe
					</button>
					<button on:click={() => goto('/import')} class="btn btn-secondary">
						📥 Import Recipes
					</button>
				</div>
			</div>
		{:else if searchResult}
			<!-- Recipe grid/list -->
			{#if viewMode === 'grid'}
				<div class="recipe-grid">
					{#each searchResult.recipes as recipe (recipe.id)}
						<RecipeCard
							{recipe}
							on:view={handleViewRecipe}
							on:edit={handleEditRecipe}
							on:delete={handleDeleteRecipe}
							on:favorite={handleFavoriteRecipe}
						/>
					{/each}
				</div>
			{:else}
				<div class="recipe-list">
					{#each searchResult.recipes as recipe (recipe.id)}
						<RecipeListItem
							{recipe}
							on:view={handleViewRecipe}
							on:edit={handleEditRecipe}
							on:delete={handleDeleteRecipe}
							on:favorite={handleFavoriteRecipe}
						/>
					{/each}
				</div>
			{/if}

			<!-- Pagination -->
			{#if searchResult.total_pages > 1}
				<div class="flex justify-center items-center gap-2 mt-8">
					<button
						on:click={() => goToPage(searchParams.page - 1)}
						disabled={!searchResult.has_prev}
						class="pagination-btn"
					>
						← Previous
					</button>

					<span class="text-sm" style="color: var(--text-600);">
						Page {searchParams.page} of {searchResult.total_pages}
					</span>

					<button
						on:click={() => goToPage(searchParams.page + 1)}
						disabled={!searchResult.has_next}
						class="pagination-btn"
					>
						Next →
					</button>
				</div>
			{/if}
		{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.search-input {
		width: 100%;
		padding: 0.75rem 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 1rem;
		transition: all var(--transition-fast);
		background: var(--neutral-white);
		color: var(--text-900);
	}

	.search-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.sort-select {
		padding: 0.75rem 2.5rem 0.75rem 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 1rem;
		background: var(--neutral-white);
		color: var(--text-900);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.sort-select:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.view-btn {
		width: 2.5rem;
		height: 2.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
		color: var(--text-600);
		font-size: 1.25rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.view-btn:hover {
		border-color: var(--accent-300);
		color: var(--accent-600);
	}

	.view-btn.active {
		background: var(--accent-500);
		border-color: var(--accent-500);
		color: var(--neutral-white);
	}

	.recipe-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1.5rem;
	}

	.recipe-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.pagination-btn {
		padding: 0.5rem 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
		color: var(--text-900);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.pagination-btn:hover:not(:disabled) {
		background: var(--accent-50);
		border-color: var(--accent-300);
	}

	.pagination-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.import-btn {
		padding: 0.5rem 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
		color: var(--text-900);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.import-btn:hover {
		background: var(--accent-50);
		border-color: var(--accent-300);
	}

	.filter-toggle-btn {
		padding: 0.5rem 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
		color: var(--text-900);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.filter-toggle-btn:hover {
		background: var(--accent-50);
		border-color: var(--accent-300);
	}

	.recipes-layout {
		display: flex;
		gap: 2rem;
		align-items: start;
	}

	.filter-column {
		flex: 0 0 280px;
		min-width: 280px;
	}

	.recipes-column {
		flex: 1;
		min-width: 0;
	}

	@media (max-width: 1024px) {
		.recipes-layout {
			flex-direction: column;
		}

		.filter-column {
			width: 100%;
			flex: 1;
		}
	}
</style>
