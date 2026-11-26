<script lang="ts">
	import { onMount } from 'svelte';
	import { importRecipes, restoreBackup } from '#lib/api/recipes.js';
	import { RECIPE_SIPHON_URL } from '#lib/constants.js';
	import {
		summarizeImport,
		summarizeRestored,
		type ImportOutcome,
	} from '#lib/utils/import-summary.js';
	import { getCollections } from '#lib/api/collections.js';
	import type { Collection } from '#lib/api/collections.js';

	let loading = false;
	let error: string | null = null;
	let success: string | null = null;
	let fileInput: HTMLInputElement;
	let selectedFiles: File[] = [];
	let duplicateHandling: 'skip' | 'update' | 'create' = 'skip';
	let selectedCollectionId: number | undefined = undefined;
	let collections: Collection[] = [];
	let importProgress = { current: 0, total: 0 };

	// Load collections
	async function loadCollections() {
		try {
			collections = await getCollections();
		} catch (err) {
			console.error('Failed to load collections:', err);
		}
	}

	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		const files = target.files;

		if (!files || files.length === 0) {
			selectedFiles = [];
			return;
		}

		// Validate all files are JSON
		const validFiles: File[] = [];
		const invalidFiles: string[] = [];

		for (let i = 0; i < files.length; i++) {
			const file = files[i];
			if (file.type === 'application/json' || file.name.endsWith('.json')) {
				validFiles.push(file);
			} else {
				invalidFiles.push(file.name);
			}
		}

		if (invalidFiles.length > 0) {
			error = `Invalid files (not JSON): ${invalidFiles.join(', ')}`;
			if (validFiles.length === 0) {
				selectedFiles = [];
				target.value = '';
				return;
			}
		}

		selectedFiles = validFiles;
		error = null;
	}

	async function handleImport() {
		if (selectedFiles.length === 0) {
			error = 'Please select at least one file to import';
			return;
		}

		loading = true;
		error = null;
		success = null;
		importProgress = { current: 0, total: selectedFiles.length };

		try {
			const outcomes: ImportOutcome[] = [];

			// Import each file sequentially
			for (let i = 0; i < selectedFiles.length; i++) {
				const file = selectedFiles[i];
				importProgress.current = i + 1;

				try {
					const result = await importRecipes(
						file,
						duplicateHandling,
						selectedCollectionId,
					);
					outcomes.push({ file: file.name, result });
				} catch (err) {
					const errorMsg = err instanceof Error ? err.message : 'Unknown error';
					outcomes.push({ file: file.name, result: errorMsg });
					console.error(`Failed to import ${file.name}:`, err);
				}
			}

			// Say what happened to the recipes. The page stays put so the
			// details can be read; the result box links to the recipe list.
			const { summary, problems, imported } = summarizeImport(outcomes);
			if (problems.length > 0) {
				error = `These could not be imported:\n${problems.join('\n')}`;
			}
			// A green box only when something went right
			success = imported > 0 || problems.length === 0 ? summary : null;

			if (imported > 0) {
				selectedFiles = [];
				if (fileInput) {
					fileInput.value = '';
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to import recipes';
			console.error('Import failed:', err);
		} finally {
			loading = false;
			importProgress = { current: 0, total: 0 };
		}
	}

	// Restoring a Complete Backup
	let restoreFile: File | null = null;
	let restoreScope: 'everything' | 'recipes' = 'everything';
	let restoring = false;
	let restoreError: string | null = null;
	let restoreSuccess: string | null = null;

	async function handleRestore() {
		if (!restoreFile) return;
		restoring = true;
		restoreError = null;
		restoreSuccess = null;
		try {
			const result = await restoreBackup(restoreFile, restoreScope);
			const { summary, problems } = summarizeImport([
				{ file: restoreFile.name, result },
			]);
			if (problems.length > 0) {
				restoreError = `These could not be restored:\n${problems.join('\n')}`;
			}
			restoreSuccess = [summary, summarizeRestored(result.restored)]
				.filter(Boolean)
				.join('. ');
		} catch (err) {
			restoreError =
				err instanceof Error ? err.message : 'Failed to restore the backup';
		} finally {
			restoring = false;
		}
	}

	onMount(() => {
		loadCollections();
	});
</script>

<svelte:head>
	<title>Import Recipes - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	<div class="container-custom py-8">
		<div class="max-w-2xl mx-auto">
			<!-- Header -->
			<div class="mb-8">
				<h1 class="text-4xl font-bold mb-2" style="color: var(--text-900);">
					Import Recipes
				</h1>
				<p class="text-lg" style="color: var(--text-600);">
					Upload a JSON file containing recipes in Schema.org format
				</p>
			</div>

			<!-- Import Form -->
			<div class="card">
				<div class="mb-6">
					<h2
						class="text-xl font-semibold mb-4"
						style="color: var(--text-900);"
					>
						Upload JSON File
					</h2>

					<!-- File input -->
					<div class="mb-4">
						<label
							for="recipe-import-files"
							class="block mb-2 font-medium"
							style="color: var(--text-700);"
						>
							Select File(s)
						</label>
						<input
							id="recipe-import-files"
							type="file"
							accept="application/json,.json"
							multiple
							bind:this={fileInput}
							on:change={handleFileSelect}
							class="w-full px-4 py-2 border rounded-md"
							style="border-color: var(--neutral-300);"
							disabled={loading}
						/>
						{#if selectedFiles.length > 0}
							<div class="mt-2">
								<p
									class="text-sm font-medium mb-1"
									style="color: var(--text-600);"
								>
									Selected {selectedFiles.length} file{selectedFiles.length > 1
										? 's'
										: ''}:
								</p>
								<ul class="text-sm space-y-1" style="color: var(--text-600);">
									{#each selectedFiles.slice(0, 5) as file (file)}
										<li>• {file.name} ({Math.round(file.size / 1024)} KB)</li>
									{/each}
									{#if selectedFiles.length > 5}
										<li class="italic">
											... and {selectedFiles.length - 5} more
										</li>
									{/if}
								</ul>
							</div>
						{/if}
					</div>

					<!-- Duplicate handling -->
					<div class="mb-4">
						<label
							for="duplicate-handling"
							class="block mb-2 font-medium"
							style="color: var(--text-700);"
						>
							Duplicate Handling
						</label>
						<select
							id="duplicate-handling"
							bind:value={duplicateHandling}
							class="w-full px-4 py-2 border rounded-md"
							style="border-color: var(--neutral-300);"
							disabled={loading}
						>
							<option value="skip">Skip duplicates (keep existing)</option>
							<option value="update">
								Update duplicates (overwrite existing)
							</option>
							<option value="create">Create all (allow duplicates)</option>
						</select>
						<p class="mt-1 text-sm" style="color: var(--text-500);">
							Duplicates are detected by source web address or recipe name
						</p>
					</div>

					<!-- Collection selection (optional) -->
					<div class="mb-6">
						<label
							for="collection-select"
							class="block mb-2 font-medium"
							style="color: var(--text-700);"
						>
							Add to Collection (Optional)
						</label>
						<select
							id="collection-select"
							bind:value={selectedCollectionId}
							class="w-full px-4 py-2 border rounded-md"
							style="border-color: var(--neutral-300);"
							disabled={loading}
						>
							<option value={undefined}>No collection</option>
							{#each collections as collection (collection.id)}
								<option value={collection.id}>{collection.name}</option>
							{/each}
						</select>
					</div>

					<!-- Status messages -->
					{#if error}
						<div
							class="mb-4 p-4 border rounded-md"
							style="background: var(--color-error-bg); border-color: var(--color-error); color: var(--color-error-text);"
							role="alert"
						>
							<p class="whitespace-pre-line">{error}</p>
						</div>
					{/if}

					{#if success}
						<div
							class="mb-4 p-4 border rounded-md"
							style="background: var(--color-success-bg); border-color: var(--color-success); color: var(--color-success-text);"
							role="status"
						>
							<p>{success}</p>
							<p class="text-sm mt-1">
								<a href="/recipes" class="underline">View your recipes</a>
							</p>
						</div>
					{/if}

					<!-- Progress indicator -->
					{#if loading && importProgress.total > 0}
						<div
							class="mb-4 p-4 border rounded-md"
							style="background: var(--primary-50); border-color: var(--primary-200);"
							role="status"
						>
							<p style="color: var(--text-900);">
								Importing file {importProgress.current} of {importProgress.total}...
							</p>
							<div
								class="mt-2 w-full rounded-full h-2"
								style="background: var(--primary-200);"
							>
								<div
									class="h-2 rounded-full transition-all"
									style="background: var(--primary-500); width: {(importProgress.current /
										importProgress.total) *
										100}%"
								></div>
							</div>
						</div>
					{/if}

					<!-- Import button -->
					<button
						on:click={handleImport}
						disabled={selectedFiles.length === 0 || loading}
						class="btn btn-primary w-full"
					>
						{loading
							? 'Importing...'
							: selectedFiles.length > 1
								? `📥 Import ${selectedFiles.length} Files`
								: '📥 Import Recipes'}
					</button>
				</div>

				<!-- Instructions -->
				<div class="pt-6 border-t" style="border-color: var(--neutral-200);">
					<h3 class="font-semibold mb-2" style="color: var(--text-800);">
						File Format
					</h3>
					<p class="text-sm mb-2" style="color: var(--text-600);">
						Your JSON file should contain either:
					</p>
					<ul
						class="list-disc list-inside text-sm space-y-1"
						style="color: var(--text-600);"
					>
						<li>A single recipe object in Schema.org Recipe format</li>
						<li>An array of recipe objects in Schema.org Recipe format</li>
						<li>
							A recipes export (JSON) from this application. A Complete Backup
							file goes in the Restore box below instead
						</li>
					</ul>
					<p class="text-sm mt-3" style="color: var(--text-600);">
						You can export your existing recipes from the
						<a href="/export" class="text-primary-600 hover:underline">
							Export page
						</a>
						to see the expected format.
					</p>
				</div>
			</div>

			<!-- Restore a Complete Backup -->
			<div class="card mt-6">
				<h2 class="text-xl font-semibold mb-2" style="color: var(--text-900);">
					Restore a Complete Backup
				</h2>
				<p class="text-sm mb-4" style="color: var(--text-600);">
					Choose a Complete Backup file from the
					<a href="/export" class="text-primary-600 hover:underline">
						Export page
					</a>. Restoring only adds what is missing: anything already here is
					left as it is, so it is safe to run twice.
				</p>

				<div class="mb-4">
					<label
						for="restore-file"
						class="block mb-2 font-medium"
						style="color: var(--text-700);"
					>
						Backup file
					</label>
					<input
						id="restore-file"
						type="file"
						accept="application/json,.json"
						on:change={(e) =>
							(restoreFile = e.currentTarget.files?.[0] ?? null)}
						class="w-full px-4 py-2 border rounded-md"
						style="border-color: var(--neutral-300);"
						disabled={restoring}
					/>
				</div>

				<div class="mb-6">
					<label
						for="restore-scope"
						class="block mb-2 font-medium"
						style="color: var(--text-700);"
					>
						What to restore
					</label>
					<select
						id="restore-scope"
						bind:value={restoreScope}
						class="w-full px-4 py-2 border rounded-md"
						style="border-color: var(--neutral-300);"
						disabled={restoring}
					>
						<option value="everything">
							Everything (recipes, collections, meal plans, shopping lists)
						</option>
						<option value="recipes">Recipes only</option>
					</select>
				</div>

				{#if restoreError}
					<div
						class="mb-4 p-4 border rounded-md"
						style="background: var(--color-error-bg); border-color: var(--color-error); color: var(--color-error-text);"
						role="alert"
					>
						<p class="whitespace-pre-line">{restoreError}</p>
					</div>
				{/if}

				{#if restoreSuccess}
					<div
						class="mb-4 p-4 border rounded-md"
						style="background: var(--color-success-bg); border-color: var(--color-success); color: var(--color-success-text);"
						role="status"
					>
						<p>{restoreSuccess}</p>
					</div>
				{/if}

				<button
					on:click={handleRestore}
					disabled={!restoreFile || restoring}
					class="btn btn-primary w-full"
				>
					{restoring ? 'Restoring...' : 'Restore Backup'}
				</button>
			</div>

			<!-- Extension info -->
			<div class="card mt-6">
				<h3 class="text-lg font-semibold mb-2" style="color: var(--text-900);">
					Save recipes straight from websites
				</h3>
				<p class="text-sm mb-3" style="color: var(--text-600);">
					The Recipe Siphon browser extension sends the recipe on the page you
					are reading to your catalog.
				</p>
				<p class="text-sm" style="color: var(--text-600);">
					<a
						href={RECIPE_SIPHON_URL}
						target="_blank"
						rel="noopener noreferrer"
						class="text-primary-600 hover:underline"
					>
						Get Recipe Siphon
					</a>, then create a token for it under
					<a href="/settings" class="text-primary-600 hover:underline">
						Settings → API Tokens
					</a>.
				</p>
			</div>
		</div>
	</div>
</div>

<style>
	.card {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
		box-shadow: var(--shadow-sm);
	}

	.btn {
		padding: 0.75rem 1.5rem;
		border-radius: var(--radius-md);
		font-weight: 500;
		transition: all var(--transition-base);
		cursor: pointer;
		border: none;
	}

	.btn-primary {
		background: var(--color-btn-primary-bg);
		color: var(--color-btn-primary-text);
	}

	.btn-primary:hover:not(:disabled) {
		opacity: 0.9;
	}

	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
