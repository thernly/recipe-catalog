<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import type { Recipe, RecipeCreate, RecipeUpdate } from '$lib/api/recipes';
	import IngredientsEditor from '$lib/components/recipe/IngredientsEditor.svelte';
	import InstructionsEditor from '$lib/components/recipe/InstructionsEditor.svelte';
	import Button from '$lib/components/Button.svelte';

	export let recipe: Recipe | null = null; // null for create, recipe for edit
	export let saving = false;
	export let initialData: RecipeCreate | null = null;

	const dispatch = createEventDispatcher();

	const baseRecipeData = recipe?.recipe_data ?? initialData?.recipe_data;

	// Form fields
	let name = initialData?.name ?? recipe?.name ?? '';
	let description = initialData?.description ?? recipe?.description ?? '';
	let imageUrl = recipe?.image_url ?? initialData?.image_url ?? '';
	let cuisine = initialData?.cuisine ?? recipe?.cuisine ?? '';
	let category = initialData?.category ?? recipe?.category ?? '';
	let sourceUrl = recipe?.source_url ?? '';

	// Times (in minutes)
	let prepTimeHours = 0;
	let prepTimeMinutes = 0;
	let cookTimeHours = 0;
	let cookTimeMinutes = 0;
	let totalTimeMinutes = recipe?.total_time_minutes || 0;

	let recipeYield = baseRecipeData?.recipeYield || '';

	// Helper to normalize instructions to string array
	function normalizeInstructions(instructions: any): string[] {
		if (!instructions) return [''];
		if (typeof instructions === 'string') return [instructions];
		if (Array.isArray(instructions)) {
			return instructions.map(item =>
				typeof item === 'string' ? item : (item.text || '')
			).filter(Boolean);
		}
		return [''];
	}

	// Dynamic lists
	const initialIngredients = baseRecipeData?.recipeIngredient;
	const initialInstructions = baseRecipeData?.recipeInstructions;
	const initialEquipment = baseRecipeData?.equipment;

	let ingredients: string[] = Array.isArray(initialIngredients) && initialIngredients.length > 0 ? [...initialIngredients] : [''];
	let instructions: string[] = normalizeInstructions(initialInstructions);
	let equipment: string[] = Array.isArray(initialEquipment) ? [...initialEquipment] : [];
	let notes = baseRecipeData?.notes || '';
	let keywords = baseRecipeData?.keywords || '';

	// Validation errors
	let errors: Record<string, string> = {};

	// Parse existing times if editing
	if (baseRecipeData) {
		const data = baseRecipeData;
		if (data.prepTime) {
			const match = data.prepTime.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
			if (match) {
				prepTimeHours = parseInt(match[1] || '0');
				prepTimeMinutes = parseInt(match[2] || '0');
			}
		}
		if (data.cookTime) {
			const match = data.cookTime.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
			if (match) {
				cookTimeHours = parseInt(match[1] || '0');
				cookTimeMinutes = parseInt(match[2] || '0');
			}
		}
	}

	// Calculate total time when prep/cook changes
	$: {
		const prep = prepTimeHours * 60 + prepTimeMinutes;
		const cook = cookTimeHours * 60 + cookTimeMinutes;
		totalTimeMinutes = prep + cook;
	}

	// Handle ingredient/instruction changes
	function handleIngredientsChange(e: CustomEvent) {
		ingredients = e.detail;
	}

	function handleInstructionsChange(e: CustomEvent) {
		instructions = e.detail;
	}

	// Add/remove equipment
	function addEquipment() {
		equipment = [...equipment, ''];
	}

	function removeEquipment(index: number) {
		equipment = equipment.filter((_, i) => i !== index);
	}

	// Validation
	function validate(): boolean {
		errors = {};

		if (!name.trim()) {
			errors.name = 'Recipe name is required';
		}

		// Filter empty values
		const validIngredients = ingredients.filter((i) => i.trim());
		if (validIngredients.length === 0) {
			errors.ingredients = 'At least one ingredient is required';
		}

		const validInstructions = instructions.filter((i) => i.trim());
		if (validInstructions.length === 0) {
			errors.instructions = 'At least one instruction is required';
		}

		return Object.keys(errors).length === 0;
	}

	// Format time to ISO 8601 duration
	function formatDuration(hours: number, minutes: number): string | undefined {
		if (hours === 0 && minutes === 0) return undefined;
		let duration = 'PT';
		if (hours > 0) duration += `${hours}H`;
		if (minutes > 0) duration += `${minutes}M`;
		return duration;
	}

	// Handle submit
	function handleSubmit() {
		if (!validate()) {
			// Scroll to first error
			const firstError = document.querySelector('.error-message');
			if (firstError) {
				firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
			}
			return;
		}

		// Build recipe data
		const recipeData = {
			name,
			recipeIngredient: ingredients.filter((i) => i.trim()),
			recipeInstructions: instructions.filter((i) => i.trim()),
			prepTime: formatDuration(prepTimeHours, prepTimeMinutes),
			cookTime: formatDuration(cookTimeHours, cookTimeMinutes),
			totalTime: totalTimeMinutes > 0 ? formatDuration(Math.floor(totalTimeMinutes / 60), totalTimeMinutes % 60) : undefined,
			recipeYield: recipeYield || undefined,
			equipment: equipment.filter((e) => e.trim()).length > 0 ? equipment.filter((e) => e.trim()) : undefined,
			notes: notes.trim() || undefined,
			keywords: keywords.trim() || undefined
		};

		const formData: RecipeCreate | RecipeUpdate = {
			name: name.trim(),
			description: description.trim() || undefined,
			image_url: imageUrl.trim() || undefined,
			cuisine: cuisine.trim() || undefined,
			category: category.trim() || undefined,
			total_time_minutes: totalTimeMinutes > 0 ? totalTimeMinutes : undefined,
			recipe_data: recipeData
		};

		// Add source URL only for new recipes
		if (!recipe && sourceUrl.trim()) {
			(formData as RecipeCreate).source_url = sourceUrl.trim();
			(formData as RecipeCreate).source_type = 'manual';
		}

		dispatch('submit', formData);
	}

	function handleCancel() {
		dispatch('cancel');
	}

	// Auto-save (TODO: implement localStorage draft saving)
	let autoSaveTimeout: ReturnType<typeof setTimeout> | undefined;
	function scheduleAutoSave() {
		if (autoSaveTimeout) {
			clearTimeout(autoSaveTimeout);
		}
		autoSaveTimeout = setTimeout(() => {
			// Save to localStorage
			if (browser) {
				const draft = {
					name,
					description,
					imageUrl,
					ingredients,
					instructions,
					equipment,
					cuisine,
					category,
					prepTimeHours,
					prepTimeMinutes,
					cookTimeHours,
					cookTimeMinutes,
					recipeYield,
					notes,
					keywords
				};
				localStorage.setItem('recipe-draft', JSON.stringify(draft));
			}
		}, 30000);
	}

	// Watch for changes to trigger auto-save
	$: name, description, scheduleAutoSave();
