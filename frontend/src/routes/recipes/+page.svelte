<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { searchRecipes, deleteRecipe, type RecipeSearchParams } from '$lib/api/recipes';
	import type { RecipeSearchResult, RecipeSummary } from '$lib/api/recipes';
	import type { RecipeSortBy, ViewMode } from '$lib/types';
	import RecipeCard from '$lib/components/RecipeCard.svelte';
	import RecipeListItem from '$lib/components/RecipeListItem.svelte';
	import FilterSidebar from '$lib/components/FilterSidebar.svelte';
	import CollectionsSidebar from '$lib/components/CollectionsSidebar.svelte';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';
	import { Download, Search, Folder, Grid, List, UtensilsCrossed, AlertCircle, Loader2 } from 'lucide-svelte';
	import { DEFAULT_PAGE, DEFAULT_PAGE_SIZE, DEBOUNCE_DELAY } from '$lib/constants';

	let searchResult: RecipeSearchResult | null = null;
	let loading = true;
	let error: string | null = null;

	// View mode
	let viewMode: ViewMode = 'grid';

	// Show/hide filters and collections
	let showFilters = true;
	let showCollections = true;

	// Search and filter params
	let searchParams: RecipeSearchParams = {
		query: '',
		sort_by: 'recently_added',
		page: DEFAULT_PAGE,
		per_page: DEFAULT_PAGE_SIZE
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
	let searchTimeout: ReturnType<typeof setTimeout>;
	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		searchParams.query = target.value;

		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			searchParams.page = DEFAULT_PAGE;
			loadRecipes();
		}, DEBOUNCE_DELAY);
	}

	// Handle sort change
	function handleSortChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		searchParams.sort_by = target.value as RecipeSortBy;
		searchParams.page = DEFAULT_PAGE;
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

		dialog.show({
			title: 'Delete Recipe',
			message: `Are you sure you want to delete "${recipe.name}"? It will be moved to trash.`,
			onConfirm: async () => {
				try {
					await deleteRecipe(recipe.id);
					toast.success('Recipe deleted successfully');
					loadRecipes();
				} catch (err) {
					toast.error('Failed to delete recipe');
					console.error('Delete failed:', err);
				}
			}
		});
	}

	function handleFavoriteRecipe(e: CustomEvent) {
		const recipe = e.detail as RecipeSummary;
		// TODO: Implement favorites
		console.log('Favorite:', recipe);
	}

	// Toggle view mode
	function toggleViewMode(mode: ViewMode) {
		viewMode = mode;
		if (browser) {
			localStorage.setItem('recipe-view-mode', mode);
		}
	}

	// Handle filter changes
	function handleFilterChange(e: CustomEvent) {
		const filters = e.detail;
		selectedCuisines = filters.selectedCuisines;
		selectedCategories = filters.selectedCategories;
		selectedSourceTypes = filters.selectedSourceTypes;
		maxTime = filters.maxTime;
		minTime = filters.minTime;
		searchParams.page = DEFAULT_PAGE; // Reset to first page when filters change
		loadRecipes();
	}

	// Initialize
	onMount(() => {
		// Restore view mode from localStorage
		if (browser) {
			const savedViewMode = localStorage.getItem('recipe-view-mode');
			if (savedViewMode === 'grid' || savedViewMode === 'list') {
				viewMode = savedViewMode;
			}
		}

		loadRecipes();
	});
</script>

