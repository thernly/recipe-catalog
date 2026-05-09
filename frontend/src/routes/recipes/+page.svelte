<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
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
	import { Download, Search, Folder, Grid, List, UtensilsCrossed, AlertCircle, Loader2, X, Clock } from 'lucide-svelte';
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

	// Update URL with current search params
	function updateURL() {
		if (!browser) return;

		const params = new URLSearchParams();

		if (searchParams.query) params.set('q', searchParams.query);
		if (searchParams.sort_by && searchParams.sort_by !== 'recently_added') params.set('sort', searchParams.sort_by);
		if (searchParams.page && searchParams.page > 1) params.set('page', searchParams.page.toString());
		if (selectedCuisines.length > 0) params.set('cuisine', selectedCuisines.join(','));
		if (selectedCategories.length > 0) params.set('category', selectedCategories.join(','));
		if (selectedSourceTypes.length > 0) params.set('source', selectedSourceTypes.join(','));
		if (maxTime) params.set('maxTime', maxTime.toString());
		if (minTime) params.set('minTime', minTime.toString());

		const newURL = params.toString() ? `/recipes?${params.toString()}` : '/recipes';
		window.history.replaceState({}, '', newURL);
	}

	// Load search params from URL
	function loadSearchParamsFromURL() {
		if (!browser) return;

		const urlParams = $page.url.searchParams;

		searchParams.query = urlParams.get('q') || '';
		searchParams.sort_by = (urlParams.get('sort') as RecipeSortBy) || 'recently_added';
		searchParams.page = parseInt(urlParams.get('page') || '1');

		const cuisineParam = urlParams.get('cuisine');
		if (cuisineParam) selectedCuisines = cuisineParam.split(',');

		const categoryParam = urlParams.get('category');
		if (categoryParam) selectedCategories = categoryParam.split(',');

		const sourceParam = urlParams.get('source');
		if (sourceParam) selectedSourceTypes = sourceParam.split(',');

		const maxTimeParam = urlParams.get('maxTime');
		if (maxTimeParam) maxTime = parseInt(maxTimeParam);

		const minTimeParam = urlParams.get('minTime');
		if (minTimeParam) minTime = parseInt(minTimeParam);
	}

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
			updateURL();
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
		// Preserve current search state by building URL from current filters
		const params = new URLSearchParams();
		if (searchParams.query) params.set('q', searchParams.query);
		if (searchParams.sort_by && searchParams.sort_by !== 'recently_added') params.set('sort', searchParams.sort_by);
		if (searchParams.page && searchParams.page > 1) params.set('page', searchParams.page.toString());
		if (selectedCuisines.length > 0) params.set('cuisine', selectedCuisines.join(','));
		if (selectedCategories.length > 0) params.set('category', selectedCategories.join(','));
		if (selectedSourceTypes.length > 0) params.set('source', selectedSourceTypes.join(','));
		if (maxTime) params.set('maxTime', maxTime.toString());
		if (minTime) params.set('minTime', minTime.toString());

		const searchString = params.toString();
		const currentUrl = searchString ? `/recipes?${searchString}` : '/recipes';
		const returnUrl = encodeURIComponent(currentUrl);
		goto(`/recipes/${recipe.id}?returnUrl=${returnUrl}`);
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

	// Clear individual filter
	function clearFilter(type: string, value?: string) {
		if (type === 'cuisine' && value) {
			selectedCuisines = selectedCuisines.filter(c => c !== value);
		} else if (type === 'category' && value) {
			selectedCategories = selectedCategories.filter(c => c !== value);
		} else if (type === 'source' && value) {
			selectedSourceTypes = selectedSourceTypes.filter(s => s !== value);
		} else if (type === 'time') {
			maxTime = undefined;
			minTime = undefined;
		} else if (type === 'search') {
			searchParams.query = '';
		}
		searchParams.page = DEFAULT_PAGE;
		loadRecipes();
	}

	// Clear all filters
	function clearAllFilters() {
		selectedCuisines = [];
		selectedCategories = [];
		selectedSourceTypes = [];
		maxTime = undefined;
		minTime = undefined;
		searchParams.query = '';
		searchParams.page = DEFAULT_PAGE;
		loadRecipes();
	}

	// Check if any filters are active
	$: hasActiveFilters = selectedCuisines.length > 0 ||
		selectedCategories.length > 0 ||
		selectedSourceTypes.length > 0 ||
		maxTime !== undefined ||
		minTime !== undefined ||
		searchParams.query !== '';

	// Watch for URL changes (e.g., browser back/forward)
	$: if (browser && $page.url) {
		loadSearchParamsFromURL();
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

			<!-- Active Filter Chips -->
			{#if hasActiveFilters}
				<div class="filter-chips-container">
					<div class="filter-chips">
						{#if searchParams.query}
							<button class="filter-chip" on:click={() => clearFilter('search')}>
								<Search size={14} aria-hidden="true" />
								<span>"{searchParams.query}"</span>
								<X size={14} aria-hidden="true" />
							</button>
						{/if}
						{#each selectedCuisines as cuisine}
							<button class="filter-chip" on:click={() => clearFilter('cuisine', cuisine)}>
								<span>{cuisine}</span>
								<X size={14} aria-hidden="true" />
							</button>
						{/each}
						{#each selectedCategories as category}
							<button class="filter-chip" on:click={() => clearFilter('category', category)}>
								<span>{category}</span>
								<X size={14} aria-hidden="true" />
							</button>
						{/each}
						{#each selectedSourceTypes as source}
							<button class="filter-chip" on:click={() => clearFilter('source', source)}>
								<span>{source === 'imported' ? 'Imported' : 'Manual Entry'}</span>
								<X size={14} aria-hidden="true" />
							</button>
						{/each}
						{#if maxTime !== undefined || minTime !== undefined}
							<button class="filter-chip" on:click={() => clearFilter('time')}>
								<Clock size={14} aria-hidden="true" />
								<span>
									{#if minTime && maxTime}
										{minTime}-{maxTime} min
									{:else if maxTime}
										Under {maxTime} min
									{:else if minTime}
										Over {minTime} min
									{/if}
								</span>
								<X size={14} aria-hidden="true" />
							</button>
						{/if}
					</div>
					<button class="clear-all-chips-btn" on:click={clearAllFilters}>
						Clear All
					</button>
				</div>
			{/if}

			<!-- Active count -->
			{#if searchResult}
				<p class="mt-3 text-sm" style="color: var(--text-600);">
					Showing {searchResult.recipes.length} of {searchResult.total} recipes
					{#if hasActiveFilters}
						<span style="color: var(--accent-600);">(filtered)</span>
					{/if}
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
			<!-- Skeleton loading state -->
			<div class="recipe-grid" role="status" aria-label="Loading recipes">
				{#each Array(8) as _, i}
					<div class="skeleton-card">
						<div class="skeleton-image"></div>
						<div class="skeleton-content">
							<div class="skeleton-title"></div>
							<div class="skeleton-meta">
								<div class="skeleton-tag"></div>
								<div class="skeleton-tag"></div>
							</div>
							<div class="skeleton-description"></div>
							<div class="skeleton-description short"></div>
						</div>
					</div>
				{/each}
			</div>
			<p class="sr-only">Loading recipes...</p>
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

	/* Filter Chips */
	.filter-chips-container {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid var(--neutral-200);
	}

	.filter-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		flex: 1;
	}

	.filter-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.375rem 0.625rem;
		background: var(--accent-100);
		border: 1px solid var(--accent-300);
		border-radius: var(--radius-full);
		font-size: 0.8125rem;
		font-weight: 500;
		color: var(--accent-800);
		cursor: pointer;
		transition: all var(--transition-fast);
		animation: chipAppear 0.2s ease-out;
	}

	.filter-chip:hover {
		background: var(--accent-200);
		border-color: var(--accent-400);
	}

	.filter-chip:focus {
		outline: none;
		box-shadow: 0 0 0 2px var(--accent-300);
	}

	@keyframes chipAppear {
		from {
			opacity: 0;
			transform: scale(0.8);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	.clear-all-chips-btn {
		padding: 0.375rem 0.75rem;
		background: transparent;
		border: 1px solid var(--neutral-300);
		border-radius: var(--radius-md);
		font-size: 0.8125rem;
		font-weight: 500;
		color: var(--text-600);
		cursor: pointer;
		transition: all var(--transition-fast);
		white-space: nowrap;
	}

	.clear-all-chips-btn:hover {
		background: var(--neutral-100);
		border-color: var(--neutral-400);
		color: var(--text-900);
	}

	/* Skeleton Loading */
	.skeleton-card {
		background: var(--neutral-white);
		border-radius: var(--radius-lg);
		overflow: hidden;
		box-shadow: var(--shadow-sm);
	}

	.skeleton-image {
		aspect-ratio: 4 / 3;
		background: linear-gradient(
			90deg,
			var(--neutral-100) 25%,
			var(--neutral-200) 50%,
			var(--neutral-100) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
	}

	.skeleton-content {
		padding: 1rem;
	}

	.skeleton-title {
		height: 1.5rem;
		width: 70%;
		background: linear-gradient(
			90deg,
			var(--neutral-100) 25%,
			var(--neutral-200) 50%,
			var(--neutral-100) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-sm);
		margin-bottom: 0.75rem;
	}

	.skeleton-meta {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.skeleton-tag {
		height: 1.25rem;
		width: 4rem;
		background: linear-gradient(
			90deg,
			var(--neutral-100) 25%,
			var(--neutral-200) 50%,
			var(--neutral-100) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-full);
	}

	.skeleton-description {
		height: 0.875rem;
		width: 100%;
		background: linear-gradient(
			90deg,
			var(--neutral-100) 25%,
			var(--neutral-200) 50%,
			var(--neutral-100) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-sm);
		margin-bottom: 0.5rem;
	}

	.skeleton-description.short {
		width: 60%;
	}

	@keyframes shimmer {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}
</style>
