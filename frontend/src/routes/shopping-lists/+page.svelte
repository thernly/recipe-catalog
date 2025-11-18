<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		listShoppingLists,
		createShoppingList,
		type ShoppingListSummary,
		type ShoppingListCreate
	} from '$lib/api/shopping-lists';

	let shoppingLists: ShoppingListSummary[] = [];
	let loading = true;
	let error: string | null = null;
	let statusFilter: 'active' | 'archived' | 'all' = 'active';

	// Create dialog state
	let showCreateDialog = false;
	let newListName = '';
	let newListDescription = '';
	let creating = false;

	async function loadShoppingLists() {
		loading = true;
		error = null;

		try {
			const filter = statusFilter === 'all' ? undefined : statusFilter;
			shoppingLists = await listShoppingLists(filter);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load shopping lists';
			console.error('Failed to load shopping lists:', err);
		} finally {
			loading = false;
		}
	}

	async function handleCreateList() {
		if (!newListName.trim()) return;

		creating = true;
		try {
			const data: ShoppingListCreate = {
				name: newListName.trim(),
				description: newListDescription.trim() || undefined
			};

			const newList = await createShoppingList(data);
			showCreateDialog = false;
			newListName = '';
			newListDescription = '';

			// Navigate to the new list
			goto(`/shopping-lists/${newList.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create shopping list';
			console.error('Failed to create shopping list:', err);
		} finally {
			creating = false;
		}
	}

	function openCreateDialog() {
		newListName = '';
		newListDescription = '';
		showCreateDialog = true;
	}

	function closeCreateDialog() {
		showCreateDialog = false;
		newListName = '';
		newListDescription = '';
	}

	$: {
		statusFilter;
		if (!loading) {
			loadShoppingLists();
		}
	}

	onMount(() => {
		loadShoppingLists();
	});
</script>

<svelte:head>
	<title>Shopping Lists - Recipe Catalog</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-6xl">
	<div class="mb-8">
		<div class="flex justify-between items-center mb-6">
			<h1 class="text-3xl font-bold">Shopping Lists</h1>
			<button
				on:click={openCreateDialog}
				class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg"
			>
				+ New List
			</button>
		</div>

		<!-- Filter tabs -->
		<div class="flex gap-2 mb-6 border-b border-gray-200">
			<button
				on:click={() => (statusFilter = 'active')}
				class="px-4 py-2 font-medium border-b-2 transition-colors {statusFilter === 'active'
					? 'border-blue-600 text-blue-600'
					: 'border-transparent text-gray-600 hover:text-gray-900'}"
			>
				Active
			</button>
			<button
				on:click={() => (statusFilter = 'archived')}
				class="px-4 py-2 font-medium border-b-2 transition-colors {statusFilter === 'archived'
					? 'border-blue-600 text-blue-600'
					: 'border-transparent text-gray-600 hover:text-gray-900'}"
			>
				Archived
			</button>
			<button
				on:click={() => (statusFilter = 'all')}
				class="px-4 py-2 font-medium border-b-2 transition-colors {statusFilter === 'all'
					? 'border-blue-600 text-blue-600'
					: 'border-transparent text-gray-600 hover:text-gray-900'}"
			>
				All
			</button>
		</div>
	</div>

	{#if error}
		<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
			{error}
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div class="text-gray-600">Loading shopping lists...</div>
		</div>
	{:else if shoppingLists.length === 0}
		<div class="text-center py-12">
			<p class="text-gray-600 mb-4">No shopping lists found.</p>
			<button
				on:click={openCreateDialog}
				class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg"
			>
				Create Your First List
			</button>
		</div>
	{:else}
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
			{#each shoppingLists as list}
				<a
					href="/shopping-lists/{list.id}"
					class="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6"
				>
					<h3 class="text-lg font-semibold mb-2 text-gray-900">{list.name}</h3>

					{#if list.description}
						<p class="text-sm text-gray-600 mb-3 line-clamp-2">{list.description}</p>
					{/if}

					<div class="flex items-center gap-4 text-sm text-gray-600">
						<div class="flex items-center gap-1">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
								/>
							</svg>
							<span>{list.item_count} items</span>
						</div>

						{#if list.item_count > 0}
							<div class="flex items-center gap-1">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M5 13l4 4L19 7"
									/>
								</svg>
								<span>{list.checked_count} checked</span>
							</div>
						{/if}

						{#if list.status === 'archived'}
							<span class="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">Archived</span>
						{/if}
					</div>

					<div class="text-xs text-gray-500 mt-3">
						Created {new Date(list.created_at).toLocaleDateString()}
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>

<!-- Create List Dialog -->
{#if showCreateDialog}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
		<div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
			<h2 class="text-2xl font-bold mb-4">Create Shopping List</h2>

			<form on:submit|preventDefault={handleCreateList}>
				<div class="mb-4">
					<label for="name" class="block text-sm font-medium text-gray-700 mb-1">
						List Name <span class="text-red-500">*</span>
					</label>
					<input
						id="name"
						type="text"
						bind:value={newListName}
						required
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						placeholder="e.g., Weekly Groceries"
					/>
				</div>

				<div class="mb-6">
					<label for="description" class="block text-sm font-medium text-gray-700 mb-1">
						Description (optional)
					</label>
					<textarea
						id="description"
						bind:value={newListDescription}
						rows="3"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						placeholder="Add any notes about this list..."
					/>
				</div>

				<div class="flex justify-end gap-3">
					<button
						type="button"
						on:click={closeCreateDialog}
						class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
						disabled={creating}
					>
						Cancel
					</button>
					<button
						type="submit"
						class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
						disabled={creating || !newListName.trim()}
					>
						{creating ? 'Creating...' : 'Create List'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
