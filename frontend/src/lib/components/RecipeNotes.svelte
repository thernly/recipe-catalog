<script lang="ts">
	import { onMount } from 'svelte';
	import {
		listNotes,
		addNote,
		updateNote,
		deleteNote,
		type RecipeNote,
	} from '#lib/api/recipe-notes.js';
	import { dialog } from '#lib/stores/dialog.js';
	import { toast } from '#lib/stores/toast.js';

	export let recipeId: number;
	/** The recipe's owner may delete anyone's note on it */
	export let isRecipeOwner = false;

	const MAX_LENGTH = 10000;

	let notes: RecipeNote[] = [];
	let loading = true;
	let loadError = '';

	let newText = '';
	let adding = false;

	let editingId: number | null = null;
	let editText = '';
	let saving = false;

	async function loadNotes() {
		loading = true;
		loadError = '';
		try {
			notes = await listNotes(recipeId);
		} catch (err) {
			console.error('Failed to load notes:', err);
			loadError = 'Failed to load notes';
		} finally {
			loading = false;
		}
	}

	async function handleAdd() {
		const text = newText.trim();
		if (!text) return;
		adding = true;
		try {
			const note = await addNote(recipeId, text);
			notes = [note, ...notes];
			newText = '';
		} catch (err) {
			console.error('Failed to add note:', err);
			toast.error(err instanceof Error ? err.message : 'Failed to add note');
		} finally {
			adding = false;
		}
	}

	function startEdit(note: RecipeNote) {
		editingId = note.id;
		editText = note.text;
	}

	function cancelEdit() {
		editingId = null;
		editText = '';
	}

	async function saveEdit(note: RecipeNote) {
		const text = editText.trim();
		if (!text) return;
		saving = true;
		try {
			const updated = await updateNote(recipeId, note.id, text);
			notes = notes.map((n) => (n.id === updated.id ? updated : n));
			cancelEdit();
		} catch (err) {
			console.error('Failed to update note:', err);
			toast.error(err instanceof Error ? err.message : 'Failed to update note');
		} finally {
			saving = false;
		}
	}

	function handleDelete(note: RecipeNote) {
		dialog.show({
			title: 'Delete note',
			message: `Delete ${note.is_author ? 'your' : `${note.author_name}'s`} note? This cannot be undone.`,
			onConfirm: async () => {
				try {
					await deleteNote(recipeId, note.id);
					notes = notes.filter((n) => n.id !== note.id);
					toast.success('Note deleted');
				} catch (err) {
					console.error('Failed to delete note:', err);
					toast.error('Failed to delete note');
				}
			},
		});
	}

	function formatDateTime(value: string): string {
		return new Date(value).toLocaleString(undefined, {
			dateStyle: 'medium',
			timeStyle: 'short',
		});
	}

	onMount(loadNotes);
</script>

<section class="card mt-8" aria-labelledby="household-notes-heading">
	<h2
		id="household-notes-heading"
		class="text-xl font-semibold mb-3"
		style="color: var(--text-900);"
	>
		Household Notes
	</h2>

	{#if loading}
		<p class="note-muted">Loading notes...</p>
	{:else if loadError}
		<p class="note-error" role="alert">{loadError}</p>
	{:else if notes.length === 0}
		<p class="note-muted">No notes yet.</p>
	{:else}
		<ul class="note-list">
			{#each notes as note (note.id)}
				<li class="note-item">
					<p class="note-meta">
						<span class="note-author">{note.author_name}</span>
						·
						<time datetime={note.created_at}
							>{formatDateTime(note.created_at)}</time
						>
						{#if note.updated_at}
							<span title={`Edited ${formatDateTime(note.updated_at)}`}
								>(edited)</span
							>
						{/if}
					</p>

					{#if editingId === note.id}
						<div class="note-row">
							<label for="edit-note-{note.id}" class="sr-only">Edit note</label>
							<textarea
								id="edit-note-{note.id}"
								bind:value={editText}
								maxlength={MAX_LENGTH}
								rows="3"
								class="note-input"></textarea>
							<div class="note-actions">
								<button
									type="button"
									class="btn btn-primary btn-sm"
									disabled={saving || !editText.trim()}
									on:click={() => saveEdit(note)}
								>
									{saving ? 'Saving...' : 'Save'}
								</button>
								<button
									type="button"
									class="btn btn-outline btn-sm"
									on:click={cancelEdit}
								>
									Cancel
								</button>
							</div>
						</div>
					{:else}
						<div class="note-row">
							<p class="note-text">{note.text}</p>
							{#if note.is_author || isRecipeOwner}
								<div class="note-actions no-print">
									{#if note.is_author}
										<button
											type="button"
											class="btn btn-outline btn-sm"
											on:click={() => startEdit(note)}
										>
											Edit
										</button>
									{/if}
									<button
										type="button"
										class="btn btn-outline btn-danger btn-sm"
										on:click={() => handleDelete(note)}
									>
										Delete
									</button>
								</div>
							{/if}
						</div>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}

	<form on:submit|preventDefault={handleAdd} class="note-form no-print">
		<label for="new-note" class="sr-only">Add a note</label>
		<textarea
			id="new-note"
			bind:value={newText}
			maxlength={MAX_LENGTH}
			rows="2"
			placeholder="How did it go? e.g. Halved the sugar, still sweet enough"
			class="note-input"></textarea>
		<button
			type="submit"
			class="btn btn-primary"
			disabled={adding || !newText.trim()}
		>
			{adding ? 'Adding...' : 'Add note'}
		</button>
	</form>
</section>

<style>
	/* Text on the left, buttons top-aligned on the right; they wrap below on narrow screens */
	.note-form,
	.note-row {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-start;
		gap: 0.5rem 0.75rem;
	}

	.note-form {
		margin-top: 1.5rem;
	}

	.note-form > button,
	.note-actions {
		flex-shrink: 0;
	}

	/* Borders use --neutral-500: at least 3:1 against the card in every theme (WCAG 1.4.11) */
	.note-input {
		flex: 1 1 16rem;
		min-width: 0;
		padding: 0.75rem;
		border: 1px solid var(--neutral-500);
		border-radius: var(--radius-md);
		font-size: 1rem;
		color: var(--text-900);
		background: var(--neutral-white);
		resize: vertical;
	}

	.note-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.note-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.note-item {
		padding-top: 1rem;
		border-top: 1px solid var(--neutral-200);
	}

	.note-meta {
		font-size: 0.875rem;
		color: var(--text-500);
		margin: 0 0 0.25rem 0;
	}

	.note-author {
		font-weight: 600;
		color: var(--text-700);
	}

	.note-text {
		flex: 1 1 16rem;
		min-width: 0;
		color: var(--text-700);
		white-space: pre-line;
		overflow-wrap: anywhere;
		margin: 0;
	}

	.note-actions {
		display: flex;
		gap: 0.5rem;
	}

	.note-muted {
		font-size: 0.875rem;
		color: var(--text-500);
		margin: 0;
	}

	.note-error {
		font-size: 0.875rem;
		color: var(--error-700);
		margin: 0;
	}

	.btn-outline {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-500);
		color: var(--text-900);
	}

	.btn-outline:hover {
		background: var(--neutral-50);
		border-color: var(--neutral-600);
	}

	/* Destructive action: --error-700 is at least 6.8:1 on the card and on hover in every theme */
	.btn-danger,
	.btn-danger:hover {
		border-color: var(--error-700);
		color: var(--error-700);
	}

	.btn-danger:hover {
		background: var(--error-50);
	}

	.btn-sm {
		padding: 0.375rem 0.75rem;
		font-size: 0.875rem;
	}
</style>
