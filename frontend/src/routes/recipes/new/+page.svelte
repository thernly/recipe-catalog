<script lang="ts">
	import { goto } from '$app/navigation';
	import { createRecipe, type RecipeCreate } from '$lib/api/recipes';
	import RecipeForm from '$lib/components/RecipeForm.svelte';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';

	let saving = false;
	let error: string | null = null;

	async function handleSubmit(event: CustomEvent) {
		const formData = event.detail as RecipeCreate;
		saving = true;
		error = null;

		try {
			const recipe = await createRecipe(formData);
			// Clear draft from localStorage
			localStorage.removeItem('recipe-draft');
			// Navigate to the new recipe
			toast.success('Recipe created successfully');
			goto(`/recipes/${recipe.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create recipe';
			console.error('Failed to create recipe:', err);
			saving = false;

			// Show error to user
			toast.error(`Failed to create recipe: ${error}`);
		}
	}

	function handleCancel() {
		dialog.show({
			title: 'Cancel Recipe Creation',
			message: 'Are you sure you want to cancel? Any unsaved changes will be lost (except auto-saved drafts).',
			onConfirm: () => {
				goto('/recipes');
			}
		});
	}
</script>

<svelte:head>
	<title>Add New Recipe - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50 py-8">
	<div class="container-custom">
		<!-- Header -->
		<div class="mb-8">
			<button
				on:click={() => goto('/recipes')}
				class="text-sm mb-4 flex items-center gap-2"
				style="color: var(--text-600);"
			>
				← Back to Recipes
			</button>

			<h1 class="text-4xl font-bold" style="color: var(--text-900);">Add New Recipe</h1>
			<p class="text-lg mt-2" style="color: var(--text-600);">
				Manually add a recipe to your collection
			</p>
		</div>

		<!-- Form -->
		<RecipeForm on:submit={handleSubmit} on:cancel={handleCancel} {saving} />
	</div>
</div>
