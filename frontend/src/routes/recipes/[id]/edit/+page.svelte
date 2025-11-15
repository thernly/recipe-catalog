<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { getRecipe, updateRecipe, type Recipe, type RecipeUpdate } from '$lib/api/recipes';
	import RecipeForm from '$lib/components/RecipeForm.svelte';

	let recipe: Recipe | null = null;
	let loading = true;
	let saving = false;
	let error: string | null = null;

	$: recipeId = parseInt($page.params.id);

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

	async function handleSubmit(event: CustomEvent) {
		if (!recipe) return;

		const formData = event.detail as RecipeUpdate;
		saving = true;
		error = null;

		try {
			const updated = await updateRecipe(recipe.id, formData);
			// Navigate to the updated recipe
			goto(`/recipes/${updated.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update recipe';
			console.error('Failed to update recipe:', err);
			saving = false;

			// Show error to user
			alert(`Failed to update recipe: ${error}`);
		}
	}

	function handleCancel() {
		if (!recipe) {
			goto('/recipes');
			return;
		}

		if (confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) {
			goto(`/recipes/${recipe.id}`);
		}
	}

	onMount(() => {
		loadRecipe();
	});
</script>

<svelte:head>
	<title>{recipe?.name ? `Edit ${recipe.name}` : 'Edit Recipe'} - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50 py-8">
	{#if loading}
		<!-- Loading state -->
		<div class="container-custom text-center py-16">
			<div class="text-4xl mb-4">⏳</div>
			<p class="text-lg" style="color: var(--text-600);">Loading recipe...</p>
		</div>
	{:else if error || !recipe}
		<!-- Error state -->
		<div class="container-custom text-center py-16">
			<div class="text-4xl mb-4">⚠️</div>
			<p class="text-lg mb-2" style="color: var(--text-900);">Recipe not found</p>
			<p class="text-sm mb-4" style="color: var(--text-600);">
				{error || 'This recipe may have been deleted.'}
			</p>
			<button on:click={() => goto('/recipes')} class="btn btn-primary">Back to Recipes</button>
		</div>
	{:else}
		<div class="container-custom">
			<!-- Header -->
			<div class="mb-8">
				<button
					on:click={() => goto(`/recipes/${recipe.id}`)}
					class="text-sm mb-4 flex items-center gap-2"
					style="color: var(--text-600);"
				>
					← Back to Recipe
				</button>

				<h1 class="text-4xl font-bold" style="color: var(--text-900);">Edit Recipe</h1>
				<p class="text-lg mt-2" style="color: var(--text-600);">{recipe.name}</p>

				{#if recipe.source_type === 'imported' && !recipe.is_modified}
					<div class="mt-3 p-4 rounded-lg" style="background: var(--accent-100); color: var(--accent-800);">
						<p class="text-sm font-medium">
							ℹ️ This recipe was imported. Editing it will mark it as modified.
						</p>
					</div>
				{/if}
			</div>

			<!-- Form -->
			<RecipeForm {recipe} on:submit={handleSubmit} on:cancel={handleCancel} {saving} />
		</div>
	{/if}
</div>
