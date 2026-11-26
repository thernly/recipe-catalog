<script lang="ts">
	/**
	 * "Collections" button for one recipe: lists the signed-in user's own
	 * collections with a tick box each, and adds or removes the recipe.
	 */
	import { Folder, Loader2 } from '@lucide/svelte';
	import {
		addRecipesToCollection,
		getCollectionIdsContaining,
		getCollections,
		removeRecipesFromCollection,
		type CollectionWithCount,
	} from '#lib/api/collections.js';
	import { auth } from '#lib/stores/auth.js';
	import { favorites } from '#lib/stores/favorites.js';
	import { toast } from '#lib/stores/toast.js';

	export let recipeId: number;

	let open = false;
	let loading = false;
	let collections: CollectionWithCount[] = [];
	let containing = new Set<number>();
	let busyId: number | null = null;

	async function toggleOpen() {
		open = !open;
		if (!open) return;
		loading = true;
		try {
			const [all, ids] = await Promise.all([
				getCollections(),
				getCollectionIdsContaining(recipeId),
			]);
			// Only your own collections can be changed
			collections = all.filter((c) => c.user_id === $auth.user?.id);
			containing = new Set(ids);
		} catch (err) {
			toast.error('Could not load your collections');
			console.error('Failed to load collections:', err);
			open = false;
		} finally {
			loading = false;
		}
	}

	async function toggle(collection: CollectionWithCount) {
		const add = !containing.has(collection.id);
		busyId = collection.id;
		try {
			if (add) await addRecipesToCollection(collection.id, [recipeId]);
			else await removeRecipesFromCollection(collection.id, [recipeId]);
			if (add) containing.add(collection.id);
			else containing.delete(collection.id);
			containing = containing;
			if (collection.is_default) await favorites.refresh();
		} catch (err) {
			toast.error(`Could not update "${collection.name}"`);
			console.error('Failed to update collection:', err);
		} finally {
			busyId = null;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') open = false;
	}
</script>

<div class="collections-menu" on:keydown={handleKeydown} role="presentation">
	<button
		type="button"
		class="btn btn-secondary flex items-center gap-2"
		aria-expanded={open}
		on:click={toggleOpen}
	>
		<Folder size={16} aria-hidden="true" />
		<span>Collections</span>
	</button>

	{#if open}
		<div class="collections-panel" role="group" aria-label="Collections">
			{#if loading}
				<p class="panel-note">
					<Loader2 size={14} class="animate-spin" aria-hidden="true" /> Loading...
				</p>
			{:else if collections.length === 0}
				<p class="panel-note">
					You have no collections yet. Create one from the Recipes page.
				</p>
			{:else}
				{#each collections as collection (collection.id)}
					<label class="panel-row">
						<input
							type="checkbox"
							checked={containing.has(collection.id)}
							disabled={busyId === collection.id}
							on:change={() => toggle(collection)}
						/>
						<span>{collection.icon || ''} {collection.name}</span>
					</label>
				{/each}
			{/if}
		</div>
	{/if}
</div>

<style>
	.collections-menu {
		position: relative;
	}

	.collections-panel {
		position: absolute;
		bottom: 100%;
		left: 0;
		margin-bottom: 0.5rem;
		min-width: 14rem;
		max-height: 16rem;
		overflow-y: auto;
		padding: 0.5rem;
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-md);
		z-index: 50;
	}

	/* Phones: open across the screen above the recipe page's button bar */
	@media (max-width: 768px) {
		.collections-menu {
			position: static;
		}

		.collections-panel {
			left: 1rem;
			right: 1rem;
			min-width: 0;
		}
	}

	.panel-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
		border-radius: var(--radius-sm);
		color: var(--text-900);
		cursor: pointer;
	}

	.panel-row:hover {
		background: var(--neutral-100);
	}

	.panel-note {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
		font-size: 0.875rem;
		color: var(--text-600);
	}
</style>
