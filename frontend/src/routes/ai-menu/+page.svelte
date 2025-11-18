<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { generateMenu, type MealSuggestion } from '$lib/api/ai';
	import { getUserPreferences, type UserPreferences } from '$lib/api/users';
	import { addPlannedMeal, getWeekStart, formatDateISO, getCurrentWeekMealPlan } from '$lib/api/meal-plans';

	let step: 'config' | 'preview' = 'config';
	let generating = false;
	let applying = false;
	let error: string | null = null;

	// Form inputs
	let days = 7;
	let selectedMealTypes: Set<string> = new Set(['breakfast', 'lunch', 'dinner']);
	let dietaryPreferences: string[] = [];
	let cuisine = '';
	let mode: 'catalog-first' | 'ai-only' = 'catalog-first';

	// User preferences
	let userPreferences: UserPreferences | null = null;

	// Generated suggestions
	let suggestions: MealSuggestion[] = [];
	let selectedSuggestions: Set<number> = new Set();

	const mealTypeOptions = ['breakfast', 'lunch', 'dinner', 'snack'];

	const dietaryOptions = [
		'Vegetarian',
		'Vegan',
		'Gluten-Free',
		'Dairy-Free',
		'Nut-Free',
		'Low-Carb',
		'Keto',
		'Paleo',
		'Halal',
		'Kosher'
	];

	onMount(async () => {
		// Load user preferences to pre-fill dietary preferences
		try {
			userPreferences = await getUserPreferences();
			if (userPreferences.dietary_preferences && userPreferences.dietary_preferences.length > 0) {
				dietaryPreferences = [...userPreferences.dietary_preferences];
			}
		} catch (err) {
			console.error('Failed to load user preferences:', err);
		}
	});

	function toggleMealType(mealType: string) {
		if (selectedMealTypes.has(mealType)) {
			selectedMealTypes.delete(mealType);
		} else {
			selectedMealTypes.add(mealType);
		}
		selectedMealTypes = selectedMealTypes;
	}

	function toggleDietary(option: string) {
		if (dietaryPreferences.includes(option)) {
			dietaryPreferences = dietaryPreferences.filter((p) => p !== option);
		} else {
			dietaryPreferences = [...dietaryPreferences, option];
		}
	}

	async function handleGenerate() {
		error = null;
		generating = true;

		if (selectedMealTypes.size === 0) {
			error = 'Please select at least one meal type';
			generating = false;
			return;
		}

		try {
			const response = await generateMenu({
				days,
				meals_per_day: Array.from(selectedMealTypes),
				dietary_preferences: dietaryPreferences.length > 0 ? dietaryPreferences : undefined,
				cuisine: cuisine || undefined,
				mode
			});

			suggestions = response.suggestions;
			// Initially select all suggestions
			selectedSuggestions = new Set(suggestions.map((_, idx) => idx));
			step = 'preview';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to generate menu suggestions';
			console.error('Failed to generate menu:', err);
		} finally {
			generating = false;
		}
	}

	function toggleSuggestion(index: number) {
		if (selectedSuggestions.has(index)) {
			selectedSuggestions.delete(index);
		} else {
			selectedSuggestions.add(index);
		}
		selectedSuggestions = selectedSuggestions;
	}

	async function handleApplyToMealPlan() {
		error = null;
		applying = true;

		try {
			// Get current week's meal plan
			const weekStartStr = formatDateISO(getWeekStart());
			const mealPlan = await getCurrentWeekMealPlan(weekStartStr);

			// Apply selected suggestions to the meal plan
			for (const [index, suggestion] of suggestions.entries()) {
				if (!selectedSuggestions.has(index)) continue;

				// Only add if there's a recipe_id (catalog-first mode)
				if (suggestion.recipe_id) {
					await addPlannedMeal({
						meal_plan_id: mealPlan.id,
						recipe_id: suggestion.recipe_id,
						day_of_week: suggestion.day - 1, // Convert 1-indexed to 0-indexed
						meal_type: suggestion.meal_type,
						servings: 4,
						notes: suggestion.description || null
					});
				}
			}

			// Navigate to meal plans page
			goto('/meal-plans');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to apply suggestions to meal plan';
			console.error('Failed to apply suggestions:', err);
		} finally {
			applying = false;
		}
	}

	function goBack() {
		step = 'config';
	}

	function regenerate() {
		step = 'config';
		suggestions = [];
		selectedSuggestions = new Set();
	}

	// Group suggestions by day
	function getSuggestionsForDay(day: number): MealSuggestion[] {
		return suggestions.filter((s) => s.day === day);
	}

	const dayNames = ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'];
</script>

