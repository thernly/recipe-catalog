<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { collections } from '#lib/stores/collections.js';
	import {
		createCollection,
		updateCollection,
		deleteCollection,
		type CollectionCreate,
		type CollectionUpdate,
	} from '#lib/api/collections.js';
	import { getUserStats, type UserStats } from '#lib/api/users.js';
	import CollectionModal from './CollectionModal.svelte';
	import type { Collection } from '#lib/api/collections.js';
	import { auth } from '#lib/stores/auth.js';
	import { dialog } from '#lib/stores/dialog.js';
	import { toast } from '#lib/stores/toast.js';

	export let currentCollectionId: number | null = null;

	let showModal = false;
	let editingCollection: Collection | null = null;
	// eslint-disable-next-line @typescript-eslint/no-unused-vars -- written but not yet read by the template
	let deleting = false;
	let stats: UserStats | null = null;

	// Load collections and stats on mount. Always, even when already loaded:
	// the counts change while this sidebar is away (a recipe starred, added to a
	// collection or deleted on its own page), and a reload keeps the list on screen.
	onMount(() => {
		collections.load();
		loadStats();
	});

	async function loadStats() {
		try {
			stats = await getUserStats();
		} catch (err) {
			console.error('Failed to load stats:', err);
		}
	}

	function openCreateModal() {
		editingCollection = null;
		showModal = true;
	}

	function openEditModal(collection: Collection) {
		editingCollection = collection;
		showModal = true;
	}

	async function handleModalSubmit(event: CustomEvent) {
		const data = event.detail;

		try {
			if (editingCollection) {
				// Update existing collection
				await updateCollection(editingCollection.id, data as CollectionUpdate);
				toast.success('Collection updated successfully');
			} else {
				// Create new collection
				await createCollection(data as CollectionCreate);
				toast.success('Collection created successfully');
			}

			// Reload collections and stats to get updated counts
			await Promise.all([collections.load(), loadStats()]);

			showModal = false;
			editingCollection = null;
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : 'Failed to save collection',
			);
			console.error('Failed to save collection:', err);
		}
	}

	function handleModalCancel() {
		showModal = false;
		editingCollection = null;
	}

	async function handleDeleteCollection(collection: Collection) {
		if (collection.is_default) {
			toast.error('Cannot delete default collections');
			return;
		}

		dialog.show({
			title: 'Delete Collection',
			message: `Are you sure you want to delete "${collection.name}"? Recipes will not be deleted.`,
			onConfirm: async () => {
				deleting = true;
				try {
					await deleteCollection(collection.id);
					collections.remove(collection.id);
					await loadStats(); // Reload stats after deletion
					toast.success('Collection deleted successfully');

					// Navigate away if we're viewing this collection
					if (currentCollectionId === collection.id) {
						goto('/recipes');
					}
				} catch (err) {
					toast.error(
						err instanceof Error ? err.message : 'Failed to delete collection',
					);
					console.error('Failed to delete collection:', err);
				} finally {
					deleting = false;
				}
			},
		});
	}

	// The household's collections are all listed, but only your own can be changed.
	// Everyone has a "Favorites"; yours goes under Quick Access, the others below.
	$: myId = $auth.user?.id;
	$: quickAccess = $collections.collections.filter(
		(c) => c.is_default && c.user_id === myId,
	);
	$: otherCollections = $collections.collections.filter(
		(c) => !c.is_default || c.user_id !== myId,
	);

	function isActive(collectionId: number | null): boolean {
		return currentCollectionId === collectionId;
	}
</script>

