<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getTrashedRecipes, restoreRecipe, deleteRecipe, type RecipeSummary } from '$lib/api/recipes';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';

	let recipes: RecipeSummary[] = [];
	let loading = true;
	let error: string | null = null;

	async function loadTrashedRecipes() {
		loading = true;
		error = null;

		try {
			recipes = await getTrashedRecipes();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load trashed recipes';
			console.error('Failed to load trashed recipes:', err);
		} finally {
			loading = false;
		}
	}

	async function handleRestore(recipe: RecipeSummary) {
		try {
			await restoreRecipe(recipe.id);
			// Remove from list
			recipes = recipes.filter((r) => r.id !== recipe.id);

			// Show success message
			toast.success(`"${recipe.name}" has been restored`);
		} catch (err) {
			toast.error('Failed to restore recipe');
			console.error('Restore failed:', err);
		}
	}

	async function handlePermanentDelete(recipe: RecipeSummary) {
		dialog.show({
			title: 'Permanently Delete Recipe',
			message: `Are you sure you want to permanently delete "${recipe.name}"? This action cannot be undone.`,
			onConfirm: async () => {
				try {
					await deleteRecipe(recipe.id, true); // permanent = true
					// Remove from list
					recipes = recipes.filter((r) => r.id !== recipe.id);
					toast.success('Recipe permanently deleted');
				} catch (err) {
					toast.error('Failed to delete recipe');
					console.error('Delete failed:', err);
				}
			}
		});
	}

	async function handleEmptyTrash() {
		if (!recipes.length) return;

		dialog.show({
			title: 'Empty Trash',
			message: `Are you sure you want to permanently delete all ${recipes.length} recipes in trash? This action cannot be undone.`,
			onConfirm: async () => {
				try {
					// Delete all recipes
					await Promise.all(recipes.map((recipe) => deleteRecipe(recipe.id, true)));
					recipes = [];
					toast.success('Trash emptied successfully');
				} catch (err) {
					toast.error('Failed to empty trash');
					console.error('Empty trash failed:', err);
					// Reload to show what's left
					loadTrashedRecipes();
				}
			}
		});
	}

	function getDaysUntilPurge(deletedAt: string): number {
		const deleted = new Date(deletedAt);
		const purgeDate = new Date(deleted);
		purgeDate.setDate(purgeDate.getDate() + 30);

		const today = new Date();
		const diffTime = purgeDate.getTime() - today.getTime();
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		return Math.max(0, diffDays);
	}

	onMount(() => {
		loadTrashedRecipes();
	});
</script>

