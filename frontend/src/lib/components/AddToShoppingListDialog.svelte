<script lang="ts">
	import {
		listShoppingLists,
		getLastShoppingListId,
		type ShoppingListSummary,
	} from '#lib/api/shopping-lists.js';

	/** Whether the dialog is shown */
	export let open = false;
	export let heading = 'Add to shopping list';
	/** Offer "New list" as well as existing lists (off in pick-a-list mode) */
	export let allowNew = true;
	export let busy = false;
	/** Called with the chosen list id, or null for "New list" */
	export let onPick: (listId: number | null) => void;
	export let onClose: () => void;

	let lists: ShoppingListSummary[] = [];
	let loading = false;
	let error: string | null = null;
	let choice = '';

	$: if (open) void load();

	async function load() {
		loading = true;
		error = null;
		try {
			lists = await listShoppingLists('active');
			const last = getLastShoppingListId();
			const preferred = lists.find((l) => l.id === last) ?? lists[0];
			choice = preferred ? String(preferred.id) : allowNew ? 'new' : '';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load lists';
		} finally {
			loading = false;
		}
	}

	function submit() {
		if (!choice) return;
		onPick(choice === 'new' ? null : Number(choice));
	}
</script>

{#if open}
	<div
		class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
		role="presentation"
		on:keydown={(e) => e.key === 'Escape' && onClose()}
	>
		<div
			role="dialog"
			aria-modal="true"
			aria-labelledby="add-to-list-heading"
			class="rounded-lg shadow-xl max-w-md w-full p-6"
			style="background: var(--neutral-white); color: var(--text-900);"
		>
			<h2 id="add-to-list-heading" class="text-xl font-bold mb-4">{heading}</h2>
			<form on:submit|preventDefault={submit}>
				{#if loading}
					<p style="color: var(--text-600);">Loading lists...</p>
				{:else if error}
					<p role="alert" style="color: var(--text-900);">{error}</p>
				{:else}
					<fieldset class="mb-6 space-y-2 max-h-72 overflow-y-auto">
						<legend class="sr-only">Shopping list</legend>
						{#each lists as list (list.id)}
							<label class="flex items-center gap-2 cursor-pointer">
								<input
									type="radio"
									bind:group={choice}
									value={String(list.id)}
								/>
								<span>{list.name}</span>
								<span class="text-xs" style="color: var(--text-600);"
									>{list.item_count} items</span
								>
							</label>
						{/each}
						{#if allowNew}
							<label class="flex items-center gap-2 cursor-pointer">
								<input type="radio" bind:group={choice} value="new" />
								<span>New list</span>
							</label>
						{:else if lists.length === 0}
							<p style="color: var(--text-600);">
								No active lists. Create one from Shopping Lists first.
							</p>
						{/if}
					</fieldset>
				{/if}
				<div class="flex justify-end gap-3">
					<button
						type="button"
						on:click={onClose}
						class="px-4 py-2 rounded-lg"
						style="color: var(--text-900); background: var(--neutral-100); border: 1px solid var(--neutral-300);"
						disabled={busy}
					>
						Cancel
					</button>
					<button
						type="submit"
						class="px-4 py-2 text-white rounded-lg disabled:opacity-50"
						style="background: var(--accent-500);"
						disabled={busy || loading || !choice}
					>
						{busy ? 'Adding...' : 'Add'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
