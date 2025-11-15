<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let selectedCuisines: string[] = [];
	export let selectedCategories: string[] = [];
	export let selectedSourceTypes: string[] = [];
	export let maxTime: number | undefined = undefined;
	export let minTime: number | undefined = undefined;

	const dispatch = createEventDispatcher();

	// Available filter options
	const cuisineOptions = [
		'Italian',
		'Mexican',
		'Chinese',
		'Japanese',
		'Indian',
		'Thai',
		'French',
		'Greek',
		'Spanish',
		'Mediterranean',
		'American',
		'Korean',
		'Vietnamese',
		'Middle Eastern',
		'Other'
	];

	const categoryOptions = [
		'Breakfast',
		'Lunch',
		'Dinner',
		'Appetizer',
		'Main Course',
		'Side Dish',
		'Dessert',
		'Snack',
		'Beverage',
		'Salad',
		'Soup',
		'Pasta',
		'Bread',
		'Sauce',
		'Other'
	];

	const sourceTypeOptions = [
		{ value: 'imported', label: 'Imported' },
		{ value: 'manual', label: 'Manual Entry' }
	];

	const timePresets = [
		{ label: 'Under 15 min', max: 15 },
		{ label: 'Under 30 min', max: 30 },
		{ label: 'Under 1 hour', max: 60 },
		{ label: 'Under 2 hours', max: 120 }
	];

	// Toggle functions
	function toggleCuisine(cuisine: string) {
		if (selectedCuisines.includes(cuisine)) {
			selectedCuisines = selectedCuisines.filter((c) => c !== cuisine);
		} else {
			selectedCuisines = [...selectedCuisines, cuisine];
		}
		emitChange();
	}

	function toggleCategory(category: string) {
		if (selectedCategories.includes(category)) {
			selectedCategories = selectedCategories.filter((c) => c !== category);
		} else {
			selectedCategories = [...selectedCategories, category];
		}
		emitChange();
	}

	function toggleSourceType(sourceType: string) {
		if (selectedSourceTypes.includes(sourceType)) {
			selectedSourceTypes = selectedSourceTypes.filter((s) => s !== sourceType);
		} else {
			selectedSourceTypes = [...selectedSourceTypes, sourceType];
		}
		emitChange();
	}

	function setTimePreset(max: number) {
		maxTime = max;
		minTime = undefined;
		emitChange();
	}

	function clearTimeFilters() {
		maxTime = undefined;
		minTime = undefined;
		emitChange();
	}

	function clearAllFilters() {
		selectedCuisines = [];
		selectedCategories = [];
		selectedSourceTypes = [];
		maxTime = undefined;
		minTime = undefined;
		emitChange();
	}

	function emitChange() {
		dispatch('change', {
			selectedCuisines,
			selectedCategories,
			selectedSourceTypes,
			maxTime,
			minTime
		});
	}

	// Count active filters
	$: activeFilterCount =
		selectedCuisines.length +
		selectedCategories.length +
		selectedSourceTypes.length +
		(maxTime !== undefined || minTime !== undefined ? 1 : 0);
</script>