<aside class="collections-sidebar">
	<div class="sidebar-header">
		<h2 class="sidebar-title">Collections</h2>
		<button
			on:click={openCreateModal}
			class="btn-icon"
			title="New Collection"
			aria-label="Create new collection"
		>
			+
		</button>
	</div>

	{#if $collections.loading}
		<div class="sidebar-loading">
			<p class="text-sm" style="color: var(--text-600);">Loading...</p>
		</div>
	{:else if $collections.error}
		<div class="sidebar-error">
			<p class="text-sm" style="color: var(--color-error-text);">
				{$collections.error}
			</p>
			<button
				on:click={() => collections.load()}
				class="btn-sm btn-secondary mt-2"
			>
				Retry
			</button>
		</div>
	{:else}
		<nav class="collections-nav">
			<!-- Default Collections -->
			<div class="nav-section">
				<h3 class="nav-section-title">Quick Access</h3>
				<ul class="nav-list">
					<li>
						<button
							on:click={() => goto('/recipes')}
							class="nav-item"
							class:active={page.url.pathname === '/recipes' &&
								!currentCollectionId}
						>
							<span class="nav-icon">📚</span>
							<span class="nav-label">All Recipes</span>
							<span class="nav-count">
								{stats?.total_recipes ?? 0}
							</span>
						</button>
					</li>
					{#each quickAccess as collection (collection.id)}
						<li>
							<button
								on:click={() => goto(`/collections/${collection.id}`)}
								class="nav-item"
								class:active={isActive(collection.id)}
							>
								<span class="nav-icon">{collection.icon || '⭐'}</span>
								<span class="nav-label">{collection.name}</span>
								<span class="nav-count">{collection.recipe_count}</span>
							</button>
						</li>
					{/each}
				</ul>
			</div>

			<!-- Custom Collections -->
			{#if otherCollections.length > 0}
				<div class="nav-section">
					<h3 class="nav-section-title">Collections</h3>
					<ul class="nav-list">
						{#each otherCollections as collection (collection.id)}
							{@const mine = collection.user_id === myId}
							<li>
								<div class="nav-item-group">
									<button
										on:click={() => goto(`/collections/${collection.id}`)}
										class="nav-item"
										class:active={isActive(collection.id)}
									>
										<span class="nav-icon">{collection.icon || '📁'}</span>
										<span class="nav-label">
											{collection.name}{#if !mine && collection.creator_display_name}
												<span class="nav-owner">
													· {collection.creator_display_name}
												</span>{/if}
										</span>
										<span class="nav-count">{collection.recipe_count}</span>
									</button>
									{#if mine && !collection.is_default}
										<div class="nav-item-actions">
											<button
												on:click={() => openEditModal(collection)}
												class="action-btn"
												title="Edit collection"
												aria-label="Edit collection {collection.name}"
											>
												✏️
											</button>
											<button
												on:click={() => handleDeleteCollection(collection)}
												class="action-btn"
												title="Delete collection"
												aria-label="Delete collection {collection.name}"
											>
												🗑️
											</button>
										</div>
									{/if}
								</div>
							</li>
						{/each}
					</ul>
				</div>
			{/if}

			<!-- Trash -->
			<div class="nav-section">
				<ul class="nav-list">
					<li>
						<button
							on:click={() => goto('/recipes/trash')}
							class="nav-item"
							class:active={page.url.pathname === '/recipes/trash'}
						>
							<span class="nav-icon">🗑️</span>
							<span class="nav-label">Trash</span>
						</button>
					</li>
				</ul>
			</div>
		</nav>
	{/if}
</aside>

<CollectionModal
	bind:isOpen={showModal}
	collection={editingCollection}
	on:submit={handleModalSubmit}
	on:cancel={handleModalCancel}
/>

<style>
	.collections-sidebar {
		width: 100%;
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: sticky;
		top: 5.5rem;
		max-height: calc(100vh - 7rem);
	}

	.sidebar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1.5rem 1rem;
		border-bottom: 1px solid var(--neutral-200);
	}

	.sidebar-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-900);
	}

	.btn-icon {
		width: 2.75rem;
		height: 2.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-btn-primary-bg);
		color: var(--color-btn-primary-text);
		border: none;
		border-radius: var(--radius-md);
		font-size: 1.25rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-icon:hover {
		background: var(--accent-600);
		transform: scale(1.05);
	}

	.sidebar-loading,
	.sidebar-error {
		padding: 1rem;
		text-align: center;
	}

	.collections-nav {
		flex: 1;
		overflow-y: auto;
		padding: 0.5rem 0;
	}

	.nav-section {
		margin-bottom: 1.5rem;
	}

	.nav-section-title {
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--text-500);
		padding: 0.5rem 1rem;
		margin-bottom: 0.25rem;
	}

	.nav-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.nav-item-group {
		position: relative;
	}

	.nav-item {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.625rem 1rem;
		border: none;
		background: transparent;
		color: var(--text-700);
		font-size: 0.875rem;
		text-align: left;
		cursor: pointer;
		transition: all var(--transition-fast);
		border-left: 3px solid transparent;
	}

	.nav-item:hover {
		background: var(--neutral-100);
		color: var(--text-900);
	}

	.nav-item.active {
		background: var(--accent-50);
		color: var(--accent-800);
		border-left-color: var(--accent-500);
		font-weight: 500;
	}

	.nav-icon {
		font-size: 1.125rem;
		line-height: 1;
	}

	.nav-label {
		flex: 1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.nav-count {
		font-size: 0.75rem;
		color: var(--text-500);
		font-weight: 500;
	}

	.nav-item-actions {
		position: absolute;
		right: 0.5rem;
		top: 50%;
		transform: translateY(-50%);
		display: none;
		gap: 0.25rem;
		background: var(--neutral-50);
		padding: 0.25rem;
		border-radius: var(--radius-sm);
	}

	.nav-item-group:hover .nav-item-actions,
	.nav-item-group:focus-within .nav-item-actions {
		display: flex;
	}

	.action-btn {
		width: 2.75rem;
		height: 2.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-sm);
		font-size: 1rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.action-btn:hover {
		background: var(--accent-50);
		border-color: var(--accent-300);
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}

	.nav-owner {
		color: var(--text-500);
		font-weight: 400;
	}

	/* Below this width the recipes page stacks the sidebar above the list,
	   so it sits in the page flow instead of sticking beside it. */
	@media (max-width: 1024px) {
		.collections-sidebar {
			position: static;
			max-height: none;
		}
	}
</style>
