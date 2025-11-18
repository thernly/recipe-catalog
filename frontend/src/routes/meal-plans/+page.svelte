<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getCurrentWeekMealPlan,
		addPlannedMeal,
		deletePlannedMeal,
		getWeekStart,
		formatDateISO,
		getWeekDates,
		type MealPlan,
		type PlannedMeal,
		type PlannedMealCreate
	} from '$lib/api/meal-plans';
	import { searchRecipes, type RecipeSummary } from '$lib/api/recipes';
	import AddMealDialog from './AddMealDialog.svelte';
	import EditMealDialog from './EditMealDialog.svelte';

	let mealPlan: MealPlan | null = null;
	let loading = true;
	let error: string | null = null;
	let currentWeekStart: Date = getWeekStart();
	let weekDates: Date[] = [];

	// Dialog states
	let showAddDialog = false;
	let addDialogDay: number = 0;
	let addDialogMealType: string = 'dinner';
	let selectedMeal: PlannedMeal | null = null;
	let showEditDialog = false;

	const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
	const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'];

	$: weekDates = getWeekDates(currentWeekStart);

	async function loadMealPlan() {
		loading = true;
		error = null;

		try {
			const weekStartStr = formatDateISO(currentWeekStart);
			mealPlan = await getCurrentWeekMealPlan(weekStartStr);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load meal plan';
			console.error('Failed to load meal plan:', err);
		} finally {
			loading = false;
		}
	}

	function previousWeek() {
		const newDate = new Date(currentWeekStart);
		newDate.setDate(newDate.getDate() - 7);
		currentWeekStart = newDate;
		loadMealPlan();
	}

	function nextWeek() {
		const newDate = new Date(currentWeekStart);
		newDate.setDate(newDate.getDate() + 7);
		currentWeekStart = newDate;
		loadMealPlan();
	}

	function currentWeek() {
		currentWeekStart = getWeekStart();
		loadMealPlan();
	}

	function getMealsForCell(day: number, mealType: string): PlannedMeal[] {
		if (!mealPlan) return [];
		return mealPlan.planned_meals.filter(
			(meal) => meal.day_of_week === day && meal.meal_type === mealType
		);
	}

	function openAddDialog(day: number, mealType: string) {
		addDialogDay = day;
		addDialogMealType = mealType;
		showAddDialog = true;
	}

	function openEditDialog(meal: PlannedMeal) {
		selectedMeal = meal;
		showEditDialog = true;
	}

	async function handleMealAdded() {
		showAddDialog = false;
		await loadMealPlan();
	}

	async function handleMealUpdated() {
		showEditDialog = false;
		selectedMeal = null;
		await loadMealPlan();
	}

	async function handleMealDeleted() {
		showEditDialog = false;
		selectedMeal = null;
		await loadMealPlan();
	}

	function formatDate(date: Date): string {
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	function isToday(date: Date): boolean {
		const today = new Date();
		return (
			date.getDate() === today.getDate() &&
			date.getMonth() === today.getMonth() &&
			date.getFullYear() === today.getFullYear()
		);
	}

	onMount(() => {
		loadMealPlan();
	});
</script>

<div class="meal-planning-container">
	<div class="header">
		<h1>Meal Planning</h1>
		<div class="week-navigation">
			<button on:click={previousWeek} class="btn-secondary">
				<span>&larr;</span> Previous Week
			</button>
			<button on:click={currentWeek} class="btn-secondary">This Week</button>
			<button on:click={nextWeek} class="btn-secondary">
				Next Week <span>&rarr;</span>
			</button>
		</div>
	</div>

	{#if loading}
		<div class="loading">Loading meal plan...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else if mealPlan}
		<div class="week-header">
			<h2>
				Week of {formatDate(weekDates[0])} - {formatDate(weekDates[6])}
			</h2>
		</div>

		<div class="meal-grid">
			<!-- Header row with meal types -->
			<div class="grid-header"></div>
			{#each mealTypes as mealType}
				<div class="grid-header meal-type-header">
					{mealType.charAt(0).toUpperCase() + mealType.slice(1)}
				</div>
			{/each}

			<!-- Grid rows for each day -->
			{#each weekDates as date, dayIndex}
				<div class="day-header" class:today={isToday(date)}>
					<div class="day-name">{dayNames[dayIndex]}</div>
					<div class="day-date">{formatDate(date)}</div>
				</div>

				{#each mealTypes as mealType}
					<div
						class="meal-cell"
						on:click={() => openAddDialog(dayIndex, mealType)}
						on:keydown={(e) => e.key === 'Enter' && openAddDialog(dayIndex, mealType)}
						role="button"
						tabindex="0"
					>
						{#each getMealsForCell(dayIndex, mealType) as meal}
							<div
								class="meal-item"
								on:click|stopPropagation={() => openEditDialog(meal)}
								on:keydown|stopPropagation={(e) => e.key === 'Enter' && openEditDialog(meal)}
								role="button"
								tabindex="0"
							>
								<div class="meal-name">Recipe #{meal.recipe_id}</div>
								{#if meal.servings}
									<div class="meal-servings">{meal.servings} servings</div>
								{/if}
								{#if meal.notes}
									<div class="meal-notes" title={meal.notes}>📝</div>
								{/if}
							</div>
						{/each}
						<div class="add-meal-hint">+ Add meal</div>
					</div>
				{/each}
			{/each}
		</div>
	{/if}
</div>

{#if showAddDialog && mealPlan}
	<AddMealDialog
		{mealPlan}
		day={addDialogDay}
		mealType={addDialogMealType}
		on:close={() => (showAddDialog = false)}
		on:mealAdded={handleMealAdded}
	/>
{/if}

{#if showEditDialog && selectedMeal && mealPlan}
	<EditMealDialog
		{mealPlan}
		meal={selectedMeal}
		on:close={() => {
			showEditDialog = false;
			selectedMeal = null;
		}}
		on:mealUpdated={handleMealUpdated}
		on:mealDeleted={handleMealDeleted}
	/>
{/if}

<style>
	.meal-planning-container {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	h1 {
		font-size: 2rem;
		margin: 0;
	}

	.week-navigation {
		display: flex;
		gap: 0.5rem;
	}

	.week-header {
		margin-bottom: 1.5rem;
	}

	.week-header h2 {
		font-size: 1.5rem;
		margin: 0;
	}

	.meal-grid {
		display: grid;
		grid-template-columns: 150px repeat(4, 1fr);
		gap: 1px;
		background-color: #ddd;
		border: 1px solid #ddd;
	}

	.grid-header {
		background-color: #f5f5f5;
		padding: 1rem;
		font-weight: 600;
		text-align: center;
	}

	.meal-type-header {
		text-transform: capitalize;
	}

	.day-header {
		background-color: #f9f9f9;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.day-header.today {
		background-color: #e3f2fd;
		font-weight: 600;
	}

	.day-name {
		font-weight: 600;
		margin-bottom: 0.25rem;
	}

	.day-date {
		font-size: 0.875rem;
		color: #666;
	}

	.meal-cell {
		background-color: white;
		padding: 0.75rem;
		min-height: 100px;
		cursor: pointer;
		position: relative;
		transition: background-color 0.2s;
	}

	.meal-cell:hover {
		background-color: #f9f9f9;
	}

	.meal-cell:focus {
		outline: 2px solid #2196f3;
		outline-offset: -2px;
	}

	.meal-item {
		background-color: #e3f2fd;
		border: 1px solid #90caf9;
		border-radius: 4px;
		padding: 0.5rem;
		margin-bottom: 0.5rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.meal-item:hover {
		background-color: #bbdefb;
		transform: translateY(-1px);
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.meal-item:focus {
		outline: 2px solid #2196f3;
		outline-offset: 2px;
	}

	.meal-name {
		font-weight: 500;
		margin-bottom: 0.25rem;
	}

	.meal-servings {
		font-size: 0.875rem;
		color: #666;
	}

	.meal-notes {
		font-size: 0.875rem;
		margin-top: 0.25rem;
	}

	.add-meal-hint {
		color: #999;
		font-size: 0.875rem;
		text-align: center;
		padding: 0.5rem;
	}

	.meal-cell:hover .add-meal-hint {
		color: #2196f3;
	}

	.loading,
	.error {
		text-align: center;
		padding: 2rem;
		font-size: 1.125rem;
	}

	.error {
		color: #d32f2f;
	}

	.btn-secondary {
		padding: 0.5rem 1rem;
		background-color: white;
		border: 1px solid #ddd;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 1rem;
	}

	.btn-secondary:hover {
		background-color: #f5f5f5;
		border-color: #999;
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.meal-planning-container {
			padding: 1rem;
		}

		.header {
			flex-direction: column;
			align-items: stretch;
		}

		.week-navigation {
			flex-direction: column;
		}

		.meal-grid {
			grid-template-columns: 1fr;
			gap: 1rem;
			background-color: transparent;
			border: none;
		}

		.grid-header {
			display: none;
		}

		.day-header {
			border-radius: 8px 8px 0 0;
			border: 1px solid #ddd;
			border-bottom: none;
		}

		.meal-cell {
			border: 1px solid #ddd;
			border-top: none;
		}

		.meal-cell:last-child {
			border-radius: 0 0 8px 8px;
			margin-bottom: 1rem;
		}
	}
</style>