<svelte:head>
	<title>Trash - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	<!-- Header -->
	<div class="sticky top-0 z-40 bg-white border-b border-neutral-200">
		<div class="container-custom py-4">
			<button
				on:click={() => goto('/recipes')}
				class="text-sm mb-4 flex items-center gap-2"
				style="color: var(--text-600);"
			>
				← Back to Recipes
			</button>

			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-4xl font-bold mb-2" style="color: var(--text-900);">
						🗑️ Trash
					</h1>
					<p class="text-sm" style="color: var(--text-600);">
						Deleted recipes are kept for 30 days before permanent deletion
					</p>
				</div>

				{#if recipes.length > 0}
					<button on:click={handleEmptyTrash} class="btn btn-danger">
						Empty Trash ({recipes.length})
					</button>
				{/if}
			</div>
		</div>
	</div>

	<!-- Content -->
	<div class="container-custom py-8">
		{#if loading}
			<!-- Loading state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⏳</div>
				<p class="text-lg" style="color: var(--text-600);">Loading trashed recipes...</p>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⚠️</div>
				<p class="text-lg mb-2" style="color: var(--text-900);">Failed to load trash</p>
				<p class="text-sm mb-4" style="color: var(--text-600);">{error}</p>
				<button on:click={loadTrashedRecipes} class="btn btn-primary">Try Again</button>
			</div>
		{:else if recipes.length === 0}
			<!-- Empty state -->
			<div class="text-center py-16">
				<div class="text-6xl mb-4">✨</div>
				<h2 class="text-2xl font-semibold mb-2" style="color: var(--text-900);">
					Trash is empty
				</h2>
				<p class="text-lg mb-6" style="color: var(--text-600);">
					No deleted recipes to show
				</p>
				<button on:click={() => goto('/recipes')} class="btn btn-primary">
					Browse Recipes
				</button>
			</div>
		{:else}
			<!-- Trash items -->
			<div class="trash-list">
{#each recipes as recipe (recipe.id)}
				<article class="trash-item">
					<!-- Recipe info -->
					<div class="flex items-start gap-4 flex-1">
						{#if recipe.recipe_data?.images?.[0]?.data && recipe.recipe_data.images[0].data.trim()}
							<div class="trash-item-thumbnail">
								<img
									src="data:{recipe.recipe_data.images[0].mimeType};base64,{recipe.recipe_data.images[0].data}"
									alt={recipe.name}
									class="w-full h-full object-cover"
								/>
							</div>
						{:else if recipe.image_url}
							<div class="trash-item-thumbnail">
								<img src={recipe.image_url} alt={recipe.name} class="w-full h-full object-cover" />
							</div>
						{:else}
								<div class="trash-item-thumbnail">
									<div
										class="w-full h-full flex items-center justify-center text-3xl"
										style="background: var(--neutral-100);"
									>
										🍽️
									</div>
								</div>
							{/if}

							<div class="flex-1 min-w-0">
								<h3 class="trash-item-title">{recipe.name}</h3>
								{#if recipe.description}
									<p class="trash-item-description">{recipe.description}</p>
								{/if}

								<div class="flex items-center gap-3 mt-2 text-sm">
									{#if recipe.cuisine}
										<span style="color: var(--text-600);">{recipe.cuisine}</span>
									{/if}
									{#if recipe.category}
										<span style="color: var(--text-500);">• {recipe.category}</span>
									{/if}
								</div>

								<!-- Days until purge warning -->
								{#if recipe.deleted_at}
									{@const daysLeft = getDaysUntilPurge(recipe.deleted_at)}
									<div class="mt-3">
										{#if daysLeft > 7}
											<span class="trash-warning trash-warning-normal">
												Deletes in {daysLeft} days
											</span>
										{:else if daysLeft > 0}
											<span class="trash-warning trash-warning-soon">
												⚠️ Deletes in {daysLeft} {daysLeft === 1 ? 'day' : 'days'}
											</span>
										{:else}
											<span class="trash-warning trash-warning-urgent">
												🚨 Deletes soon
											</span>
										{/if}
									</div>
								{/if}
							</div>
						</div>

						<!-- Actions -->
						<div class="flex gap-2">
							<button on:click={() => handleRestore(recipe)} class="btn btn-primary btn-sm">
								↺ Restore
							</button>
							<button on:click={() => handlePermanentDelete(recipe)} class="btn btn-danger btn-sm">
								Delete Forever
							</button>
						</div>
					</article>
				{/each}
			</div>

			<!-- Info box -->
			<div class="mt-8 p-4 rounded-lg" style="background: var(--accent-50); color: var(--accent-800);">
				<p class="text-sm">
					<strong>ℹ️ Note:</strong> Recipes in trash will be automatically and permanently deleted after 30 days.
					You can restore them before then.
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.trash-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.trash-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1.5rem;
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		transition: all var(--transition-fast);
	}

	.trash-item:hover {
		border-color: var(--neutral-300);
		box-shadow: var(--shadow-sm);
	}

	.trash-item-thumbnail {
		width: 5rem;
		height: 5rem;
		border-radius: var(--radius-md);
		overflow: hidden;
		flex-shrink: 0;
		background: var(--neutral-100);
	}

	.trash-item-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-900);
		line-height: 1.4;
	}

	.trash-item-description {
		font-size: 0.875rem;
		color: var(--text-600);
		line-height: 1.5;
		margin-top: 0.25rem;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.trash-warning {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		border-radius: var(--radius-full);
		font-size: 0.75rem;
		font-weight: 500;
	}

	.trash-warning-normal {
		background: var(--neutral-100);
		color: var(--text-600);
	}

	.trash-warning-soon {
		background: #FEF3C7;
		color: #92400E;
	}

	.trash-warning-urgent {
		background: #FEE2E2;
		color: #991B1B;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
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

	@media (max-width: 640px) {
		.trash-item {
			flex-direction: column;
		}
	}
</style>
