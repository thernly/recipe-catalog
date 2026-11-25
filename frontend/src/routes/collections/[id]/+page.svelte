<script lang="ts">
	import { downloadBlob } from '#lib/utils/download.js';
	import { onMount } from 'svelte';
	import { browser } from '$app/env';
	import { goto } from '$app/navigation';
	import {
		getCollection,
		getCollectionRecipes,
		exportCollectionPdf,
		type CollectionWithCount,
	} from '#lib/api/collections.js';
	import { deleteRecipe, type RecipeSummary } from '#lib/api/recipes.js';
	import type { ViewMode } from '#lib/types/index.js';
	import RecipeCard from '#lib/components/RecipeCard.svelte';
	import RecipeListItem from '#lib/components/RecipeListItem.svelte';
	import { dialog } from '#lib/stores/dialog.js';
	import { toast } from '#lib/stores/toast.js';

	let collection: CollectionWithCount | null = null;
	let recipes: RecipeSummary[] = [];
	let loading = true;
	let error: string | null = null;
	let viewMode: ViewMode = 'grid';
	let exportingPdf = false;

	export let params: { id: string };
	$: collectionId = parseInt(params.id);

	async function loadData() {
		loading = true;
		error = null;

		try {
			[collection, recipes] = await Promise.all([
				getCollection(collectionId),
				getCollectionRecipes(collectionId),
			]);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load collection';
			console.error('Failed to load collection:', err);
		} finally {
			loading = false;
		}
	}

	// Real links, so cmd-click opens a new tab; "Back" on the recipe returns here
	function recipeHref(recipe: RecipeSummary) {
		return `/recipes/${recipe.id}?returnUrl=${encodeURIComponent(`/collections/${collectionId}`)}`;
	}

	function handleEditRecipe(recipe: RecipeSummary) {
		goto(`/recipes/${recipe.id}/edit`);
	}

	function handleDeleteRecipe(recipe: RecipeSummary) {
		dialog.show({
			title: 'Delete Recipe',
			message: `Are you sure you want to delete "${recipe.name}"? It will be moved to trash.`,
			onConfirm: async () => {
				try {
					await deleteRecipe(recipe.id);
					toast.success('Recipe deleted successfully');
					// Reload the collection
					loadData();
				} catch (err) {
					toast.error('Failed to delete recipe');
					console.error('Delete failed:', err);
				}
			},
		});
	}

	function toggleViewMode(mode: ViewMode) {
		viewMode = mode;
		if (browser) {
			localStorage.setItem('recipe-view-mode', mode);
		}
	}

	async function handleExportPdf() {
		if (!collection) return;

		exportingPdf = true;
		try {
			const blob = await exportCollectionPdf(collection.id);

			// Generate filename
			const safeName = collection.name
				.replace(/[^a-z0-9]/gi, '_')
				.toLowerCase();
			const filename = `${safeName}.pdf`;

			// Create download
			downloadBlob(blob, filename);
		} catch (err) {
			toast.error(
				`Failed to export collection: ${err instanceof Error ? err.message : 'Unknown error'}`,
			);
			console.error('Export failed:', err);
		} finally {
			exportingPdf = false;
		}
	}

	onMount(() => {
		// Restore view mode
		if (browser) {
			const savedViewMode = localStorage.getItem('recipe-view-mode');
			if (savedViewMode === 'grid' || savedViewMode === 'list') {
				viewMode = savedViewMode;
			}
		}

		loadData();
	});
</script>

<svelte:head>
	<title>{collection?.name || 'Collection'} - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	{#if loading}
		<!-- Loading state -->
		<div class="container-custom py-16 text-center">
			<div class="text-4xl mb-4">⏳</div>
			<p class="text-lg" style="color: var(--text-600);">
				Loading collection...
			</p>
		</div>
	{:else if error || !collection}
		<!-- Error state -->
		<div class="container-custom py-16 text-center" role="alert">
			<div class="text-4xl mb-4" aria-hidden="true">⚠️</div>
			<p class="text-lg mb-2" style="color: var(--text-900);">
				Collection not found
			</p>
			<p class="text-sm mb-4" style="color: var(--text-600);">
				{error || 'This collection may have been deleted.'}
			</p>
			<button on:click={() => goto('/recipes')} class="btn btn-primary">
				Back to Recipes
			</button>
		</div>
	{:else}
		<!-- Header -->
		<div
			class="sticky top-0 z-40 border-b border-neutral-200"
			style="background: var(--neutral-white);"
		>
			<div class="container-custom py-4">
				<button
					on:click={() => goto('/recipes')}
					class="text-sm mb-4 flex items-center gap-2"
					style="color: var(--text-600);"
				>
					← Back to All Recipes
				</button>

				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						{#if collection.icon}
							<span class="text-4xl">{collection.icon}</span>
						{/if}
						<div>
							<h1 class="text-3xl font-bold" style="color: var(--text-900);">
								{collection.name}
							</h1>
							{#if collection.description}
								<p class="text-sm mt-1" style="color: var(--text-600);">
									{collection.description}
								</p>
							{/if}
							{#if collection.creator_display_name}
								<p class="text-xs mt-1" style="color: var(--text-500);">
									Created by {collection.creator_display_name}
								</p>
							{/if}
						</div>
					</div>

					<div class="flex items-center gap-2">
						<button
							on:click={handleExportPdf}
							class="btn btn-secondary"
							disabled={exportingPdf || recipes.length === 0}
							title="Export collection as PDF"
						>
							{exportingPdf ? '⏳' : '📄'} Export PDF
						</button>
						<button
							on:click={() => toggleViewMode('grid')}
							class="view-btn"
							class:active={viewMode === 'grid'}
							title="Grid view"
							aria-label="Grid view"
							aria-pressed={viewMode === 'grid'}
						>
							⊞
						</button>
						<button
							on:click={() => toggleViewMode('list')}
							class="view-btn"
							class:active={viewMode === 'list'}
							title="List view"
							aria-label="List view"
							aria-pressed={viewMode === 'list'}
						>
							≡
						</button>
					</div>
				</div>

				<p class="text-sm" style="color: var(--text-600);">
					{collection.recipe_count}
					{collection.recipe_count === 1 ? 'recipe' : 'recipes'}
				</p>
			</div>
		</div>

		<!-- Content -->
		<div class="container-custom py-8">
			{#if recipes.length === 0}
				<!-- Empty state -->
				<div class="text-center py-16">
					<div class="text-6xl mb-4">📭</div>
					<h2
						class="text-2xl font-semibold mb-2"
						style="color: var(--text-900);"
					>
						No recipes in this collection
					</h2>
					<p class="text-lg mb-6" style="color: var(--text-600);">
						Add recipes from your library to this collection
					</p>
					<button on:click={() => goto('/recipes')} class="btn btn-primary">
						Browse Recipes
					</button>
				</div>
			{:else if viewMode === 'grid'}
				<div class="recipe-grid">
					{#each recipes as recipe (recipe.id)}
						<RecipeCard
							{recipe}
							href={recipeHref(recipe)}
							onedit={handleEditRecipe}
							ondelete={handleDeleteRecipe}
						/>
					{/each}
				</div>
			{:else}
				<div class="recipe-list">
					{#each recipes as recipe (recipe.id)}
						<RecipeListItem
							{recipe}
							href={recipeHref(recipe)}
							onedit={handleEditRecipe}
							ondelete={handleDeleteRecipe}
						/>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
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
</style>
