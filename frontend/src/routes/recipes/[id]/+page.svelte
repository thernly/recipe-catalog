<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { getRecipe, deleteRecipe, duplicateRecipe, exportRecipe, type Recipe } from '$lib/api/recipes';
	import { generateFromRecipe, listShoppingLists, type ShoppingListSummary } from '$lib/api/shopping-lists';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';
	import { ArrowLeft, Edit, Copy, ShoppingCart, Download, Printer, Trash2, Loader2, Globe, FileText } from 'lucide-svelte';

	let recipe: Recipe | null = null;
	let loading = true;
	let error: string | null = null;
	let checkedIngredients = new Set<number>();
	let showExportMenu = false;
	let exporting = false;
	let showAddToShoppingListDialog = false;
	let shoppingLists: ShoppingListSummary[] = [];
	let addingToList = false;

	// Get recipe ID from URL
	$: recipeId = parseInt($page.params.id!);

	async function loadRecipe() {
		loading = true;
		error = null;

		try {
			recipe = await getRecipe(recipeId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load recipe';
			console.error('Failed to load recipe:', err);
		} finally {
			loading = false;
		}
	}

	function toggleIngredient(index: number) {
		if (checkedIngredients.has(index)) {
			checkedIngredients.delete(index);
		} else {
			checkedIngredients.add(index);
		}
		checkedIngredients = checkedIngredients; // Trigger reactivity
	}

	function getIngredients(recipe: Recipe): string[] {
		if (recipe.recipe_data?.recipeIngredient) {
			return recipe.recipe_data.recipeIngredient;
		}
		return [];
	}

	function getInstructions(recipe: Recipe): string[] {
		if (recipe.recipe_data?.recipeInstructions) {
			const instructions = recipe.recipe_data.recipeInstructions;
			if (Array.isArray(instructions)) {
				return instructions.map((item: any) => {
					if (typeof item === 'string') return item;
					if (item?.text) return item.text;
					return JSON.stringify(item);
				});
			}
		}
		return [];
	}

	function formatTime(duration: string | undefined): string {
		if (!duration) return '';
		// Parse ISO 8601 duration (PT1H30M format)
		const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
		if (!match) return duration;

		const hours = parseInt(match[1] || '0');
		const minutes = parseInt(match[2] || '0');

		if (hours && minutes) return `${hours}h ${minutes}min`;
		if (hours) return `${hours}h`;
		if (minutes) return `${minutes}min`;
		return '';
	}

	function formatNutritionLabel(key: string): string {
		// Convert camelCase to Title Case with spaces
		// e.g., "fatContent" -> "Fat Content"
		return key
			.replace(/([A-Z])/g, ' $1') // Add space before capital letters
			.replace(/^./, (str) => str.toUpperCase()) // Capitalize first letter
			.trim();
	}

	function handleBackToRecipes() {
		// Check if we have a returnUrl query parameter first
		const returnUrl = $page.url.searchParams.get('returnUrl');
		if (returnUrl) {
			// Use the explicit return URL (preserves search filters)
			goto(decodeURIComponent(returnUrl));
		} else {
			// Fallback: Check if we came from the recipes page by looking at the referrer
			const referrer = document.referrer;
			if (referrer && referrer.includes('/recipes') && !referrer.includes('/recipes/')) {
				// Go back to preserve search state
				window.history.back();
			} else {
				// Navigate to recipes page
				goto('/recipes');
			}
		}
	}

	async function handleDelete() {
		if (!recipe) return;
		const deleteId = recipe.id;
		const deleteName = recipe.name;

		dialog.show({
			title: 'Delete Recipe',
			message: `Are you sure you want to delete "${deleteName}"? It will be moved to trash.`,
			onConfirm: async () => {
				try {
					await deleteRecipe(deleteId);
					toast.success('Recipe deleted successfully');
					goto('/recipes');
				} catch (err) {
					toast.error('Failed to delete recipe');
					console.error('Delete failed:', err);
				}
			}
		});
	}

	async function handleDuplicate() {
		if (!recipe) return;

		try {
			const duplicated = await duplicateRecipe(recipe.id);
			toast.success('Recipe duplicated successfully');
			goto(`/recipes/${duplicated.id}/edit`);
		} catch (err) {
			toast.error('Failed to duplicate recipe');
			console.error('Duplicate failed:', err);
		}
	}

	function handlePrint() {
		window.print();
	}

	async function handleExport(format: 'json' | 'markdown' | 'text' | 'pdf') {
		if (!recipe) return;

		exporting = true;
		showExportMenu = false;

		try {
			const blob = await exportRecipe(recipe.id, format);

			// Generate filename
			const extensions = { json: 'json', markdown: 'md', text: 'txt', pdf: 'pdf' };
			const safeName = recipe.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
			const filename = `${safeName}.${extensions[format]}`;

			// Create download
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = filename;
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
			document.body.removeChild(a);
		} catch (err) {
			toast.error(`Failed to export recipe: ${err instanceof Error ? err.message : 'Unknown error'}`);
			console.error('Export failed:', err);
		} finally {
			exporting = false;
		}
	}

	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.export-dropdown')) {
			showExportMenu = false;
		}
	}

	async function handleAddToShoppingList() {
		if (!recipe) return;

		addingToList = true;
		try {
			const newList = await generateFromRecipe({
				recipe_id: recipe.id,
				list_name: `Shopping list for ${recipe.name}`
			});
			showAddToShoppingListDialog = false;
			toast.success('Shopping list created successfully');
			goto(`/shopping-lists/${newList.id}`);
		} catch (err) {
			toast.error(`Failed to create shopping list: ${err instanceof Error ? err.message : 'Unknown error'}`);
			console.error('Failed to create shopping list:', err);
		} finally {
			addingToList = false;
		}
	}

	onMount(() => {
		loadRecipe();
		document.addEventListener('click', handleClickOutside);
		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	});
