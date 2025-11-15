<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { importRecipes } from '$lib/api/recipes';
	import { getCollections } from '$lib/api/collections';
	import type { Collection } from '$lib/api/collections';
	import Navbar from '$lib/components/Navbar.svelte';

	let loading = false;
	let error: string | null = null;
	let success: string | null = null;
	let fileInput: HTMLInputElement;
	let selectedFile: File | null = null;
	let duplicateHandling: 'skip' | 'update' | 'create' = 'skip';
	let selectedCollectionId: number | undefined = undefined;
	let collections: Collection[] = [];

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
		const file = target.files?.[0];

		if (!file) {
			selectedFile = null;
			return;
		}

		if (file.type !== 'application/json' && !file.name.endsWith('.json')) {
			error = 'Please select a JSON file';
			selectedFile = null;
			target.value = '';
			return;
		}

		selectedFile = file;
		error = null;
	}

	async function handleImport() {
		if (!selectedFile) {
			error = 'Please select a file to import';
			return;
		}

		loading = true;
		error = null;
		success = null;

		try {
			const result = await importRecipes(selectedFile, duplicateHandling, selectedCollectionId);

			success = result.message;

			// Reset form
			selectedFile = null;
			if (fileInput) {
				fileInput.value = '';
			}

			// Show details if available
			if (result.details) {
				const details = result.details;
				console.log('Import details:', details);

				if (details.errors && details.errors.length > 0) {
					error = `Import completed with some errors. Check console for details.`;
				}
			}

			// Redirect to recipes page after 2 seconds
			setTimeout(() => {
				goto('/recipes');
			}, 2000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to import recipes';
			console.error('Import failed:', err);
		} finally {
			loading = false;
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
	<!-- Navbar -->
	<Navbar />

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
					<h2 class="text-xl font-semibold mb-4" style="color: var(--text-900);">
						Upload JSON File
					</h2>

					<!-- File input -->
					<div class="mb-4">
						<label class="block mb-2 font-medium" style="color: var(--text-700);">
							Select File
						</label>
						<input
							type="file"
							accept="application/json,.json"
							bind:this={fileInput}
							on:change={handleFileSelect}
							class="w-full px-4 py-2 border rounded-md"
							style="border-color: var(--neutral-300);"
							disabled={loading}
						/>
						{#if selectedFile}
							<p class="mt-2 text-sm" style="color: var(--text-600);">
								Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
							</p>
						{/if}
					</div>

					<!-- Duplicate handling -->
					<div class="mb-4">
						<label class="block mb-2 font-medium" style="color: var(--text-700);">
							Duplicate Handling
						</label>
						<select
							bind:value={duplicateHandling}
							class="w-full px-4 py-2 border rounded-md"
							style="border-color: var(--neutral-300);"
							disabled={loading}
						>
							<option value="skip">Skip duplicates (keep existing)</option>
							<option value="update">Update duplicates (overwrite existing)</option>
							<option value="create">Create all (allow duplicates)</option>
						</select>
						<p class="mt-1 text-sm" style="color: var(--text-500);">
							Duplicates are detected by recipe name
						</p>
					</div>

					<!-- Collection selection (optional) -->
					<div class="mb-6">
						<label class="block mb-2 font-medium" style="color: var(--text-700);">
							Add to Collection (Optional)
						</label>
						<select
							bind:value={selectedCollectionId}
							class="w-full px-4 py-2 border rounded-md"
							style="border-color: var(--neutral-300);"
							disabled={loading}
						>
							<option value={undefined}>No collection</option>
							{#each collections as collection}
								<option value={collection.id}>{collection.name}</option>
							{/each}
						</select>
					</div>

					<!-- Status messages -->
					{#if error}
						<div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
							<p class="text-red-800">{error}</p>
						</div>
					{/if}

					{#if success}
						<div class="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
							<p class="text-green-800">{success}</p>
							<p class="text-sm text-green-600 mt-1">Redirecting to recipes page...</p>
						</div>
					{/if}

					<!-- Import button -->
					<button
						on:click={handleImport}
						disabled={!selectedFile || loading}
						class="btn btn-primary w-full"
					>
						{loading ? 'Importing...' : '📥 Import Recipes'}
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
					<ul class="list-disc list-inside text-sm space-y-1" style="color: var(--text-600);">
						<li>A single recipe object in Schema.org Recipe format</li>
						<li>An array of recipe objects in Schema.org Recipe format</li>
						<li>Exported data from this application</li>
					</ul>
					<p class="text-sm mt-3" style="color: var(--text-600);">
						You can export your existing recipes from the
						<a href="/export" class="text-primary-600 hover:underline">Export page</a>
						to see the expected format.
					</p>
				</div>
			</div>

			<!-- Extension info -->
			<div class="card mt-6">
				<h3 class="text-lg font-semibold mb-2" style="color: var(--text-900);">
					Browser Extension (Coming Soon)
				</h3>
				<p class="text-sm mb-3" style="color: var(--text-600);">
					Import recipes directly from websites using our browser extension.
				</p>
				<p class="text-sm" style="color: var(--text-500);">
					The browser extension is currently under development and will be available soon.
				</p>
			</div>
		</div>
	</div>
</div>

<style>
	.card {
		background: white;
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
