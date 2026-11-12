<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		getShoppingList,
		updateShoppingList,
		deleteShoppingList,
		archiveShoppingList,
		duplicateShoppingList,
		addShoppingListItem,
		updateShoppingListItem,
		deleteShoppingListItem,
		getCategories,
		createdByLabel,
		formatQuantityUnit,
		type ShoppingList,
		type ShoppingListItem,
		type ShoppingListItemCreate,
		type ShoppingListUpdate,
	} from '#lib/api/shopping-lists.js';
	import { dialog } from '#lib/stores/dialog.js';
	import { toast } from '#lib/stores/toast.js';
	import { auth } from '#lib/stores/auth.js';

	// Inline quantity/unit edit (no merging: merging happens only on add)
	let editingItemId: number | null = null;
	let editQuantity = '';
	let editUnit = '';

	function startEditQuantity(item: ShoppingListItem) {
		editingItemId = item.id;
		editQuantity = item.quantity ?? '';
		editUnit = item.unit ?? '';
	}

	async function saveQuantity(item: ShoppingListItem) {
		if (editingItemId !== item.id) return;
		editingItemId = null;
		const quantity = editQuantity.trim();
		const unit = editUnit.trim();
		if (quantity === (item.quantity ?? '') && unit === (item.unit ?? ''))
			return;
		try {
			// "" (not undefined) so clearing a field is saved
			await updateShoppingListItem(item.id, { quantity, unit });
			await loadShoppingList();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to update item');
		}
	}

	function handleQuantityFocusOut(event: FocusEvent, item: ShoppingListItem) {
		const form = event.currentTarget as HTMLElement;
		if (!form.contains(event.relatedTarget as Node | null))
			void saveQuantity(item);
	}

	let listId: number;
	let shoppingList: ShoppingList | null = null;
	let loading = true;
	let error: string | null = null;
	let categories: string[] = [];

	// Item management
	let newItemName = '';
	let newItemQuantity = '';
	let newItemUnit = '';
	let newItemCategory = '';
	let addingItem = false;

	// Edit mode
	let editingListName = false;
	let editedName = '';
	let editedDescription = '';

	// Filters and sorting
	let sortBy: 'order' | 'category' | 'checked' = 'order';
	let hideChecked = false;

	export let params: { id: string };
	$: listId = parseInt(params.id);
	// Reload whenever the id changes: SvelteKit reuses this component when
	// navigating list-to-list (e.g. after Duplicate), so onMount alone would
	// leave the old list on screen while actions target the new id.
	$: if (listId) void loadShoppingList();
	$: sortedItems = sortItems(shoppingList?.items || []);
	$: visibleItems = hideChecked
		? sortedItems.filter((item) => !item.checked)
		: sortedItems;

	function sortItems(items: ShoppingListItem[]): ShoppingListItem[] {
		const itemsCopy = [...items];

		if (sortBy === 'order') {
			return itemsCopy.sort((a, b) => a.display_order - b.display_order);
		} else if (sortBy === 'category') {
			return itemsCopy.sort((a, b) => {
				const catA = a.category || 'Uncategorized';
				const catB = b.category || 'Uncategorized';
				return catA.localeCompare(catB);
			});
		} else if (sortBy === 'checked') {
			return itemsCopy.sort((a, b) => Number(a.checked) - Number(b.checked));
		}

		return itemsCopy;
	}

	async function loadShoppingList() {
		loading = true;
		error = null;

		try {
			shoppingList = await getShoppingList(listId);
			editedName = shoppingList.name;
			editedDescription = shoppingList.description || '';
		} catch (err) {
			error =
				err instanceof Error ? err.message : 'Failed to load shopping list';
			console.error('Failed to load shopping list:', err);
		} finally {
			loading = false;
		}
	}

	async function loadCategories() {
		try {
			categories = await getCategories();
		} catch (err) {
			console.error('Failed to load categories:', err);
		}
	}

	async function handleAddItem() {
		if (!newItemName.trim()) return;

		addingItem = true;
		try {
			const data: ShoppingListItemCreate = {
				item_name: newItemName.trim(),
				quantity: newItemQuantity.trim() || undefined,
				unit: newItemUnit.trim() || undefined,
				category: newItemCategory || undefined,
			};

			await addShoppingListItem(listId, data);

			// Clear form
			newItemName = '';
			newItemQuantity = '';
			newItemUnit = '';
			newItemCategory = '';

			// Reload list
			await loadShoppingList();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to add item';
			console.error('Failed to add item:', err);
		} finally {
			addingItem = false;
		}
	}

	async function handleToggleChecked(item: ShoppingListItem) {
		try {
			await updateShoppingListItem(item.id, { checked: !item.checked });
			await loadShoppingList();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update item';
			console.error('Failed to update item:', err);
		}
	}

	async function handleDeleteItem(itemId: number) {
		dialog.show({
			title: 'Delete Item',
			message: 'Are you sure you want to delete this item?',
			onConfirm: async () => {
				try {
					await deleteShoppingListItem(itemId);
					toast.success('Item deleted successfully');
					await loadShoppingList();
				} catch (err) {
					error = err instanceof Error ? err.message : 'Failed to delete item';
					toast.error('Failed to delete item');
					console.error('Failed to delete item:', err);
				}
			},
		});
	}

	async function handleUpdateList() {
		if (!shoppingList || !editedName.trim()) return;

		try {
			const data: ShoppingListUpdate = {
				name: editedName.trim(),
				// "" (not undefined) so clearing the description is saved
				description: editedDescription.trim(),
			};

			await updateShoppingList(listId, data);
			editingListName = false;
			await loadShoppingList();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update list';
			console.error('Failed to update list:', err);
		}
	}

	async function handleArchiveList() {
		dialog.show({
			title: 'Archive List',
			message: 'Are you sure you want to archive this list?',
			onConfirm: async () => {
				try {
					await archiveShoppingList(listId);
					toast.success('List archived successfully');
					goto('/shopping-lists');
				} catch (err) {
					error = err instanceof Error ? err.message : 'Failed to archive list';
					toast.error('Failed to archive list');
					console.error('Failed to archive list:', err);
				}
			},
		});
	}

	async function handleDuplicateList() {
		try {
			const newList = await duplicateShoppingList(listId);
			goto(`/shopping-lists/${newList.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to duplicate list';
			console.error('Failed to duplicate list:', err);
		}
	}

	// One unchecked item per line: iOS Reminders splits pasted lines into items.
	async function handleShareList() {
		const text = sortedItems
			.filter((item) => !item.checked)
			.map((item) => {
				const qty = formatQuantityUnit(item.quantity, item.unit);
				return qty ? `${item.item_name} (${qty})` : item.item_name;
			})
			.join('\n');
		if (!text) {
			toast.error('No unchecked items to share');
			return;
		}
		try {
			if (navigator.share) {
				await navigator.share({ text });
			} else {
				await navigator.clipboard.writeText(text);
				toast.success('List copied to clipboard');
			}
		} catch (err) {
			if (err instanceof Error && err.name === 'AbortError') return;
			toast.error('Failed to share list');
		}
	}

	async function handleDeleteList() {
		dialog.show({
			title: 'Delete List',
			message:
				'Are you sure you want to delete this list? This action cannot be undone.',
			onConfirm: async () => {
				try {
					await deleteShoppingList(listId);
					toast.success('List deleted successfully');
					goto('/shopping-lists');
				} catch (err) {
					error = err instanceof Error ? err.message : 'Failed to delete list';
					toast.error('Failed to delete list');
					console.error('Failed to delete list:', err);
				}
			},
		});
	}

	onMount(loadCategories);
</script>

<svelte:head
	><title>{shoppingList?.name || 'Shopping List'} - Recipe Catalog</title
	></svelte:head
>

<div class="container mx-auto px-4 py-8 max-w-4xl">
	{#if error}
		<div
			class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4"
		>
			{error}
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div style="color: var(--text-600);">Loading shopping list...</div>
		</div>
	{:else if shoppingList}
		<!-- Header -->
		<div class="mb-6">
			<a
				href="/shopping-lists"
				class="text-blue-600 hover:underline mb-4 inline-block"
			>
				← Back to Lists
			</a>

			{#if editingListName}
				<div class="mb-4">
					<input
						type="text"
						bind:value={editedName}
						aria-label="List name"
						class="text-3xl font-bold w-full border-b-2 border-blue-600 focus:outline-none mb-2"
						style="background: var(--neutral-white); color: var(--text-900);"
					/>
					<textarea
						bind:value={editedDescription}
						aria-label="List description"
						class="w-full rounded px-3 py-2 mt-2"
						style="color: var(--text-600); border: 1px solid var(--neutral-300); background: var(--neutral-white);"
						rows="2"
						placeholder="Description (optional)"></textarea>
					<div class="flex gap-2 mt-2">
						<button
							on:click={handleUpdateList}
							class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
						>
							Save
						</button>
						<button
							on:click={() => {
								editingListName = false;
								editedName = shoppingList?.name || '';
								editedDescription = shoppingList?.description || '';
							}}
							class="px-3 py-1 rounded"
							style="background: var(--neutral-200); color: var(--text-900);"
						>
							Cancel
						</button>
					</div>
				</div>
			{:else}
				<div class="flex justify-between items-start mb-4">
					<div class="flex-1">
						<h1 class="text-3xl font-bold mb-2">{shoppingList.name}</h1>
						{#if shoppingList.description}
							<p style="color: var(--text-600);">{shoppingList.description}</p>
						{/if}
						<p class="text-sm mt-1" style="color: var(--text-600);">
							{createdByLabel(shoppingList, $auth.user?.id)}
						</p>
					</div>
					<button
						on:click={() => (editingListName = true)}
						class="text-blue-600 hover:underline text-sm"
						aria-label="Edit list"
					>
						Edit
					</button>
				</div>
			{/if}

			<!-- Actions -->
			<div class="flex gap-2 mb-4 flex-wrap">
				<button
					on:click={handleShareList}
					class="px-3 py-1 text-sm rounded"
					style="background: var(--neutral-100); color: var(--text-900);"
				>
					Share
				</button>
				<button
					on:click={handleDuplicateList}
					class="px-3 py-1 text-sm rounded"
					style="background: var(--neutral-100); color: var(--text-900);"
				>
					Duplicate
				</button>
				{#if shoppingList.status === 'active'}
					<button
						on:click={handleArchiveList}
						class="px-3 py-1 text-sm rounded"
						style="background: var(--neutral-100); color: var(--text-900);"
					>
						Archive
					</button>
				{/if}
				<button
					on:click={handleDeleteList}
					class="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded"
				>
					Delete
				</button>
			</div>

			<!-- Filters and sorting -->
			<div class="flex gap-4 items-center text-sm">
				<label class="flex items-center gap-2">
					<span>Sort by:</span>
					<select
						bind:value={sortBy}
						class="border border-gray-300 rounded px-2 py-1"
					>
						<option value="order">Order</option>
						<option value="category">Category</option>
						<option value="checked">Status</option>
					</select>
				</label>
				<label class="flex items-center gap-2">
					<input type="checkbox" bind:checked={hideChecked} />
					<span>Hide checked items</span>
				</label>
			</div>
		</div>

		<!-- Add item form -->
		<div class="rounded-lg p-4 mb-6" style="background: var(--neutral-100);">
			<h2 class="font-semibold mb-3">Add Item</h2>
			<form
				on:submit|preventDefault={handleAddItem}
				class="grid gap-3 md:grid-cols-5"
			>
				<div class="md:col-span-2">
					<input
						type="text"
						bind:value={newItemName}
						placeholder="Item name"
						aria-label="Item name"
						maxlength="255"
						class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
				<div>
					<input
						type="text"
						bind:value={newItemQuantity}
						placeholder="Quantity"
						aria-label="Quantity"
						maxlength="100"
						class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
				<div>
					<input
						type="text"
						bind:value={newItemUnit}
						placeholder="Unit (e.g. cup)"
						aria-label="Unit"
						maxlength="50"
						class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
				<div>
					<select
						bind:value={newItemCategory}
						class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						<option value="">Category</option>
						{#each categories as category (category)}
							<option value={category}>{category}</option>
						{/each}
					</select>
				</div>
				<div class="md:col-span-5">
					<button
						type="submit"
						class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded disabled:opacity-50"
						disabled={addingItem || !newItemName.trim()}
					>
						{addingItem ? 'Adding...' : 'Add Item'}
					</button>
				</div>
			</form>
		</div>

		<!-- Shopping list items -->
		{#if visibleItems.length === 0}
			<div class="text-center py-12 text-gray-600">
				{hideChecked && shoppingList.items.some((i) => i.checked)
					? 'All items are checked! Uncheck "Hide checked items" to see them.'
					: 'No items yet. Add your first item above.'}
			</div>
		{:else}
			<div class="space-y-2">
				{#each visibleItems as item (item.id)}
					<div
						class="flex items-center gap-3 p-3 border rounded-lg hover:shadow-sm transition-shadow"
						style="background: var(--neutral-white); border-color: var(--neutral-200); color: var(--text-900);"
					>
						<!-- Checkbox -->
						<input
							type="checkbox"
							checked={item.checked}
							on:change={() => handleToggleChecked(item)}
							class="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
						/>

						<!-- Item details -->
						<div
							class="flex-1"
							class:line-through={item.checked}
							style={item.checked ? 'color: var(--text-500);' : ''}
						>
							<div class="font-medium">{item.item_name}</div>
							<div class="text-sm" style="color: var(--text-600);">
								{#if editingItemId === item.id}
									<form
										class="inline-flex gap-2"
										on:submit|preventDefault={() => saveQuantity(item)}
										on:focusout={(e) => handleQuantityFocusOut(e, item)}
									>
										<!-- svelte-ignore a11y_autofocus -->
										<input
											bind:value={editQuantity}
											aria-label="Quantity for {item.item_name}"
											maxlength="100"
											autofocus
											on:keydown={(e) =>
												e.key === 'Escape' && (editingItemId = null)}
											class="w-20 px-2 py-0.5 border rounded"
											style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900);"
										/>
										<input
											bind:value={editUnit}
											aria-label="Unit for {item.item_name}"
											maxlength="50"
											on:keydown={(e) =>
												e.key === 'Escape' && (editingItemId = null)}
											class="w-24 px-2 py-0.5 border rounded"
											style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900);"
										/>
										<button type="submit" class="sr-only">Save quantity</button>
									</form>
								{:else}
									<button
										type="button"
										on:click={() => startEditQuantity(item)}
										aria-label="Quantity for {item.item_name}: {formatQuantityUnit(
											item.quantity,
											item.unit,
										) || 'none'}. Edit"
										class="underline decoration-dotted"
									>
										{formatQuantityUnit(item.quantity, item.unit) ||
											'Add quantity'}
									</button>
								{/if}
								{#if item.notes}
									<span class="ml-2 italic">{item.notes}</span>
								{/if}
								{#if item.category}
									<span class="ml-2 px-2 py-0.5 bg-gray-100 rounded text-xs">
										{item.category}
									</span>
								{/if}
							</div>
						</div>

						<!-- Delete button -->
						<button
							on:click={() => handleDeleteItem(item.id)}
							class="text-red-600 hover:text-red-800 p-1"
							aria-label="Delete item"
						>
							<svg
								class="w-5 h-5"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
								></path>
							</svg>
						</button>
					</div>
				{/each}
			</div>

			<!-- Summary -->
			<div class="mt-6 text-sm text-gray-600">
				{shoppingList.items.filter((i) => i.checked).length} of {shoppingList
					.items.length} items checked
			</div>
		{/if}
	{:else}
		<div class="text-center py-12">
			<p style="color: var(--text-600);">Shopping list not found.</p>
			<a
				href="/shopping-lists"
				class="text-blue-600 hover:underline mt-4 inline-block"
			>
				← Back to Lists
			</a>
		</div>
	{/if}
</div>