</script>

<svelte:head>
	<title>{recipe?.name || 'Loading...'} - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	{#if loading}
		<!-- Loading state -->
		<div class="container-custom py-16 text-center">
			<div class="flex justify-center mb-4" style="color: var(--accent-500);">
				<Loader2 size={48} class="animate-spin" aria-hidden="true" />
			</div>
			<p class="text-lg" style="color: var(--text-600);">Loading recipe...</p>
		</div>
	{:else if error || !recipe}
		<!-- Error state -->
		<div class="container-custom py-16 text-center">
			<div class="text-4xl mb-4">⚠️</div>
			<p class="text-lg mb-2" style="color: var(--text-900);">Recipe not found</p>
			<p class="text-sm mb-4" style="color: var(--text-600);">{error || 'This recipe may have been deleted.'}</p>
			<button on:click={handleBackToRecipes} class="btn btn-primary">Back to Recipes</button>
		</div>
	{:else}
		<!-- Recipe content -->
		<div class="recipe-detail-container">
			<!-- Back Button Bar -->
			<div class="back-button-bar">
				<div class="container-custom">
					<button
						on:click={handleBackToRecipes}
						class="back-button"
					>
						<ArrowLeft size={20} aria-hidden="true" />
						<span>Back to Recipes</span>
					</button>
				</div>
			</div>

			<!-- Header -->
			<div class="recipe-header">
				<div class="container-custom py-6">
					<div>
						<h1 class="text-3xl font-bold mb-3" style="color: var(--text-900);">
							{recipe.name}
						</h1>

						{#if recipe.source_url}
							<p class="text-base mb-2" style="color: var(--text-600);">
								Source: <a href={recipe.source_url} target="_blank" class="link">
									{new URL(recipe.source_url).hostname}
								</a>
							</p>
						{:else}
							<p class="text-base mb-2" style="color: var(--text-600);">Personal Recipe</p>
						{/if}

						<div class="flex items-center gap-3 text-sm" style="color: var(--text-500);">
							<span class="flex items-center gap-1">
								{#if recipe.source_type === 'imported'}
									<Download size={14} aria-hidden="true" />
									<span>Imported</span>
								{:else}
									<Edit size={14} aria-hidden="true" />
									<span>Manual</span>
								{/if}
							</span>
							{#if recipe.is_modified && recipe.source_type === 'imported'}
								<span>• Modified</span>
							{/if}
							<span>• Added {new Date(recipe.created_at).toLocaleDateString()}</span>
							{#if recipe.creator_display_name}
								<span>• Created by {recipe.creator_display_name}</span>
							{/if}
						</div>
					</div>
				</div>
			</div>

		<!-- Main content -->
		<div class="container-custom py-8 recipe-content">
			<!-- Hero Image -->
			{#if recipe.recipe_data?.images?.[0]?.data && recipe.recipe_data.images[0].data.trim()}
				<div class="recipe-hero-image mb-6">
					<img
						src="data:{recipe.recipe_data.images[0].mimeType};base64,{recipe.recipe_data.images[0].data}"
						alt={recipe.name}
					/>
				</div>
			{:else if recipe.image_url}
				<div class="recipe-hero-image mb-6">
					<img src={recipe.image_url} alt={recipe.name} />
				</div>
			{/if}				<!-- Description -->
				{#if recipe.description}
					<p class="text-lg leading-relaxed mb-8" style="color: var(--text-700);">{recipe.description}</p>
				{/if}

				<!-- Consolidated Metadata card -->
				{#if recipe.recipe_data?.prepTime || recipe.recipe_data?.cookTime || recipe.recipe_data?.totalTime || recipe.total_time_minutes || recipe.recipe_data?.recipeYield}
					<div class="metadata-card-consolidated mb-8">
						<div class="metadata-items">
							{#if recipe.recipe_data?.prepTime}
								<div class="metadata-item">
									<span class="metadata-label-inline">Prep:</span>
									<span class="metadata-value-inline">{formatTime(recipe.recipe_data.prepTime)}</span>
								</div>
							{/if}

							{#if recipe.recipe_data?.cookTime}
								<div class="metadata-item">
									<span class="metadata-label-inline">Cook:</span>
									<span class="metadata-value-inline">{formatTime(recipe.recipe_data.cookTime)}</span>
								</div>
							{/if}

							{#if recipe.recipe_data?.totalTime || recipe.total_time_minutes}
								<div class="metadata-item">
									<span class="metadata-label-inline">Total:</span>
									<span class="metadata-value-inline">
										{recipe.recipe_data?.totalTime ? formatTime(recipe.recipe_data.totalTime) : `${recipe.total_time_minutes}min`}
									</span>
								</div>
							{/if}

							{#if recipe.recipe_data?.recipeYield}
								<div class="metadata-item">
									<span class="metadata-label-inline">Yield:</span>
									<span class="metadata-value-inline">{recipe.recipe_data.recipeYield}</span>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Tags -->
				{#if recipe.cuisine || recipe.category || recipe.recipe_data?.keywords}
					<div class="flex flex-wrap gap-2 mb-8">
						{#if recipe.cuisine}
							<span class="tag">{recipe.cuisine}</span>
						{/if}
						{#if recipe.category}
							<span class="tag tag-secondary">{recipe.category}</span>
						{/if}
						{#if recipe.recipe_data?.keywords}
							{#each recipe.recipe_data.keywords.split(',').slice(0, 5) as keyword}
								<span class="tag tag-outline">{keyword.trim()}</span>
							{/each}
						{/if}
					</div>
				{/if}

				<!-- Equipment (if any) -->
				{#if recipe.recipe_data?.equipment && recipe.recipe_data.equipment.length > 0}
					<div class="card mb-8">
						<h2 class="text-xl font-semibold mb-3" style="color: var(--text-900);">Equipment</h2>
						<ul class="equipment-list">
							{#each recipe.recipe_data.equipment as item}
								<li style="color: var(--text-700);">{item}</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- Ingredients and Instructions -->
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
					<!-- Ingredients -->
					<div class="card">
						<h2 class="text-2xl font-semibold mb-4" style="color: var(--text-900);">
							Ingredients
						</h2>

						<ul class="space-y-3">
							{#each getIngredients(recipe) as ingredient, index}
								<li class="flex items-start gap-3">
									<input
										type="checkbox"
										id="ingredient-{index}"
										checked={checkedIngredients.has(index)}
										on:change={() => toggleIngredient(index)}
										class="ingredient-checkbox"
									/>
									<label
										for="ingredient-{index}"
										class="flex-1 cursor-pointer"
										class:line-through={checkedIngredients.has(index)}
										class:opacity-50={checkedIngredients.has(index)}
										style="color: var(--text-700);"
									>
										{ingredient}
									</label>
								</li>
							{/each}
						</ul>
					</div>

					<!-- Instructions -->
					<div class="card">
						<h2 class="text-2xl font-semibold mb-4" style="color: var(--text-900);">
							Instructions
						</h2>

						<ol class="instructions-list">
							{#each getInstructions(recipe) as instruction, index}
								<li class="instruction-step">
									<span class="step-number">
										{index + 1}
									</span>
									<p class="step-text">
										{instruction}
									</p>
								</li>
							{/each}
						</ol>
					</div>
				</div>

				<!-- Notes (if any) -->
				{#if recipe.recipe_data?.notes}
					<div class="card mt-8">
						<h2 class="text-xl font-semibold mb-3" style="color: var(--text-900);">Notes & Tips</h2>
						<p style="color: var(--text-700);">{recipe.recipe_data.notes}</p>
					</div>
				{/if}

				<!-- Nutrition (if any) -->
				{#if recipe.recipe_data?.nutrition}
					<details class="card mt-8">
						<summary class="text-xl font-semibold cursor-pointer" style="color: var(--text-900);">
							Nutrition Information
						</summary>
						<div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
							{#each Object.entries(recipe.recipe_data.nutrition) as [key, value]}
								<div>
									<div class="text-sm" style="color: var(--text-600);">{formatNutritionLabel(key)}</div>
									<div class="font-semibold" style="color: var(--text-900);">{value}</div>
								</div>
							{/each}
						</div>
					</details>
				{/if}
			</div>
		</div>

		<!-- Sticky Action Bar -->
		<div class="sticky-action-bar no-print">
			<div class="container-custom">
				<div class="action-bar-content">
					<!-- Primary Actions -->
					<div class="action-group">
						<button on:click={() => goto(`/recipes/${recipe?.id}/edit`)} class="btn btn-primary flex items-center gap-2">
							<Edit size={18} aria-hidden="true" />
							<span>Edit Recipe</span>
						</button>
						<button
							on:click={handleAddToShoppingList}
							class="btn btn-primary flex items-center gap-2"
							disabled={addingToList}
						>
							{#if addingToList}
								<Loader2 size={18} class="animate-spin" aria-hidden="true" />
							{:else}
								<ShoppingCart size={18} aria-hidden="true" />
							{/if}
							<span>Shopping List</span>
						</button>
					</div>

					<!-- Utility Actions -->
					<div class="action-group">
						<button on:click={handleDuplicate} class="btn btn-secondary flex items-center gap-2">
							<Copy size={16} aria-hidden="true" />
							<span>Duplicate</span>
						</button>
					<button on:click={handlePrint} data-print-hide class="btn btn-secondary flex items-center gap-2">
						<Printer size={16} aria-hidden="true" />
						<span>Print</span>
					</button>

						<!-- Export dropdown -->
						<div class="export-dropdown">
							<button
								on:click={() => showExportMenu = !showExportMenu}
								class="btn btn-secondary flex items-center gap-2"
								disabled={exporting}
							>
								{#if exporting}
									<Loader2 size={16} class="animate-spin" aria-hidden="true" />
								{:else}
									<Download size={16} aria-hidden="true" />
								{/if}
								<span>Export</span>
							</button>
							{#if showExportMenu}
								<div class="export-menu export-menu-up">
									<button on:click={() => handleExport('pdf')} class="export-menu-item">
										<FileText size={14} aria-hidden="true" />
										<span>PDF</span>
									</button>
									<button on:click={() => handleExport('json')} class="export-menu-item">
										<FileText size={14} aria-hidden="true" />
										<span>JSON</span>
									</button>
									<button on:click={() => handleExport('markdown')} class="export-menu-item">
										<FileText size={14} aria-hidden="true" />
										<span>Markdown</span>
									</button>
									<button on:click={() => handleExport('text')} class="export-menu-item">
										<FileText size={14} aria-hidden="true" />
										<span>Plain Text</span>
									</button>
								</div>
							{/if}
						</div>
					</div>

					<!-- Danger Actions -->
					<div class="action-group">
						<button on:click={handleDelete} class="btn btn-danger flex items-center gap-2">
							<Trash2 size={16} aria-hidden="true" />
							<span>Delete</span>
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.recipe-detail-container {
		background: var(--neutral-white);
		min-height: 100vh;
	}

	.recipe-content {
		padding-bottom: 10rem; /* Space for sticky action bar on desktop */
	}

	.back-button-bar {
		background: var(--neutral-white);
		border-bottom: 1px solid var(--neutral-200);
		padding: 1rem 0;
	}

	.back-button {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		background: var(--accent-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-base);
		box-shadow: var(--shadow-sm);
	}

	.back-button:hover {
		background: var(--accent-600);
		transform: translateY(-1px);
		box-shadow: var(--shadow-md);
	}

	.back-button:active {
		transform: translateY(0);
	}

	.recipe-header {
		background: var(--neutral-50);
		border-bottom: 1px solid var(--neutral-200);
	}

	.recipe-hero-image {
		width: 100%;
		max-height: 350px;
		overflow: hidden;
		background: var(--neutral-100);
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-lg);
		margin: 0 auto;
		box-shadow: var(--shadow-md);
		position: relative;
	}

	.recipe-hero-image::after {
		content: '';
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 40%;
		background: linear-gradient(to top, rgba(0, 0, 0, 0.15), transparent);
		pointer-events: none;
	}

	.recipe-hero-image img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		aspect-ratio: 16 / 9;
	}

	.metadata-card-consolidated {
		background: var(--primary-50);
		border: 1px solid var(--neutral-300);
		border-radius: var(--radius-lg);
		padding: 1.5rem 2rem;
		box-shadow: var(--shadow-sm);
	}

	.metadata-items {
		display: flex;
		flex-wrap: wrap;
		gap: 2.5rem;
		align-items: center;
	}

	.metadata-item {
		display: flex;
		align-items: baseline;
		gap: 0.625rem;
	}

	.metadata-label-inline {
		font-family: var(--font-ui);
		font-size: 0.875rem;
		color: var(--text-600);
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.metadata-value-inline {
		font-family: var(--font-display);
		font-size: 1.375rem;
		font-weight: 600;
		color: var(--text-900);
	}

	.equipment-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		list-style: none;
		padding: 0;
	}

	.equipment-list li {
		background: var(--neutral-100);
		padding: 0.625rem 1.125rem;
		border-radius: var(--radius-full);
		font-family: var(--font-ui);
		font-size: 0.875rem;
		color: var(--text-700);
		border: 1px solid var(--neutral-300);
		transition: all var(--transition-fast);
	}

	.equipment-list li:hover {
		background: var(--neutral-200);
		border-color: var(--neutral-400);
	}

	.tag {
		display: inline-flex;
		align-items: center;
		padding: 0.5rem 1.125rem;
		background: var(--accent-100);
		color: var(--accent-800);
		border-radius: var(--radius-full);
		font-family: var(--font-ui);
		font-size: 0.8125rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all var(--transition-fast);
	}

	.tag:hover {
		background: var(--accent-200);
		transform: translateY(-1px);
	}

	.tag-secondary {
		background: var(--neutral-200);
		color: var(--text-700);
	}

	.tag-secondary:hover {
		background: var(--neutral-300);
	}

	.tag-outline {
		background: transparent;
		border: 1.5px solid var(--neutral-400);
		color: var(--text-600);
	}

	.tag-outline:hover {
		border-color: var(--accent-500);
		color: var(--accent-700);
	}

	.ingredient-checkbox {
		appearance: none;
		margin-top: 0.25rem;
		width: 1.5rem;
		height: 1.5rem;
		cursor: pointer;
		border: 2px solid var(--neutral-400);
		border-radius: 50%;
		background: var(--neutral-50);
		transition: all var(--transition-base);
		position: relative;
		flex-shrink: 0;
	}

	.ingredient-checkbox:hover {
		border-color: var(--accent-500);
		background: var(--accent-50);
	}

	.ingredient-checkbox:checked {
		background: var(--accent-500);
		border-color: var(--accent-500);
	}

	.ingredient-checkbox:checked::after {
		content: '';
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%) rotate(45deg);
		width: 0.375rem;
		height: 0.625rem;
		border: solid var(--neutral-white);
		border-width: 0 2px 2px 0;
	}

	/* Instructions Styling */
	.instructions-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.instruction-step {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
		transition: all var(--transition-base);
		padding: 0.75rem;
		margin: -0.75rem;
		border-radius: var(--radius-md);
	}

	.instruction-step:hover {
		background: var(--primary-50);
	}

	.step-number {
		flex-shrink: 0;
		width: 2.5rem;
		height: 2.5rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-display);
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--neutral-white);
		background: linear-gradient(135deg, var(--accent-500) 0%, var(--accent-600) 100%);
		box-shadow: var(--shadow-md);
	}

	.step-text {
		flex: 1;
		font-size: 1.125rem;
		line-height: 1.7;
		color: var(--text-700);
		margin: 0;
		padding-top: 0.375rem;
	}

	.link {
		color: var(--accent-500);
		text-decoration: underline;
		transition: color var(--transition-fast);
	}

	.link:hover {
		color: var(--accent-600);
	}

	.btn-danger {
		background: #EF4444;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		cursor: pointer;
		border: none;
		transition: all var(--transition-fast);
	}

	.btn-danger:hover {
		background: #DC2626;
	}

	.export-dropdown {
		position: relative;
	}

	.export-menu {
		position: absolute;
		top: 100%;
		right: 0;
		margin-top: 0.5rem;
		background: white;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-md);
		min-width: 150px;
		z-index: 10;
		overflow: hidden;
	}

	.export-menu-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.75rem 1rem;
		text-align: left;
		background: white;
		border: none;
		cursor: pointer;
		font-size: 0.875rem;
		color: var(--text-700);
		transition: background var(--transition-fast);
	}

	.export-menu-item:hover {
		background: var(--neutral-50);
	}

	.export-menu-item:not(:last-child) {
		border-bottom: 1px solid var(--neutral-100);
	}

	.export-menu-up {
		bottom: 100%;
		top: auto;
		margin-bottom: 0.5rem;
		margin-top: 0;
	}

	/* Sticky Action Bar */
	.sticky-action-bar {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		background: var(--neutral-white);
		border-top: 2px solid var(--accent-500);
		box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
		z-index: 40;
		padding: 1rem 0;
	}

	.action-bar-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1.5rem;
		flex-wrap: wrap;
	}

	.action-group {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.action-group:first-child {
		flex: 1;
	}

	/* Responsive adjustments */
	@media (max-width: 768px) {
		.recipe-content {
			padding-bottom: 20rem; /* More space on mobile since action bar is taller */
		}

		.action-bar-content {
			flex-direction: column;
			align-items: stretch;
		}

		.action-group {
			justify-content: center;
			width: 100%;
		}

		.action-group:first-child {
			flex: none;
		}
	}

	/* Print styles */
	@media print {
		.back-button,
		.btn,
		.btn-danger {
			display: none;
		}

		.recipe-detail-container {
			background: white;
		}

		.ingredient-checkbox {
			display: none;
		}
	}
</style>
