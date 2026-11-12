<script lang="ts">
	import { goto } from '$app/navigation';
	import {
		listShoppingLists,
		createShoppingList,
		updateShoppingList,
		deleteShoppingList,
		createdByLabel,
		type ShoppingListSummary,
		type ShoppingListCreate,
	} from '#lib/api/shopping-lists.js';
	import { auth } from '#lib/stores/auth.js';
	import { dialog } from '#lib/stores/dialog.js';
	import { toast } from '#lib/stores/toast.js';

	// Inline rename state
	let renamingId: number | null = null;
	let renameValue = '';

	function startRename(list: ShoppingListSummary) {
		renamingId = list.id;
		renameValue = list.name;
	}

	async function saveRename(list: ShoppingListSummary) {
		const name = renameValue.trim();
		renamingId = null;
		if (!name || name === list.name) return;
		try {
			await updateShoppingList(list.id, { name });
			shoppingLists = shoppingLists.map((l) =>
				l.id === list.id ? { ...l, name } : l,
			);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to rename list');
		}
	}

	function confirmDelete(list: ShoppingListSummary) {
		dialog.show({
			title: 'Delete shopping list',
			message: `Delete "${list.name}" and all its items? This cannot be undone.`,
			onConfirm: async () => {
				try {
					await deleteShoppingList(list.id);
					shoppingLists = shoppingLists.filter((l) => l.id !== list.id);
					toast.success(`Deleted "${list.name}"`);
				} catch (err) {
					toast.error(
						err instanceof Error ? err.message : 'Failed to delete list',
					);
				}
			},
		});
	}

	let shoppingLists: ShoppingListSummary[] = [];
	let loading = true;
	let error: string | null = null;
	let statusFilter: 'active' | 'archived' | 'all' = 'active';

	async function unarchive(list: ShoppingListSummary) {
		try {
			await updateShoppingList(list.id, { status: 'active' });
			toast.success(`Restored "${list.name}"`);
			await loadShoppingLists();
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : 'Failed to restore list',
			);
		}
	}

	// Create dialog: native <dialog> gives the focus trap, Escape and focus return
	let createDialog: HTMLDialogElement;
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
			error =
				err instanceof Error ? err.message : 'Failed to load shopping lists';
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
				description: newListDescription.trim() || undefined,
			};

			const newList = await createShoppingList(data);
			createDialog.close();

			// Navigate to the new list
			goto(`/shopping-lists/${newList.id}`);
		} catch (err) {
			error =
				err instanceof Error ? err.message : 'Failed to create shopping list';
			console.error('Failed to create shopping list:', err);
		} finally {
			creating = false;
		}
	}

	function openCreateDialog() {
		newListName = '';
		newListDescription = '';
		createDialog.showModal();
	}

	// eslint-disable-next-line @typescript-eslint/no-unused-expressions -- lists reactive dependencies
	$: (statusFilter, loadShoppingLists());
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
				class="btn-primary font-semibold py-2 px-4 rounded-lg"
			>
				+ New List
			</button>
		</div>

		<!-- Filter tabs -->
		<div
			class="flex gap-2 mb-6 border-b"
			style="border-color: var(--neutral-200);"
		>
			<button
				on:click={() => (statusFilter = 'active')}
				class="px-4 py-2 font-medium border-b-2 transition-colors"
				style={statusFilter === 'active'
					? 'border-color: var(--accent-500); color: var(--accent-500);'
					: 'border-color: transparent; color: var(--text-600);'}
			>
				Active
			</button>
			<button
				on:click={() => (statusFilter = 'archived')}
				class="px-4 py-2 font-medium border-b-2 transition-colors"
				style={statusFilter === 'archived'
					? 'border-color: var(--accent-500); color: var(--accent-500);'
					: 'border-color: transparent; color: var(--text-600);'}
			>
				Archived
			</button>
			<button
				on:click={() => (statusFilter = 'all')}
				class="px-4 py-2 font-medium border-b-2 transition-colors"
				style={statusFilter === 'all'
					? 'border-color: var(--accent-500); color: var(--accent-500);'
					: 'border-color: transparent; color: var(--text-600);'}
			>
				All
			</button>
		</div>
	</div>

	{#if error}
		<div
			class="border px-4 py-3 rounded mb-4"
			style="background: var(--error-50); border-color: var(--error-200); color: var(--error-700);"
		>
			{error}
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div style="color: var(--text-600);">Loading shopping lists...</div>
		</div>
	{:else if shoppingLists.length === 0}
		<div class="text-center py-12">
			<p class="mb-4" style="color: var(--text-600);">
				No shopping lists found.
			</p>
			<button
				on:click={openCreateDialog}
				class="btn-primary font-semibold py-2 px-4 rounded-lg"
			>
				Create Your First List
			</button>
		</div>
	{:else}
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
			{#each shoppingLists as list (list.id)}
				<div
					class="flex flex-col rounded-lg shadow-sm border hover:shadow-md transition-shadow"
					style="background: var(--neutral-white); border-color: var(--neutral-200);"
				>
					<a href="/shopping-lists/{list.id}" class="block p-6 pb-3 grow">
						<h3
							class="text-lg font-semibold mb-2"
							style="color: var(--text-900);"
						>
							{list.name}
						</h3>

						{#if list.description}
							<p
								class="text-sm mb-3 line-clamp-2"
								style="color: var(--text-600);"
							>
								{list.description}
							</p>
						{/if}

						<div
							class="flex items-center gap-4 text-sm"
							style="color: var(--text-600);"
						>
							<div class="flex items-center gap-1">
								<svg
									class="w-4 h-4"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
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
									<svg
										class="w-4 h-4"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
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
								<span
									class="text-xs px-2 py-1 rounded"
									style="background: var(--neutral-100); color: var(--text-900);"
									>Archived</span
								>
							{/if}
						</div>

						<div class="text-xs mt-3" style="color: var(--text-600);">
							{createdByLabel(list, $auth.user?.id)} · {new Date(
								list.created_at,
							).toLocaleDateString()}
						</div>
					</a>
					<div class="flex items-center gap-2 px-6 pb-4">
						{#if renamingId === list.id}
							<form
								class="flex gap-2 w-full"
								on:submit|preventDefault={() => saveRename(list)}
							>
								<!-- svelte-ignore a11y_autofocus -->
								<input
									bind:value={renameValue}
									aria-label="New name for {list.name}"
									autofocus
									required
									maxlength="255"
									on:keydown={(e) => e.key === 'Escape' && (renamingId = null)}
									class="flex-1 px-2 py-1 border rounded"
									style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900);"
								/>
								<button
									type="submit"
									class="px-3 py-1 rounded text-white text-sm"
									style="background: var(--accent-500);">Save</button
								>
								<button
									type="button"
									on:click={() => (renamingId = null)}
									class="px-3 py-1 rounded text-sm"
									style="color: var(--text-900); background: var(--neutral-100);"
									>Cancel</button
								>
							</form>
						{:else}
							<button
								type="button"
								on:click={() => startRename(list)}
								aria-label="Rename {list.name}"
								class="px-3 py-1 rounded text-sm border"
								style="color: var(--text-900); background: var(--neutral-100); border-color: var(--neutral-300);"
								>Rename</button
							>
							{#if list.status === 'archived'}
								<button
									type="button"
									on:click={() => unarchive(list)}
									aria-label="Unarchive {list.name}"
									class="px-3 py-1 rounded text-sm border"
									style="color: var(--text-900); background: var(--neutral-100); border-color: var(--neutral-300);"
									>Unarchive</button
								>
							{/if}
							<button
								type="button"
								on:click={() => confirmDelete(list)}
								aria-label="Delete {list.name}"
								class="px-3 py-1 rounded text-sm border"
								style="color: var(--color-error-text); background: var(--neutral-100); border-color: var(--neutral-300);"
								>Delete</button
							>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Create List Dialog -->
<dialog
	bind:this={createDialog}
	aria-labelledby="create-list-title"
	class="create-dialog rounded-lg shadow-xl max-w-md w-full p-6"
>
	<h2
		id="create-list-title"
		class="text-2xl font-bold mb-4"
		style="color: var(--text-900);"
	>
		Create Shopping List
	</h2>

	<form on:submit|preventDefault={handleCreateList}>
		<div class="mb-4">
			<label
				for="name"
				class="block text-sm font-medium mb-1"
				style="color: var(--text-900);"
			>
				List Name <span style="color: var(--error-500);">*</span>
			</label>
			<input
				id="name"
				type="text"
				bind:value={newListName}
				required
				class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2"
				style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900); --tw-ring-color: var(--accent-500);"
				placeholder="e.g., Weekly Groceries"
			/>
		</div>

		<div class="mb-6">
			<label
				for="description"
				class="block text-sm font-medium mb-1"
				style="color: var(--text-900);"
			>
				Description (optional)
			</label>
			<textarea
				id="description"
				bind:value={newListDescription}
				rows="3"
				class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2"
				style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900); --tw-ring-color: var(--accent-500);"
				placeholder="Add any notes about this list..."></textarea>
		</div>
		<div class="flex justify-end gap-3">
			<button
				type="button"
				on:click={() => createDialog.close()}
				class="px-4 py-2 rounded-lg"
				style="color: var(--text-900); background: var(--neutral-100); border: 1px solid var(--neutral-300);"
				disabled={creating}
			>
				Cancel
			</button>
			<button
				type="submit"
				class="px-4 py-2 text-white rounded-lg disabled:opacity-50"
				style="background: var(--accent-500);"
				disabled={creating || !newListName.trim()}
			>
				{creating ? 'Creating...' : 'Create List'}
			</button>
		</div>
	</form>
</dialog>

<style>
	.create-dialog {
		margin: auto;
		border: 1px solid var(--neutral-300);
		background: var(--neutral-white);
	}
	.create-dialog::backdrop {
		background: rgba(0, 0, 0, 0.5);
	}
</style>
