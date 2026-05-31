<script lang="ts">
	import type { RecipeSummary } from '$lib/api/recipes';
	import { UtensilsCrossed, Clock, Star, Edit, Trash2, Download, PencilLine } from '@lucide/svelte';

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
		<button on:click={handleView} class="recipe-list-thumbnail shrink-0">
			{#if recipe.recipe_data?.images?.[0]?.data && recipe.recipe_data.images[0].data.trim()}
				<img
					src="data:{recipe.recipe_data.images[0].mimeType};base64,{recipe.recipe_data.images[0].data}"
					alt={recipe.name}
					class="w-full h-full object-cover"
				/>
			{:else if recipe.image_url}
				<img src={recipe.image_url} alt={recipe.name} class="w-full h-full object-cover" />
			{:else}
				<div
					class="w-full h-full flex items-center justify-center"
					style="background: var(--neutral-100); color: var(--text-400);"
				>
					<UtensilsCrossed size={32} aria-hidden="true" />
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
					<span class="text-sm flex items-center gap-1" style="color: var(--text-500);">
						<span>•</span>
						<Clock size={14} aria-hidden="true" />
						<span>{formatTime(recipe.total_time_minutes)}</span>
					</span>
				{/if}
				<span class="text-xs flex items-center gap-1" style="color: var(--text-500);">
					<span>•</span>
					{#if recipe.source_type === 'imported'}
						<Download size={12} aria-hidden="true" />
						<span>Imported</span>
					{:else}
						<PencilLine size={12} aria-hidden="true" />
						<span>Manual</span>
					{/if}
				</span>
			</div>
		</button>

		<!-- Actions -->
		<div class="flex items-center gap-2 shrink-0">
			<button
				on:click={handleFavorite}
				class="action-btn-small"
				aria-label="Add to favorites"
			>
				<Star size={16} aria-hidden="true" />
			</button>
			<button on:click={handleEdit} class="action-btn-small" aria-label="Edit recipe">
				<Edit size={16} aria-hidden="true" />
			</button>
			<button
				on:click={handleDelete}
				class="action-btn-small"
				aria-label="Delete recipe"
			>
				<Trash2 size={16} aria-hidden="true" />
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