</script>

<form on:submit|preventDefault={handleSubmit} class="recipe-form">
	<!-- Basic Info Section -->
	<section class="form-section">
		<h2 class="section-title">Basic Information</h2>

		<div class="form-group">
			<label for="name" class="form-label required">Recipe Name</label>
			<input
				type="text"
				id="name"
				bind:value={name}
				placeholder="e.g., Grandma's Chocolate Chip Cookies"
				class="form-input"
				class:error={errors.name}
				required
			/>
			{#if errors.name}
				<p class="error-message">{errors.name}</p>
			{/if}
		</div>

	<div class="form-group">
		<label for="description" class="form-label">Description</label>
		<textarea
			id="description"
			bind:value={description}
			placeholder="A brief description of your recipe..."
			rows="3"
			class="form-input"
		></textarea>
	</div>

		<div class="form-group">
			<label for="imageUrl" class="form-label">Image URL</label>
			<input
				type="url"
				id="imageUrl"
				bind:value={imageUrl}
				placeholder="https://example.com/image.jpg"
				class="form-input"
			/>
			<p class="form-help">Paste a URL to an image, or leave blank to upload later</p>
		</div>

		{#if !recipe}
			<div class="form-group">
				<label for="sourceUrl" class="form-label">Source URL (Optional)</label>
				<input
					type="url"
					id="sourceUrl"
					bind:value={sourceUrl}
					placeholder="https://example.com/original-recipe"
					class="form-input"
				/>
				<p class="form-help">Link to the original recipe if this is adapted from one</p>
			</div>
		{/if}
	</section>

	<!-- Ingredients Section -->
	<IngredientsEditor
		bind:ingredients
		error={errors.ingredients || ''}
		on:change={handleIngredientsChange}
	/>

	<!-- Instructions Section -->
	<InstructionsEditor
		bind:instructions
		error={errors.instructions || ''}
		on:change={handleInstructionsChange}
	/>

	<!-- Times & Yield Section -->
	<section class="form-section">
		<h2 class="section-title">Times & Yield</h2>

	<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
		<fieldset class="form-group time-fieldset">
			<legend class="form-label">Prep Time</legend>
			<div class="flex gap-3">
				<div class="flex-1">
					<label for="prep-time-hours" class="sr-only">Prep time hours</label>
					<input
						id="prep-time-hours"
						type="number"
						bind:value={prepTimeHours}
						min="0"
						placeholder="Hours"
						class="form-input"
					/>
				</div>
				<span class="py-2" aria-hidden="true">:</span>
				<div class="flex-1">
					<label for="prep-time-minutes" class="sr-only">Prep time minutes</label>
					<input
						id="prep-time-minutes"
						type="number"
						bind:value={prepTimeMinutes}
						min="0"
						max="59"
						placeholder="Minutes"
						class="form-input"
					/>
				</div>
			</div>
		</fieldset>

		<fieldset class="form-group time-fieldset">
			<legend class="form-label">Cook Time</legend>
			<div class="flex gap-3">
				<div class="flex-1">
					<label for="cook-time-hours" class="sr-only">Cook time hours</label>
					<input
						id="cook-time-hours"
						type="number"
						bind:value={cookTimeHours}
						min="0"
						placeholder="Hours"
						class="form-input"
					/>
				</div>
				<span class="py-2" aria-hidden="true">:</span>
				<div class="flex-1">
					<label for="cook-time-minutes" class="sr-only">Cook time minutes</label>
					<input
						id="cook-time-minutes"
						type="number"
						bind:value={cookTimeMinutes}
						min="0"
						max="59"
						placeholder="Minutes"
						class="form-input"
					/>
				</div>
			</div>
		</fieldset>
	</div>

		{#if totalTimeMinutes > 0}
			<p class="text-sm mt-2" style="color: var(--text-600);">
				Total Time: {Math.floor(totalTimeMinutes / 60) > 0 ? `${Math.floor(totalTimeMinutes / 60)}h ` : ''}{totalTimeMinutes % 60}min
			</p>
		{/if}

		<div class="form-group mt-6">
			<label for="yield" class="form-label">Yield</label>
			<input
				type="text"
				id="yield"
				bind:value={recipeYield}
				placeholder="e.g., 4 servings, 24 cookies, 1 loaf"
				class="form-input"
			/>
		</div>
	</section>

	<!-- Categories Section -->
	<section class="form-section">
		<h2 class="section-title">Categories & Tags</h2>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div class="form-group">
				<label for="cuisine" class="form-label">Cuisine</label>
				<input
					type="text"
					id="cuisine"
					bind:value={cuisine}
					placeholder="e.g., Italian, Mexican, Thai"
					class="form-input"
				/>
			</div>

			<div class="form-group">
				<label for="category" class="form-label">Category</label>
				<input
					type="text"
					id="category"
					bind:value={category}
					placeholder="e.g., Dessert, Main Course, Appetizer"
					class="form-input"
				/>
			</div>
		</div>

		<div class="form-group">
			<label for="keywords" class="form-label">Keywords</label>
			<input
				type="text"
				id="keywords"
				bind:value={keywords}
				placeholder="e.g., quick, easy, vegetarian, comfort food"
				class="form-input"
			/>
			<p class="form-help">Separate keywords with commas</p>
		</div>
	</section>

	<!-- Equipment Section (Optional) -->
	{#if equipment.length > 0 || recipe}
		<section class="form-section">
			<h2 class="section-title">Equipment</h2>

			<div class="dynamic-list">
				{#each equipment as item, index}
					<div class="dynamic-list-item">
						<input
							type="text"
							bind:value={equipment[index]}
							placeholder="e.g., Stand mixer, 9x13 baking pan"
							class="form-input flex-1"
						/>
						<button type="button" on:click={() => removeEquipment(index)} class="btn-remove" title="Remove">
							×
						</button>
					</div>
				{/each}
			</div>

			<button type="button" on:click={addEquipment} class="btn btn-secondary btn-sm mt-3">
				+ Add Equipment
			</button>
		</section>
	{:else}
		<button type="button" on:click={addEquipment} class="btn btn-secondary btn-sm">
			+ Add Equipment (Optional)
		</button>
	{/if}

	<!-- Notes Section -->
	<section class="form-section">
	<h2 class="section-title">Notes & Tips</h2>

	<div class="form-group">
		<label for="recipe-notes" class="sr-only">Notes and Tips</label>
		<textarea
			id="recipe-notes"
			bind:value={notes}
			placeholder="Add any notes, tips, or variations..."
			rows="4"
			class="form-input"
		></textarea>
	</div>
	</section>

	<!-- Form Actions -->
	<div class="form-actions">
		<Button type="button" on:click={handleCancel} variant="secondary" disabled={saving}>
			Cancel
		</Button>
		<Button type="submit" variant="primary" loading={saving}>
			{#if recipe}
				Update Recipe
			{:else}
				Create Recipe
			{/if}
		</Button>
	</div>
</form>

<style>
	.recipe-form {
		max-width: 800px;
		margin: 0 auto;
	}

	.form-section {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 2rem;
		margin-bottom: 2rem;
	}

	.section-title {
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--text-900);
		margin-bottom: 1.5rem;
	}

	/* Unused: .section-title.required::after removed */
	/* If needed in future, add required class to section-title elements */
	/* .section-title.required::after {
		content: '*';
		color: #EF4444;
		margin-left: 0.25rem;
	} */

	.form-group {
		margin-bottom: 1.5rem;
	}

	.form-group:last-child {
		margin-bottom: 0;
	}

	.form-label {
		display: block;
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-700);
		margin-bottom: 0.5rem;
	}

	.form-label.required::after {
		content: '*';
		color: #EF4444;
		margin-left: 0.25rem;
	}

	.form-input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 1rem;
		color: var(--text-900);
		background: var(--neutral-white);
		transition: all var(--transition-fast);
	}

	.form-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.form-input.error {
		border-color: #EF4444;
	}

	.form-input.error:focus {
		box-shadow: 0 0 0 3px #FEE2E2;
	}

	.form-help {
		font-size: 0.875rem;
		color: var(--text-500);
		margin-top: 0.5rem;
	}

	.error-message {
		font-size: 0.875rem;
		color: #EF4444;
		margin-top: 0.5rem;
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: 1rem;
		padding: 2rem;
		background: var(--neutral-50);
		border-top: 1px solid var(--neutral-200);
		position: sticky;
		bottom: 0;
		z-index: 10;
		margin: 2rem -2rem -2rem;
		border-radius: 0 0 var(--radius-lg) var(--radius-lg);
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}

	textarea.form-input {
		resize: vertical;
		min-height: 5rem;
	}

	.time-fieldset {
		border: 0;
		padding: 0;
		margin: 0 0 1.5rem;
	}

	.time-fieldset:last-child {
		margin-bottom: 0;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		border: 0;
	}
</style>
