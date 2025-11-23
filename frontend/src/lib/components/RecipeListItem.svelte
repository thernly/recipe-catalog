<script lang="ts">
	import type { RecipeSummary } from '$lib/api/recipes';

	export let recipe: RecipeSummary;
	export let onview: ((recipe: RecipeSummary) => void) | undefined = undefined;
	export let onedit: ((recipe: RecipeSummary) => void) | undefined = undefined;
	export let ondelete: ((recipe: RecipeSummary) => void) | undefined = undefined;
	export let onfavorite: ((recipe: RecipeSummary) => void) | undefined = undefined;

	function formatTime(minutes: number | undefined): string {
		if (!minutes) return '';
		if (minutes < 60) return `${minutes}min`;
		const hours = Math.floor(minutes / 60);
		const mins = minutes % 60;
		return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
	}

	function handleView() {
		onview?.(recipe);
	}

	function handleEdit() {
		onedit?.(recipe);
	}

	function handleDelete() {
		ondelete?.(recipe);
	}

	function handleFavorite() {
		onfavorite?.(recipe);
	}
</script>

<article class="recipe-list-item group">
	<div class="flex items-center gap-4 p-4">
		<!-- Thumbnail -->
		<button on:click={handleView} class="recipe-list-thumbnail flex-shrink-0">
			{#if recipe.recipe_data?.images?.[0]?.data}
				<img
					src="data:{recipe.recipe_data.images[0].mimeType};base64,{recipe.recipe_data.images[0].data}"
					alt={recipe.name}
					class="w-full h-full object-cover"
				/>
			{:else if recipe.image_url}
				<img src={recipe.image_url} alt={recipe.name} class="w-full h-full object-cover" />
			{:else}
				<div
					class="w-full h-full flex items-center justify-center text-3xl"
					style="background: var(--neutral-100);"
				>
					🍽️
				</div>
			{/if}
		</button>

		<!-- Content (clickable) -->
		<button on:click={handleView} class="flex-1 min-w-0 text-left">
			<h3 class="recipe-list-title">{recipe.name}</h3>
			{#if recipe.description}
				<p class="recipe-list-description">{recipe.description}</p>
			{/if}
			<div class="flex items-center gap-3 mt-2">
				{#if recipe.cuisine}
					<span class="text-sm font-medium" style="color: var(--accent-600);">
						{recipe.cuisine}
					</span>
				{/if}
				{#if recipe.category}
					<span class="text-sm" style="color: var(--text-500);">• {recipe.category}</span>
				{/if}
				{#if recipe.total_time_minutes}
					<span class="text-sm" style="color: var(--text-500);">
						• 🕐 {formatTime(recipe.total_time_minutes)}
					</span>
				{/if}
				<span class="text-xs" style="color: var(--text-500);">
					• {recipe.source_type === 'imported' ? '📥 Imported' : '✏️ Manual'}
				</span>
			</div>
		</button>

		<!-- Actions -->
		<div class="flex items-center gap-2 flex-shrink-0">
			<button
				on:click={handleFavorite}
				class="action-btn-small"
				title="Add to favorites"
			>
				⭐
			</button>
			<button on:click={handleEdit} class="action-btn-small" title="Edit recipe">
				✏️
			</button>
			<button
				on:click={handleDelete}
				class="action-btn-small"
				title="Delete recipe"
			>
				🗑️
			</button>
		</div>
	</div>
</article>

<style>
	.recipe-list-item {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
	}

	.recipe-list-item:hover {
		border-color: var(--neutral-300);
		box-shadow: var(--shadow-sm);
	}

	.recipe-list-thumbnail {
		width: 5rem;
		height: 5rem;
		border-radius: var(--radius-md);
		overflow: hidden;
		flex-shrink: 0;
		background: var(--neutral-100);
		border: none;
		padding: 0;
		cursor: pointer;
		transition: opacity var(--transition-fast);
	}

	.recipe-list-thumbnail:hover {
		opacity: 0.9;
	}

	.recipe-list-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-900);
		line-height: 1.4;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.recipe-list-description {
		font-size: 0.875rem;
		color: var(--text-600);
		line-height: 1.5;
		margin-top: 0.25rem;
		display: -webkit-box;
		-webkit-line-clamp: 1;
		line-clamp: 1;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.action-btn-small {
		width: 2rem;
		height: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
		opacity: 0;
	}

	.recipe-list-item:hover .action-btn-small {
		opacity: 1;
	}

	.action-btn-small:hover {
		background: var(--accent-50);
		border-color: var(--accent-300);
		transform: scale(1.1);
	}
</style>