<svelte:head>
	<title>AI Menu Suggestions - Recipe Catalog</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-4xl">
	<div class="mb-6">
		<h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">AI Menu Suggestions</h1>
		<p class="text-gray-600 dark:text-gray-400">
			Generate personalized menu plans for your week using AI
		</p>
	</div>

	{#if error}
		<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 px-4 py-3 rounded mb-4">
			{error}
		</div>
	{/if}

	{#if step === 'config'}
		<!-- Configuration Step -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 space-y-6">
			<!-- Time Range -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Number of Days
				</label>
				<input
					type="number"
					min="1"
					max="14"
					bind:value={days}
					class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
				/>
			</div>

			<!-- Meal Types -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Meal Types to Include
				</label>
				<div class="grid grid-cols-2 md:grid-cols-4 gap-2">
					{#each mealTypeOptions as mealType}
						<button
							type="button"
							on:click={() => toggleMealType(mealType)}
							class="px-4 py-2 rounded-md border transition-colors capitalize {selectedMealTypes.has(
								mealType
							)
								? 'bg-blue-600 text-white border-blue-600'
								: 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'}"
						>
							{mealType}
						</button>
					{/each}
				</div>
			</div>

			<!-- Dietary Preferences -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Dietary Preferences
				</label>
				<div class="grid grid-cols-2 md:grid-cols-3 gap-2">
					{#each dietaryOptions as option}
						<button
							type="button"
							on:click={() => toggleDietary(option)}
							class="px-4 py-2 rounded-md border text-sm transition-colors {dietaryPreferences.includes(
								option
							)
								? 'bg-green-600 text-white border-green-600'
								: 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'}"
						>
							{option}
						</button>
					{/each}
				</div>
			</div>

			<!-- Cuisine Preference -->
			<div>
				<label for="cuisine" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Cuisine Preference (Optional)
				</label>
				<input
					id="cuisine"
					type="text"
					bind:value={cuisine}
					placeholder="e.g., Italian, Mexican, Asian"
					class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
				/>
			</div>

			<!-- Generation Mode -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Generation Mode
				</label>
				<div class="space-y-2">
					<label class="flex items-start cursor-pointer">
						<input
							type="radio"
							bind:group={mode}
							value="catalog-first"
							class="mt-1 mr-3"
						/>
						<div>
							<div class="font-medium text-gray-900 dark:text-white">Catalog First</div>
							<div class="text-sm text-gray-600 dark:text-gray-400">
								Use recipes from your household catalog when possible
							</div>
						</div>
					</label>
					<label class="flex items-start cursor-pointer">
						<input
							type="radio"
							bind:group={mode}
							value="ai-only"
							class="mt-1 mr-3"
						/>
						<div>
							<div class="font-medium text-gray-900 dark:text-white">AI Only</div>
							<div class="text-sm text-gray-600 dark:text-gray-400">
								Generate completely new recipe suggestions
							</div>
						</div>
					</label>
				</div>
			</div>

			<!-- Generate Button -->
			<div class="flex justify-end space-x-3 pt-4">
				<button
					type="button"
					on:click={() => goto('/meal-plans')}
					class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
				>
					Cancel
				</button>
				<button
					type="button"
					on:click={handleGenerate}
					disabled={generating}
					class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{generating ? 'Generating...' : 'Generate Menu'}
				</button>
			</div>
		</div>
	{:else if step === 'preview'}
		<!-- Preview Step -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
			<div class="mb-4">
				<h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">Menu Suggestions</h2>
				<p class="text-sm text-gray-600 dark:text-gray-400">
					Select the meals you want to add to your meal plan
				</p>
			</div>

			<div class="space-y-6">
				{#each Array.from({ length: days }, (_, i) => i + 1) as day}
					{@const daySuggestions = getSuggestionsForDay(day)}
					{#if daySuggestions.length > 0}
						<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
							<h3 class="font-medium text-gray-900 dark:text-white mb-3">
								{day <= 7 ? dayNames[day - 1] : `Day ${day}`}
							</h3>
							<div class="space-y-2">
								{#each daySuggestions as suggestion, idx}
									{@const suggestionIndex = suggestions.indexOf(suggestion)}
									<label
										class="flex items-start p-3 rounded-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
									>
										<input
											type="checkbox"
											checked={selectedSuggestions.has(suggestionIndex)}
											on:change={() => toggleSuggestion(suggestionIndex)}
											class="mt-1 mr-3"
										/>
										<div class="flex-1">
											<div class="flex items-start justify-between">
												<div>
													<div class="font-medium text-gray-900 dark:text-white capitalize">
														{suggestion.meal_type}: {suggestion.recipe_name}
													</div>
													{#if suggestion.description}
														<div class="text-sm text-gray-600 dark:text-gray-400 mt-1">
															{suggestion.description}
														</div>
													{/if}
													<div class="text-xs text-gray-500 dark:text-gray-500 mt-1">
														{#if suggestion.recipe_id}
															<span class="inline-flex items-center px-2 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
																From Catalog
															</span>
														{:else}
															<span class="inline-flex items-center px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
																AI Suggestion
															</span>
														{/if}
														{#if suggestion.prep_time || suggestion.cook_time}
															<span class="ml-2">
																{suggestion.prep_time || ''} {suggestion.cook_time || ''}
															</span>
														{/if}
													</div>
												</div>
											</div>
										</div>
									</label>
								{/each}
							</div>
						</div>
					{/if}
				{/each}
			</div>

			{#if mode === 'ai-only'}
				<div class="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
					<p class="text-sm text-yellow-800 dark:text-yellow-200">
						<strong>Note:</strong> These are AI-generated suggestions. To add them to your meal plan,
						you'll need to first create these recipes in your catalog.
					</p>
				</div>
			{/if}

			<!-- Action Buttons -->
			<div class="flex justify-between space-x-3 pt-6 mt-6 border-t border-gray-200 dark:border-gray-700">
				<button
					type="button"
					on:click={regenerate}
					class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
				>
					Regenerate
				</button>
				<div class="flex space-x-3">
					<button
						type="button"
						on:click={goBack}
						class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
					>
						Back
					</button>
					{#if mode === 'catalog-first'}
						<button
							type="button"
							on:click={handleApplyToMealPlan}
							disabled={applying || selectedSuggestions.size === 0}
							class="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{applying ? 'Applying...' : `Apply ${selectedSuggestions.size} to Meal Plan`}
						</button>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
