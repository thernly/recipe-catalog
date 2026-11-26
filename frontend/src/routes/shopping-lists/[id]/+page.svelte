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
		groupByCategory,
		type ShoppingList,
		type ShoppingListItem,
		type ShoppingListItemCreate,
		type ShoppingListUpdate,
	} from '#lib/api/shopping-lists.js';
	import { dialog } from '#lib/stores/dialog.js';
	import { toast } from '#lib/stores/toast.js';
	import { auth } from '#lib/stores/auth.js';
	import { SHOPPING_LIST_REFRESH_INTERVAL } from '#lib/constants.js';

	// Inline quantity/unit/note edit (no merging: merging happens only on add)
	let editingItemId: number | null = null;
	let editQuantity = '';
	let editUnit = '';
	let editNotes = '';
	let editFocus: 'quantity' | 'notes' = 'quantity';

	function startEditQuantity(
		item: ShoppingListItem,
		focus: 'quantity' | 'notes' = 'quantity',
	) {
		editingItemId = item.id;
		editQuantity = item.quantity ?? '';
		editUnit = item.unit ?? '';
		editNotes = item.notes ?? '';
		editFocus = focus;
	}

	async function saveQuantity(item: ShoppingListItem) {
		if (editingItemId !== item.id) return;
		editingItemId = null;
		const quantity = editQuantity.trim();
		const unit = editUnit.trim();
		const notes = editNotes.trim();
		const notesChanged = notes !== (item.notes ?? '');
		if (
			quantity === (item.quantity ?? '') &&
			unit === (item.unit ?? '') &&
			!notesChanged
		)
			return;
		try {
			// "" (not undefined) so clearing a field is saved. The note is sent
			// only when it changed, so an untouched one is never overwritten.
			await updateShoppingListItem(item.id, {
				quantity,
				unit,
				...(notesChanged ? { notes } : {}),
			});
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
	// Both remembered in this browser, so they are still set on the next shopping trip
	const SORT_KEY = 'shopping-sort';
	let sortBy: 'order' | 'category' | 'checked' = readSort();
	const HIDE_CHECKED_KEY = 'shopping-hide-checked';
	let hideChecked = readHideChecked();

	// Grouped by store section unless this browser chose otherwise
	function readSort(): 'order' | 'category' | 'checked' {
		try {
			const saved = localStorage.getItem(SORT_KEY);
			return saved === 'order' || saved === 'checked' ? saved : 'category';
		} catch {
			return 'category';
		}
	}

	function saveSort(value: string) {
		try {
			localStorage.setItem(SORT_KEY, value);
		} catch {
			// storage unavailable
		}
	}

	$: saveSort(sortBy);

	function readHideChecked(): boolean {
		try {
			return localStorage.getItem(HIDE_CHECKED_KEY) === '1';
		} catch {
			return false; // storage unavailable: the choice just is not remembered
		}
	}

	function saveHideChecked(value: boolean) {
		try {
			if (value) localStorage.setItem(HIDE_CHECKED_KEY, '1');
			else localStorage.removeItem(HIDE_CHECKED_KEY);
		} catch {
			// storage unavailable
		}
	}

	$: saveHideChecked(hideChecked);

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
	// Section headings only when sorted by category; otherwise one unnamed group
	$: groups =
		sortBy === 'category'
			? groupByCategory(visibleItems, categories)
			: [{ category: '', items: visibleItems }];

	function sortItems(items: ShoppingListItem[]): ShoppingListItem[] {
		const itemsCopy = [...items];

		if (sortBy === 'order' || sortBy === 'category') {
			return itemsCopy.sort((a, b) => a.display_order - b.display_order);
		} else if (sortBy === 'checked') {
			return itemsCopy.sort((a, b) => Number(a.checked) - Number(b.checked));
		}

		return itemsCopy;
	}

	// Bumped by every local change, so a background refresh that was already
	// on its way (and so may predate the change) is dropped.
	let localChanges = 0;
	let pendingTicks = 0;

	// Another shopper's ticks and additions: refetch without the loading
	// screen, on a timer and on return to the tab. Never while this person is
	// typing, and failures are ignored (poor signal in a shop is normal).
	async function refreshQuietly() {
		const busy = () =>
			loading || editingListName || editingItemId !== null || pendingTicks > 0;
		if (document.hidden || !shoppingList || busy()) return;
		const seen = localChanges;
		try {
			const fresh = await getShoppingList(listId);
			if (seen === localChanges && fresh.id === listId && !busy())
				shoppingList = fresh;
		} catch {
			// keep what is on screen
		}
	}

	async function loadShoppingList() {
		localChanges++;
		// The loading screen is only for a list not yet on screen. A reload after
		// an add, edit or delete keeps the page, so scroll position and the
		// phone keyboard survive.
		loading = shoppingList?.id !== listId;
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

	function patchLocal(itemId: number, changes: Partial<ShoppingListItem>) {
		if (!shoppingList) return;
		shoppingList = {
			...shoppingList,
			items: shoppingList.items.map((i) =>
				i.id === itemId ? { ...i, ...changes } : i,
			),
		};
	}

	function setChecked(itemId: number, checked: boolean) {
		patchLocal(itemId, { checked });
	}

	// The standard categories, plus the item's own if it is not one of them
	function categoryOptions(item: ShoppingListItem, all: string[]): string[] {
		const current = item.category || 'Other';
		return all.includes(current) ? all : [...all, current];
	}

	// Optimistic, like a tick: the item moves to its new section at once and
	// moves back if the server refuses.
	async function handleCategoryChange(
		item: ShoppingListItem,
		category: string,
	) {
		patchLocal(item.id, { category });
		localChanges++;
		pendingTicks++;
		try {
			await updateShoppingListItem(item.id, { category });
		} catch (err) {
			patchLocal(item.id, { category: item.category });
			toast.error(err instanceof Error ? err.message : 'Failed to update item');
		} finally {
			pendingTicks--;
		}
	}

	// Optimistic: flip locally at once (no refetch, so a tap in the shop is
	// instant) and flip back if the server refuses.
	async function handleToggleChecked(item: ShoppingListItem) {
		const checked = !item.checked;
		setChecked(item.id, checked);
		localChanges++;
		pendingTicks++;
		try {
			await updateShoppingListItem(item.id, { checked });
		} catch (err) {
			setChecked(item.id, !checked);
			toast.error(err instanceof Error ? err.message : 'Failed to update item');
		} finally {
			pendingTicks--;
		}
	}

	async function handleUnarchiveList() {
		try {
			await updateShoppingList(listId, { status: 'active' });
			toast.success('List restored');
			await loadShoppingList();
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : 'Failed to restore list',
			);
		}
	}

	// No confirmation: one tap removes the item at once, and adding it back is
	// quick. It comes back by itself if the server refuses.
	async function handleDeleteItem(item: ShoppingListItem) {
		if (!shoppingList) return;
		shoppingList = {
			...shoppingList,
			items: shoppingList.items.filter((i) => i.id !== item.id),
		};
		localChanges++;
		pendingTicks++;
		try {
			await deleteShoppingListItem(item.id);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to delete item');
			await loadShoppingList();
		} finally {
			pendingTicks--;
		}
	}

	$: checkedItems = (shoppingList?.items ?? []).filter((i) => i.checked);

	async function handleUncheckAll() {
		const items = checkedItems;
		localChanges++;
		pendingTicks++;
		for (const item of items) setChecked(item.id, false);
		try {
			// One at a time: there is no bulk route, and lists are short
			for (const item of items)
				await updateShoppingListItem(item.id, { checked: false });
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : 'Failed to uncheck items',
			);
		} finally {
			pendingTicks--;
			await loadShoppingList();
		}
	}

	function handleRemoveChecked() {
		const items = checkedItems;
		dialog.show({
			title: 'Remove Checked Items',
			message: `Remove ${items.length} checked ${items.length === 1 ? 'item' : 'items'} from this list?`,
			onConfirm: async () => {
				try {
					for (const item of items) await deleteShoppingListItem(item.id);
					toast.success('Checked items removed');
				} catch (err) {
					toast.error(
						err instanceof Error ? err.message : 'Failed to remove items',
					);
				} finally {
					await loadShoppingList();
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
		// In the order on screen, so a shared list is grouped by section too
		const text = groups
			.flatMap((group) => group.items)
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

	onMount(() => {
		void loadCategories();
		const timer = setInterval(refreshQuietly, SHOPPING_LIST_REFRESH_INTERVAL);
		return () => clearInterval(timer);
	});
</script>

<svelte:document on:visibilitychange={refreshQuietly} />

<svelte:head>
	<title>{shoppingList?.name || 'Shopping List'} - Recipe Catalog</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-4xl">
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
			<div style="color: var(--text-600);">Loading shopping list...</div>
		</div>
	{:else if shoppingList}
		<!-- Header -->
		<div class="mb-6">
			<a
				href="/shopping-lists"
				class="hover:underline mb-4 inline-block"
				style="color: var(--primary-600);"
			>
				← Back to Lists
			</a>

			{#if editingListName}
				<div class="mb-4">
					<input
						type="text"
						bind:value={editedName}
						aria-label="List name"
						class="text-3xl font-bold w-full border-b-2 focus:outline-none mb-2"
						style="background: var(--neutral-white); color: var(--text-900); border-color: var(--primary-600);"
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
							class="btn-primary px-3 py-1 rounded"
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
						class="hover:underline text-sm"
						style="color: var(--primary-600);"
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
				{:else}
					<button
						on:click={handleUnarchiveList}
						class="px-3 py-1 text-sm rounded"
						style="background: var(--neutral-100); color: var(--text-900);"
					>
						Unarchive
					</button>
				{/if}
				<button
					on:click={handleDeleteList}
					class="px-3 py-1 text-sm rounded"
					style="background: var(--error-50); color: var(--error-700);"
				>
					Delete
				</button>
			</div>

			<!-- Filters and sorting -->
			<div class="flex flex-wrap gap-4 items-center text-sm">
				<label class="flex items-center gap-2">
					<span>Sort by:</span>
					<select
						bind:value={sortBy}
						class="border rounded px-2 py-1"
						style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900);"
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
				{#if checkedItems.length > 0}
					<button
						type="button"
						on:click={handleUncheckAll}
						class="px-3 py-1 rounded"
						style="background: var(--neutral-100); color: var(--text-900);"
					>
						Uncheck all
					</button>
					<button
						type="button"
						on:click={handleRemoveChecked}
						class="px-3 py-1 rounded"
						style="background: var(--neutral-100); color: var(--text-900);"
					>
						Remove checked
					</button>
				{/if}
			</div>
		</div>

		<!-- Add item form -->
		<div class="rounded-lg p-4 mb-6" style="background: var(--neutral-100);">
			<h2 class="text-lg font-semibold mb-3">Add Item</h2>
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
						class="add-field w-full px-3 py-2 border rounded"
					/>
				</div>
				<div>
					<input
						type="text"
						bind:value={newItemQuantity}
						placeholder="Quantity"
						aria-label="Quantity"
						maxlength="100"
						class="add-field w-full px-3 py-2 border rounded"
					/>
				</div>
				<div>
					<input
						type="text"
						bind:value={newItemUnit}
						placeholder="Unit (e.g. cup)"
						aria-label="Unit"
						maxlength="50"
						class="add-field w-full px-3 py-2 border rounded"
					/>
				</div>
				<div>
					<select
						bind:value={newItemCategory}
						class="add-field w-full px-3 py-2 border rounded"
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
						class="btn-primary w-full font-semibold py-2 px-4 rounded disabled:opacity-50"
						disabled={addingItem || !newItemName.trim()}
					>
						{addingItem ? 'Adding...' : 'Add Item'}
					</button>
				</div>
			</form>
		</div>

		<!-- Shopping list items -->
		{#if visibleItems.length === 0}
			<div class="text-center py-12" style="color: var(--text-600);">
				{hideChecked && shoppingList.items.some((i) => i.checked)
					? 'All items are checked! Uncheck "Hide checked items" to see them.'
					: 'No items yet. Add your first item above.'}
			</div>
		{:else}
			{#each groups as group (group.category)}
				{#if group.category}
					<h2
						class="text-lg font-semibold mt-6 mb-2"
						style="color: var(--text-700);"
					>
						{group.category}
					</h2>
				{/if}
				<div class="space-y-2">
					{#each group.items as item (item.id)}
						<div
							class="flex items-center gap-3 p-3 border rounded-lg hover:shadow-sm transition-shadow"
							style="background: var(--neutral-white); border-color: var(--neutral-200); color: var(--text-900);"
						>
							<!-- Checkbox: the label's padding fills the row's left edge, and
						     the item name is a second label, so both are tap targets -->
							<label
								class="flex items-center self-stretch -my-3 -ml-3 p-3 cursor-pointer"
							>
								<input
									id="item-check-{item.id}"
									type="checkbox"
									checked={item.checked}
									on:change={() => handleToggleChecked(item)}
									aria-label="Got {item.item_name}"
									class="w-5 h-5 rounded"
									style="accent-color: var(--primary-600);"
								/>
							</label>

							<!-- Item details -->
							<div
								class="flex-1"
								class:line-through={item.checked}
								style={item.checked ? 'color: var(--text-500);' : ''}
							>
								<label
									for="item-check-{item.id}"
									class="block font-medium cursor-pointer py-1"
								>
									{item.item_name}
								</label>
								<div class="text-sm" style="color: var(--text-600);">
									{#if editingItemId === item.id}
										<form
											class="inline-flex flex-wrap gap-2"
											on:submit|preventDefault={() => saveQuantity(item)}
											on:focusout={(e) => handleQuantityFocusOut(e, item)}
										>
											<!-- svelte-ignore a11y_autofocus -->
											<input
												bind:value={editQuantity}
												aria-label="Quantity for {item.item_name}"
												placeholder="Qty"
												maxlength="100"
												autofocus={editFocus === 'quantity'}
												on:keydown={(e) =>
													e.key === 'Escape' && (editingItemId = null)}
												class="w-20 px-2 py-0.5 border rounded"
												style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900);"
											/>
											<input
												bind:value={editUnit}
												aria-label="Unit for {item.item_name}"
												placeholder="Unit"
												maxlength="50"
												on:keydown={(e) =>
													e.key === 'Escape' && (editingItemId = null)}
												class="w-24 px-2 py-0.5 border rounded"
												style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900);"
											/>
											<!-- svelte-ignore a11y_autofocus -->
											<input
												bind:value={editNotes}
												aria-label="Note for {item.item_name}"
												placeholder="Note"
												maxlength="10000"
												autofocus={editFocus === 'notes'}
												on:keydown={(e) =>
													e.key === 'Escape' && (editingItemId = null)}
												class="w-48 px-2 py-0.5 border rounded"
												style="border-color: var(--neutral-300); background: var(--neutral-white); color: var(--text-900);"
											/>
											<button type="submit" class="sr-only">
												Save quantity
											</button>
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
										<!-- A row with no note gets one through the quantity
										     editor's Note box, so rows stay short in the shop -->
										{#if item.notes}
											<button
												type="button"
												on:click={() => startEditQuantity(item, 'notes')}
												aria-label="Note for {item.item_name}: {item.notes}. Edit"
												class="ml-2 italic text-left"
											>
												{item.notes}
											</button>
										{/if}
									{/if}
									<select
										value={item.category || 'Other'}
										on:change={(e) =>
											handleCategoryChange(item, e.currentTarget.value)}
										aria-label="Category for {item.item_name}"
										class="ml-2 px-1 py-0.5 rounded text-xs"
										style="background: var(--neutral-200); color: var(--text-900);"
									>
										{#each categoryOptions(item, categories) as category (category)}
											<option value={category}>{category}</option>
										{/each}
									</select>
								</div>
							</div>

							<!-- Delete button -->
							<button
								on:click={() => handleDeleteItem(item)}
								class="p-1"
								style="color: var(--error-600);"
								aria-label="Delete {item.item_name}"
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
			{/each}

			<!-- Summary -->
			<div class="mt-6 text-sm" style="color: var(--text-600);">
				{shoppingList.items.filter((i) => i.checked).length} of {shoppingList
					.items.length} items checked
			</div>
		{/if}
	{:else}
		<div class="text-center py-12">
			<p style="color: var(--text-600);">Shopping list not found.</p>
			<a
				href="/shopping-lists"
				class="hover:underline mt-4 inline-block"
				style="color: var(--primary-600);"
			>
				← Back to Lists
			</a>
		</div>
	{/if}
</div>

<style>
	.add-field {
		border-color: var(--neutral-300);
		background: var(--neutral-white);
		color: var(--text-900);
	}
	.add-field:focus {
		outline: 2px solid var(--primary-500);
		outline-offset: 1px;
	}
</style>