<aside class="filter-sidebar">
	<div class="filter-header">
		<h2 class="filter-title">Filters</h2>
		{#if activeFilterCount > 0}
			<button on:click={clearAllFilters} class="clear-all-btn"> Clear All ({activeFilterCount}) </button
			>
		{/if}
	</div>

	<!-- Cuisine Filter -->
	<div class="filter-section">
		<h3 class="filter-section-title">
			Cuisine
			{#if selectedCuisines.length > 0}
				<span class="filter-count">({selectedCuisines.length})</span>
			{/if}
		</h3>
		<div class="filter-options">
			{#each cuisineOptions as cuisine}
				<label class="filter-checkbox">
					<input
						type="checkbox"
						checked={selectedCuisines.includes(cuisine)}
						on:change={() => toggleCuisine(cuisine)}
					/>
					<span class="checkbox-label">{cuisine}</span>
				</label>
			{/each}
		</div>
	</div>

	<!-- Category Filter -->
	<div class="filter-section">
		<h3 class="filter-section-title">
			Category
			{#if selectedCategories.length > 0}
				<span class="filter-count">({selectedCategories.length})</span>
			{/if}
		</h3>
		<div class="filter-options">
			{#each categoryOptions as category}
				<label class="filter-checkbox">
					<input
						type="checkbox"
						checked={selectedCategories.includes(category)}
						on:change={() => toggleCategory(category)}
					/>
					<span class="checkbox-label">{category}</span>
				</label>
			{/each}
		</div>
	</div>

	<!-- Source Type Filter -->
	<div class="filter-section">
		<h3 class="filter-section-title">
			Source Type
			{#if selectedSourceTypes.length > 0}
				<span class="filter-count">({selectedSourceTypes.length})</span>
			{/if}
		</h3>
		<div class="filter-options">
			{#each sourceTypeOptions as option}
				<label class="filter-checkbox">
					<input
						type="checkbox"
						checked={selectedSourceTypes.includes(option.value)}
						on:change={() => toggleSourceType(option.value)}
					/>
					<span class="checkbox-label">{option.label}</span>
				</label>
			{/each}
		</div>
	</div>

	<!-- Time Filter -->
	<div class="filter-section">
		<h3 class="filter-section-title">
			Cooking Time
			{#if maxTime !== undefined || minTime !== undefined}
				<button on:click={clearTimeFilters} class="clear-section-btn">Clear</button>
			{/if}
		</h3>

		<!-- Time Presets -->
		<div class="time-presets">
			{#each timePresets as preset}
				<button
					on:click={() => setTimePreset(preset.max)}
					class="time-preset-btn"
					class:active={maxTime === preset.max && minTime === undefined}
				>
					{preset.label}
				</button>
			{/each}
		</div>

		<!-- Custom Time Range -->
		<div class="time-custom">
			<label class="time-input-label">
				Min (minutes)
				<input
					type="number"
					min="0"
					max={maxTime || 999}
					bind:value={minTime}
					on:change={emitChange}
					placeholder="0"
					class="time-input"
				/>
			</label>
			<label class="time-input-label">
				Max (minutes)
				<input
					type="number"
					min={minTime || 0}
					max="999"
					bind:value={maxTime}
					on:change={emitChange}
					placeholder="Any"
					class="time-input"
				/>
			</label>
		</div>
	</div>
</aside>

<style>
	.filter-sidebar {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
		height: fit-content;
		position: sticky;
		top: 1rem;
		max-height: calc(100vh - 2rem);
		overflow-y: auto;
	}

	.filter-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.5rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid var(--neutral-200);
	}

	.filter-title {
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0;
	}

	.clear-all-btn {
		padding: 0.25rem 0.75rem;
		font-size: 0.875rem;
		color: var(--accent-600);
		background: transparent;
		border: 1px solid var(--accent-300);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.clear-all-btn:hover {
		background: var(--accent-50);
		border-color: var(--accent-500);
	}

	.filter-section {
		margin-bottom: 1.5rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid var(--neutral-100);
	}

	.filter-section:last-child {
		border-bottom: none;
		margin-bottom: 0;
		padding-bottom: 0;
	}

	.filter-section-title {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-700);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0 0 0.75rem 0;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.filter-count {
		font-size: 0.75rem;
		color: var(--accent-600);
		font-weight: 500;
	}

	.clear-section-btn {
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--accent-600);
		background: transparent;
		border: none;
		cursor: pointer;
		text-transform: none;
		letter-spacing: normal;
		padding: 0;
		transition: color var(--transition-fast);
	}

	.clear-section-btn:hover {
		color: var(--accent-700);
		text-decoration: underline;
	}

	.filter-options {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.filter-checkbox {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		padding: 0.25rem 0;
	}

	.filter-checkbox input[type='checkbox'] {
		width: 1rem;
		height: 1rem;
		cursor: pointer;
		accent-color: var(--accent-500);
	}

	.checkbox-label {
		font-size: 0.875rem;
		color: var(--text-700);
		user-select: none;
	}

	.filter-checkbox:hover .checkbox-label {
		color: var(--text-900);
	}

	.time-presets {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.time-preset-btn {
		padding: 0.5rem 0.75rem;
		font-size: 0.875rem;
		color: var(--text-700);
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
		text-align: left;
	}

	.time-preset-btn:hover {
		background: var(--accent-50);
		border-color: var(--accent-300);
		color: var(--accent-700);
	}

	.time-preset-btn.active {
		background: var(--accent-500);
		border-color: var(--accent-500);
		color: var(--neutral-white);
		font-weight: 500;
	}

	.time-custom {
		display: flex;
		gap: 0.75rem;
	}

	.time-input-label {
		flex: 1;
		font-size: 0.75rem;
		color: var(--text-600);
		font-weight: 500;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.time-input {
		padding: 0.5rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		color: var(--text-900);
		transition: all var(--transition-fast);
	}

	.time-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	/* Custom scrollbar for filter sidebar */
	.filter-sidebar::-webkit-scrollbar {
		width: 0.5rem;
	}

	.filter-sidebar::-webkit-scrollbar-track {
		background: var(--neutral-100);
		border-radius: var(--radius-md);
	}

	.filter-sidebar::-webkit-scrollbar-thumb {
		background: var(--neutral-300);
		border-radius: var(--radius-md);
	}

	.filter-sidebar::-webkit-scrollbar-thumb:hover {
		background: var(--neutral-400);
	}
</style>
