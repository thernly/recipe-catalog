<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { collections } from '$lib/stores/collections';
	import {
		createCollection,
		updateCollection,
		deleteCollection,
		type CollectionCreate,
		type CollectionUpdate
	} from '$lib/api/collections';
	import { getUserStats, type UserStats } from '$lib/api/users';
	import CollectionModal from './CollectionModal.svelte';
	import type { Collection } from '$lib/api/collections';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';

	export let currentCollectionId: number | null = null;

	let showModal = false;
	let editingCollection: Collection | null = null;
	let deleting = false;
	let stats: UserStats | null = null;

	// Load collections and stats on mount
	onMount(() => {
		if (!$collections.loaded) {
			collections.load();
		}
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
			toast.error(err instanceof Error ? err.message : 'Failed to save collection');
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
					toast.error(err instanceof Error ? err.message : 'Failed to delete collection');
					console.error('Failed to delete collection:', err);
				} finally {
					deleting = false;
				}
			}
		});
	}

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
			<p class="text-sm" style="color: #EF4444;">{$collections.error}</p>
			<button on:click={() => collections.load()} class="btn-sm btn-secondary mt-2">
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
							class:active={$page.url.pathname === '/recipes' && !currentCollectionId}
						>
							<span class="nav-icon">📚</span>
							<span class="nav-label">All Recipes</span>
							<span class="nav-count">
								{stats?.total_recipes ?? 0}
							</span>
						</button>
					</li>
					{#each $collections.collections.filter((c) => c.is_default) as collection}
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
			{#if $collections.collections.filter((c) => !c.is_default).length > 0}
				<div class="nav-section">
					<h3 class="nav-section-title">My Collections</h3>
					<ul class="nav-list">
						{#each $collections.collections.filter((c) => !c.is_default) as collection}
							<li>
								<div class="nav-item-group">
									<button
										on:click={() => goto(`/collections/${collection.id}`)}
										class="nav-item"
										class:active={isActive(collection.id)}
									>
										<span class="nav-icon">{collection.icon || '📁'}</span>
										<span class="nav-label">{collection.name}</span>
										<span class="nav-count">{collection.recipe_count}</span>
									</button>
									<div class="nav-item-actions">
										<button
											on:click={() => openEditModal(collection)}
											class="action-btn"
											title="Edit collection"
										>
											✏️
										</button>
										<button
											on:click={() => handleDeleteCollection(collection)}
											class="action-btn"
											title="Delete collection"
										>
											🗑️
										</button>
									</div>
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
							class:active={$page.url.pathname === '/recipes/trash'}
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
		width: 2rem;
		height: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--accent-500);
		color: var(--neutral-white);
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

	.nav-item-group:hover .nav-item-actions {
		display: flex;
	}

	.action-btn {
		width: 1.75rem;
		height: 1.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-sm);
		font-size: 0.875rem;
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

	/* Mobile responsiveness */
	@media (max-width: 1024px) {
		.collections-sidebar {
			position: fixed;
			left: -260px;
			z-index: 100;
			transition: left 0.3s ease;
		}

		/* Unused: sidebar toggle not implemented yet */
		/* .collections-sidebar.open {
			left: 0;
		} */
	}
</style>
