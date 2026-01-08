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
				<div class="empty-image-placeholder">
					<span class="placeholder-initial">{recipe.name.charAt(0).toUpperCase()}</span>
					<UtensilsCrossed size={28} aria-hidden="true" class="placeholder-icon" />
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
		box-shadow: var(--shadow-warm-glow);
		transform: translateY(-4px);
		border-color: var(--accent-300);
	}

	.recipe-card-image {
		aspect-ratio: 4 / 3;
		overflow: hidden;
		background: var(--neutral-100);
	}

	.recipe-card-title {
		font-family: var(--font-display);
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text-900);
		margin-bottom: 0.5rem;
		line-height: 1.3;
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.recipe-card-description {
		font-size: 1rem;
		color: var(--text-600);
		line-height: 1.6;
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.recipe-card-actions {
		position: absolute;
		top: var(--space-sm);
		right: var(--space-sm);
		display: flex;
		gap: var(--space-xs);
		opacity: 0;
		transition: opacity var(--transition-fast);
	}

	.recipe-card:hover .recipe-card-actions {
		opacity: 1;
	}

	.action-btn {
		width: 2.75rem;
		height: 2.75rem;
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
		background: var(--accent-100);
		border-color: var(--accent-400);
		transform: scale(1.1);
		box-shadow: var(--shadow-md);
	}

	.badge {
		display: inline-flex;
		align-items: center;
		padding: 0.375rem 0.875rem;
		background: var(--accent-100);
		color: var(--accent-800);
		border-radius: var(--radius-full);
		font-family: var(--font-ui);
		font-size: 0.6875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.badge-secondary {
		background: var(--neutral-200);
		color: var(--text-700);
	}

	.empty-image-placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-sm);
		background: linear-gradient(135deg, var(--neutral-100) 0%, var(--neutral-200) 100%);
		color: var(--text-400);
		position: relative;
	}

	.empty-image-placeholder::before {
		content: '';
		position: absolute;
		inset: 0;
		background-image: radial-gradient(var(--neutral-300) 1px, transparent 1px);
		background-size: 16px 16px;
		opacity: 0.3;
	}

	.placeholder-initial {
		width: 3rem;
		height: 3rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--accent-100);
		color: var(--accent-700);
		border-radius: var(--radius-full);
		font-family: var(--font-display);
		font-size: 1.5rem;
		font-weight: 600;
		position: relative;
		z-index: 1;
	}

	.empty-image-placeholder :global(.placeholder-icon) {
		position: relative;
		z-index: 1;
		color: var(--text-400);
	}
</style>
