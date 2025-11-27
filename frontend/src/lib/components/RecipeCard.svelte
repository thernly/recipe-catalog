<script lang="ts">
	import type { RecipeSummary } from '$lib/api/recipes';
	import { UtensilsCrossed, Clock, Star, Edit, Trash2, Download, PencilLine } from 'lucide-svelte';

	export let recipe: RecipeSummary;
	export let showActions: boolean = true;
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

<article class="recipe-card group">
	<button on:click={handleView} class="w-full text-left">
		<!-- Image -->
		<div class="recipe-card-image">
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
					<UtensilsCrossed size={64} aria-hidden="true" />
				</div>
			{/if}
		</div>

		<!-- Content -->
		<div class="p-4">
			<h3 class="recipe-card-title">{recipe.name}</h3>

			{#if recipe.description}
				<p class="recipe-card-description">{recipe.description}</p>
			{/if}

			<!-- Metadata -->
			<div class="flex flex-wrap gap-2 mt-3">
				{#if recipe.cuisine}
					<span class="badge">{recipe.cuisine}</span>
				{/if}
				{#if recipe.category}
					<span class="badge badge-secondary">{recipe.category}</span>
				{/if}
			</div>

			<div class="flex items-center justify-between mt-3">
				{#if recipe.total_time_minutes}
					<span class="text-sm flex items-center gap-1" style="color: var(--text-600);">
						<Clock size={14} aria-hidden="true" />
						<span>{formatTime(recipe.total_time_minutes)}</span>
					</span>
				{:else}
					<span></span>
				{/if}

				<span
					class="text-xs px-2 py-1 rounded flex items-center gap-1"
					style="background: var(--neutral-100); color: var(--text-600);"
				>
					{#if recipe.source_type === 'imported'}
						<Download size={12} aria-hidden="true" />
						<span>Imported</span>
					{:else}
						<PencilLine size={12} aria-hidden="true" />
						<span>Manual</span>
					{/if}
				</span>
			</div>
		</div>
	</button>

	<!-- Quick Actions (shown on hover) -->
	{#if showActions}
		<div class="recipe-card-actions">
			<button
				on:click|stopPropagation={handleFavorite}
				class="action-btn"
				aria-label="Add to favorites"
			>
				<Star size={16} aria-hidden="true" />
			</button>
			<button on:click|stopPropagation={handleEdit} class="action-btn" aria-label="Edit recipe">
				<Edit size={16} aria-hidden="true" />
			</button>
			<button on:click|stopPropagation={handleDelete} class="action-btn" aria-label="Delete recipe">
				<Trash2 size={16} aria-hidden="true" />
			</button>
		</div>
	{/if}
</article>

<style>
	.recipe-card {
		position: relative;
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		overflow: hidden;
		transition: all var(--transition-base);
	}

	.recipe-card:hover {
		box-shadow: var(--shadow-lg);
		transform: translateY(-2px);
		border-color: var(--neutral-300);
	}

	.recipe-card-image {
		aspect-ratio: 1;
		overflow: hidden;
		background: var(--neutral-100);
	}

	.recipe-card-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-900);
		margin-bottom: 0.5rem;
		line-height: 1.4;
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.recipe-card-description {
		font-size: 0.875rem;
		color: var(--text-600);
		line-height: 1.5;
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.recipe-card-actions {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		display: flex;
		gap: 0.25rem;
		opacity: 0;
		transition: opacity var(--transition-fast);
	}

	.recipe-card:hover .recipe-card-actions {
		opacity: 1;
	}

	.action-btn {
		width: 2rem;
		height: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(255, 255, 255, 0.95);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 1rem;
		cursor: pointer;
		transition: all var(--transition-fast);
		backdrop-filter: blur(4px);
	}

	.action-btn:hover {
		background: var(--accent-50);
		border-color: var(--accent-300);
		transform: scale(1.1);
	}

	.badge {
		display: inline-flex;
		align-items: center;
		padding: 0.25rem 0.75rem;
		background: var(--color-badge-bg);
		color: var(--color-badge-text);
		border-radius: var(--radius-full);
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}

	.badge-secondary {
		background: var(--neutral-100);
		color: var(--text-600);
	}
</style>