<svelte:head>
	<title>My Recipes - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	<!-- Header -->
	<div class="sticky top-16 z-40 bg-white border-b border-neutral-200">
		<div class="container-custom py-4">
			<!-- Top row: Title and View toggle -->
			<div class="flex items-center justify-between mb-4">
				<h1 class="text-3xl font-bold" style="color: var(--text-900);">My Recipes</h1>

				<div class="flex items-center gap-2">
					<button
						on:click={() => goto('/import')}
						class="import-btn flex items-center gap-2"
						aria-label="Import recipes"
					>
						<Download size={16} aria-hidden="true" />
						<span>Import</span>
					</button>
					<button
						on:click={() => (showCollections = !showCollections)}
						class="filter-toggle-btn flex items-center gap-2"
						aria-label={showCollections ? 'Hide collections' : 'Show collections'}
					>
						<Folder size={16} aria-hidden="true" />
						<span>{showCollections ? 'Hide' : 'Show'} Collections</span>
					</button>
					<button
						on:click={() => (showFilters = !showFilters)}
						class="filter-toggle-btn flex items-center gap-2"
						aria-label={showFilters ? 'Hide filters' : 'Show filters'}
					>
						<Search size={16} aria-hidden="true" />
						<span>{showFilters ? 'Hide' : 'Show'} Filters</span>
					</button>
					<button
						on:click={() => toggleViewMode('grid')}
						class="view-btn"
						class:active={viewMode === 'grid'}
						aria-label="Grid view"
					>
						<Grid size={20} aria-hidden="true" />
					</button>
					<button
						on:click={() => toggleViewMode('list')}
						class="view-btn"
						class:active={viewMode === 'list'}
						aria-label="List view"
					>
						<List size={20} aria-hidden="true" />
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
			<!-- Sidebar (Collections + Filters) -->
			{#if showCollections || showFilters}
				<div class="sidebar-column">
					{#if showCollections}
						<div class="mb-6">
							<CollectionsSidebar />
						</div>
					{/if}

					{#if showFilters}
						<FilterSidebar
							bind:selectedCuisines
							bind:selectedCategories
							bind:selectedSourceTypes
							bind:maxTime
							bind:minTime
							on:change={handleFilterChange}
						/>
					{/if}
				</div>
			{/if}

			<!-- Recipes Column -->
			<div class="recipes-column">
		{#if loading}
			<!-- Loading state -->
			<div class="text-center py-16">
				<div class="flex justify-center mb-4" style="color: var(--text-400);">
					<Loader2 size={48} class="animate-spin" aria-hidden="true" />
				</div>
				<p class="text-lg" style="color: var(--text-600);">Loading recipes...</p>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="text-center py-16">
				<div class="flex justify-center mb-4" style="color: var(--error-500);">
					<AlertCircle size={48} aria-hidden="true" />
				</div>
				<p class="text-lg mb-2" style="color: var(--text-900);">Failed to load recipes</p>
				<p class="text-sm mb-4" style="color: var(--text-600);">{error}</p>
				<button on:click={loadRecipes} class="btn btn-primary">Try Again</button>
			</div>
		{:else if searchResult && searchResult.recipes.length === 0}
			<!-- Empty state -->
			<div class="text-center py-16">
				<div class="flex justify-center mb-4" style="color: var(--text-400);">
					<UtensilsCrossed size={64} aria-hidden="true" />
				</div>
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
					<button on:click={() => goto('/import')} class="btn btn-secondary flex items-center gap-2">
						<Download size={16} aria-hidden="true" />
						<span>Import Recipes</span>
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
							onview={(r) => handleViewRecipe({ detail: r } as CustomEvent)}
							onedit={(r) => handleEditRecipe({ detail: r } as CustomEvent)}
							ondelete={(r) => handleDeleteRecipe({ detail: r } as CustomEvent)}
							onfavorite={(r) => handleFavoriteRecipe({ detail: r } as CustomEvent)}
						/>
					{/each}
				</div>
			{:else}
				<div class="recipe-list">
					{#each searchResult.recipes as recipe (recipe.id)}
						<RecipeListItem
							{recipe}
							onview={(r) => handleViewRecipe({ detail: r } as CustomEvent)}
							onedit={(r) => handleEditRecipe({ detail: r } as CustomEvent)}
							ondelete={(r) => handleDeleteRecipe({ detail: r } as CustomEvent)}
							onfavorite={(r) => handleFavoriteRecipe({ detail: r } as CustomEvent)}
						/>
					{/each}
				</div>
			{/if}

			<!-- Pagination -->
			{#if searchResult.total_pages > 1}
				<div class="flex justify-center items-center gap-2 mt-8">
				<button
					on:click={() => goToPage(searchParams.page! - 1)}
					disabled={!searchResult.has_prev}
						class="pagination-btn"
					>
						← Previous
					</button>

					<span class="text-sm" style="color: var(--text-600);">
						Page {searchParams.page} of {searchResult.total_pages}
					</span>

				<button
					on:click={() => goToPage(searchParams.page! + 1)}
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

	.sidebar-column {
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

		.sidebar-column {
			width: 100%;
			flex: 1;
		}
	}
</style>
