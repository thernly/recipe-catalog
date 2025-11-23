<script lang="ts">
	import { goto } from '$app/navigation';
	import { generateRecipe } from '$lib/api/ai';
	import { createRecipe, type RecipeCreate } from '$lib/api/recipes';
	import RecipeForm from '$lib/components/RecipeForm.svelte';

	let step: 'input' | 'preview' = 'input';
	let generating = false;
	let saving = false;
	let error: string | null = null;

	// Form inputs
	let ingredientsText = '';
	let cuisine = '';
	let timeLimit: number | null = null;
	let dietaryPreferences: string[] = [];
	let equipment: string[] = [];

	// Generated recipe
	let generatedRecipe: any = null;

	const dietaryOptions = [
		'Vegetarian',
		'Vegan',
		'Gluten-Free',
		'Dairy-Free',
		'Nut-Free',
		'Low-Carb',
		'Keto'
	];

	const equipmentOptions = [
		'Oven',
		'Stovetop',
		'Microwave',
		'Slow Cooker',
		'Instant Pot',
		'Air Fryer',
		'Blender',
		'Food Processor'
	];

	function toggleDietary(option: string) {
		if (dietaryPreferences.includes(option)) {
			dietaryPreferences = dietaryPreferences.filter((p) => p !== option);
		} else {
			dietaryPreferences = [...dietaryPreferences, option];
		}
	}

	function toggleEquipment(option: string) {
		if (equipment.includes(option)) {
			equipment = equipment.filter((e) => e !== option);
		} else {
			equipment = [...equipment, option];
		}
	}

	async function handleGenerate() {
		error = null;
		generating = true;

		// Parse ingredients from textarea (one per line or comma-separated)
		const ingredients = ingredientsText
			.split(/[\n,]/)
			.map((s) => s.trim())
			.filter((s) => s.length > 0);

		if (ingredients.length === 0) {
			error = 'Please enter at least one ingredient';
			generating = false;
			return;
		}

		try {
			const response = await generateRecipe({
				ingredients,
				cuisine: cuisine || undefined,
				time_limit: timeLimit || undefined,
				dietary_preferences: dietaryPreferences.length > 0 ? dietaryPreferences : undefined,
				equipment: equipment.length > 0 ? equipment : undefined
			});

			generatedRecipe = response.recipe;
			step = 'preview';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to generate recipe';
			console.error('Failed to generate recipe:', err);
		} finally {
			generating = false;
		}
	}

	async function handleSave(event: CustomEvent) {
		const formData = event.detail as RecipeCreate;
		saving = true;
		error = null;

		try {
			// Ensure source_type is set to ai-generated
			formData.source_type = 'ai-generated';

			const recipe = await createRecipe(formData);
			goto(`/recipes/${recipe.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to save recipe';
			console.error('Failed to save recipe:', err);
			saving = false;
			alert(`Failed to save recipe: ${error}`);
		}
	}

	function handleCancel() {
		if (step === 'preview') {
			step = 'input';
			generatedRecipe = null;
		} else {
			goto('/recipes');
		}
	}

	function parseRecipeData(recipe: any): RecipeCreate {
		// Calculate total time in minutes
		const totalTime = recipe.totalTime || '';
		let totalTimeMinutes: number | undefined = undefined;

		if (totalTime) {
			const match = totalTime.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
			if (match) {
				const hours = parseInt(match[1] || '0');
				const minutes = parseInt(match[2] || '0');
				totalTimeMinutes = hours * 60 + minutes;
			}
		}

		// Extract category and cuisine
		const category =
			Array.isArray(recipe.recipeCategory) && recipe.recipeCategory.length > 0
				? recipe.recipeCategory[0]
				: recipe.recipeCategory || undefined;

		const recipeCuisine =
			Array.isArray(recipe.recipeCuisine) && recipe.recipeCuisine.length > 0
				? recipe.recipeCuisine[0]
				: recipe.recipeCuisine || undefined;

		return {
			name: recipe.name || 'AI-Generated Recipe',
			description: recipe.description || '',
			recipe_data: recipe,
			source_type: 'ai-generated',
			cuisine: recipeCuisine,
			category: category,
			total_time_minutes: totalTimeMinutes
		};
	}
</script>

<svelte:head>
	<title>AI Recipe Generator - Recipe Catalog</title>
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

			<h1 class="text-4xl font-bold" style="color: var(--text-900);">AI Recipe Generator</h1>
			<p class="text-lg mt-2" style="color: var(--text-600);">
				Generate creative recipes from your available ingredients
			</p>
		</div>

		{#if step === 'input'}
			<!-- Input Form -->
			<div class="max-w-3xl mx-auto bg-white rounded-lg shadow-sm p-8">
				<!-- Food Safety Disclaimer -->
				<div class="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
					<p class="text-sm" style="color: var(--text-700);">
						<strong>Food Safety Notice:</strong> AI-generated recipes should be reviewed for safety,
						proper cooking temperatures, and food handling. Always verify ingredient combinations and
						cooking instructions.
					</p>
				</div>

				<!-- Ingredients -->
				<div class="mb-6">
					<label
						for="ingredients-input"
						class="block text-sm font-semibold mb-2"
						style="color: var(--text-900);"
					>
						Ingredients <span class="text-red-500">*</span>
					</label>
					<p class="text-sm mb-2" style="color: var(--text-600);">
						Enter your available ingredients (one per line or comma-separated)
					</p>
					<textarea
						id="ingredients-input"
						bind:value={ingredientsText}
						rows="6"
						class="input-field w-full"
						placeholder="chicken breast&#10;bell peppers&#10;onion&#10;garlic&#10;rice"
						required
					></textarea>
				</div>

				<!-- Optional Constraints -->
				<div class="mb-6">
					<h3 class="text-lg font-semibold mb-4" style="color: var(--text-900);">
						Optional Constraints
					</h3>

					<!-- Cuisine -->
					<div class="mb-4">
						<label
							for="cuisine-input"
							class="block text-sm font-semibold mb-2"
							style="color: var(--text-900);"
						>
							Cuisine Type
						</label>
						<input
							id="cuisine-input"
							type="text"
							bind:value={cuisine}
							class="input-field w-full"
							placeholder="e.g., Italian, Mexican, Asian"
						/>
					</div>

					<!-- Time Limit -->
					<div class="mb-4">
						<label
							for="time-limit-input"
							class="block text-sm font-semibold mb-2"
							style="color: var(--text-900);"
						>
							Maximum Time (minutes)
						</label>
						<input
							id="time-limit-input"
							type="number"
							bind:value={timeLimit}
							class="input-field w-full"
							placeholder="e.g., 30"
							min="1"
							max="480"
						/>
					</div>

					<!-- Dietary Preferences -->
					<fieldset class="mb-4">
						<legend class="block text-sm font-semibold mb-2" style="color: var(--text-900);">
							Dietary Preferences
						</legend>
						<div class="flex flex-wrap gap-2">
							{#each dietaryOptions as option}
								<button
									type="button"
									on:click={() => toggleDietary(option)}
									class="px-3 py-1.5 text-sm rounded-full border transition-colors {dietaryPreferences.includes(
										option
									)
										? 'bg-emerald-100 border-emerald-500 text-emerald-700'
										: 'bg-white border-gray-300 text-gray-700 hover:border-gray-400'}"
								>
									{option}
								</button>
							{/each}
						</div>
					</fieldset>

					<!-- Equipment -->
					<fieldset class="mb-4">
						<legend class="block text-sm font-semibold mb-2" style="color: var(--text-900);">
							Available Equipment
						</legend>
						<div class="flex flex-wrap gap-2">
							{#each equipmentOptions as option}
								<button
									type="button"
									on:click={() => toggleEquipment(option)}
									class="px-3 py-1.5 text-sm rounded-full border transition-colors {equipment.includes(
										option
									)
										? 'bg-blue-100 border-blue-500 text-blue-700'
										: 'bg-white border-gray-300 text-gray-700 hover:border-gray-400'}"
								>
									{option}
								</button>
							{/each}
						</div>
					</fieldset>
				</div>

				<!-- Error Message -->
				{#if error}
					<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
						<p class="text-sm text-red-700">{error}</p>
					</div>
				{/if}

				<!-- Actions -->
				<div class="flex gap-4">
					<button type="button" on:click={handleGenerate} disabled={generating} class="btn-primary">
						{#if generating}
							<svg
								class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
							>
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
								/>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								/>
							</svg>
							Generating Recipe...
						{:else}
							Generate Recipe
						{/if}
					</button>
					<button type="button" on:click={handleCancel} class="btn-secondary">Cancel</button>
				</div>
			</div>
		{:else if step === 'preview' && generatedRecipe}
			<!-- Preview & Edit -->
			<div class="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
				<p class="text-sm" style="color: var(--text-700);">
					<strong>✨ AI-Generated Recipe</strong> - Review and edit the recipe below before saving.
					This recipe will be marked as AI-generated in your catalog.
				</p>
			</div>

			<RecipeForm
				initialData={parseRecipeData(generatedRecipe)}
				on:submit={handleSave}
				on:cancel={handleCancel}
				saving={saving}
			/>
		{/if}
	</div>
</div>

<style>
	.input-field {
		padding: 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		transition: border-color 0.15s;
	}

	.input-field:focus {
		outline: none;
		border-color: var(--primary-500);
		box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
	}

	.btn-primary {
		padding: 0.75rem 1.5rem;
		background-color: var(--primary-600);
		color: white;
		border: none;
		border-radius: 0.375rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.15s;
	}

	.btn-primary:hover:not(:disabled) {
		background-color: var(--primary-700);
	}

	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-secondary {
		padding: 0.75rem 1.5rem;
		background-color: white;
		color: var(--text-700);
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.15s;
	}

	.btn-secondary:hover {
		background-color: #f9fafb;
	}
</style>
