<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
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
	import { generateFromMealPlan, createShoppingList } from '$lib/api/shopping-lists';
	import AddMealDialog from './AddMealDialog.svelte';
	import EditMealDialog from './EditMealDialog.svelte';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';

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

	// Shopping list generation
	let generatingShoppingList = false;
	let creatingBlankList = false;

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

	async function handleGenerateShoppingList() {
		if (!mealPlan || mealPlan.planned_meals.length === 0) {
			toast.error('No meals in this meal plan to generate a shopping list from.');
			return;
		}

		generatingShoppingList = true;
		try {
			const newList = await generateFromMealPlan({
				meal_plan_id: mealPlan.id,
				list_name: `Shopping list for week of ${formatDate(weekDates[0])}`
			});
			goto(`/shopping-lists/${newList.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to generate shopping list';
			console.error('Failed to generate shopping list:', err);
		} finally {
			generatingShoppingList = false;
		}
	}

	async function handleCreateBlankList() {
		creatingBlankList = true;
		try {
			const newList = await createShoppingList({
				name: `Shopping list for week of ${formatDate(weekDates[0])}`,
				description: 'Blank shopping list'
			});
			goto(`/shopping-lists/${newList.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create shopping list';
			console.error('Failed to create shopping list:', err);
		} finally {
			creatingBlankList = false;
		}
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

	<div class="actions-bar" style="text-align: center; margin-bottom: 1rem; display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
		<button
			on:click={() => goto('/ai-menu')}
			class="btn-ai-menu"
		>
			✨ AI Menu Suggestions
		</button>
		{#if mealPlan && mealPlan.planned_meals.length > 0}
			<button
				on:click={handleGenerateShoppingList}
				class="btn-primary"
				disabled={generatingShoppingList}
			>
				{generatingShoppingList ? '⏳ Generating...' : '🛒 Generate Shopping List from Meal Plan'}
			</button>
		{/if}
		<button
			on:click={handleCreateBlankList}
			class="btn-secondary"
			disabled={creatingBlankList}
		>
			{creatingBlankList ? '⏳ Creating...' : '📝 Create Blank Shopping List'}
		</button>
	</div>

	{#if loading}
		<!-- Skeleton loading for meal plan grid -->
		<div class="week-header">
			<div class="skeleton-week-title"></div>
		</div>
		<div class="meal-grid" role="status" aria-label="Loading meal plan">
			{#each dayNames as day, dayIndex}
				<div class="day-column">
					<div class="day-header">
						<div class="skeleton-day-name"></div>
						<div class="skeleton-date"></div>
					</div>
					{#each mealTypes as mealType}
						<div class="meal-cell">
							<div class="meal-type-header">{mealType}</div>
							<div class="skeleton-meal"></div>
						</div>
					{/each}
				</div>
			{/each}
		</div>
		<p class="sr-only">Loading meal plan...</p>
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
								<div class="meal-name">{meal.recipe_name || `Recipe #${meal.recipe_id}`}</div>
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
		gap: var(--space-sm);
		background-color: transparent;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.grid-header {
		background-color: var(--neutral-100);
		padding: var(--space-md);
		font-weight: 600;
		text-align: center;
		color: var(--text-700);
	}

	.meal-type-header {
		text-transform: capitalize;
	}

	.day-header {
		background-color: var(--neutral-50);
		padding: var(--space-md);
		display: flex;
		flex-direction: column;
		justify-content: center;
		border-right: 1px solid var(--neutral-200);
	}

	.day-header.today {
		background: linear-gradient(135deg, var(--accent-50) 0%, var(--accent-100) 100%);
		border-left: 3px solid var(--accent-500);
		font-weight: 600;
	}

	.day-name {
		font-weight: 600;
		margin-bottom: var(--space-xs);
		color: var(--text-900);
	}

	.day-date {
		font-size: 0.875rem;
		color: var(--text-600);
	}

	.day-header.today .day-date {
		color: var(--accent-700);
	}

	.meal-cell {
		background-color: var(--neutral-white);
		padding: var(--space-sm);
		min-height: 100px;
		cursor: pointer;
		position: relative;
		transition: all var(--transition-base);
		border: 1px dashed var(--neutral-300);
		border-radius: var(--radius-md);
	}

	.meal-cell:hover {
		background-color: var(--accent-50);
		border-color: var(--accent-300);
	}

	.meal-cell:focus {
		outline: 2px solid var(--accent-500);
		outline-offset: -2px;
	}

	.meal-cell:has(.meal-item) {
		border-style: solid;
		border-color: var(--neutral-200);
	}

	.meal-item {
		background-color: var(--accent-50);
		border: 1px solid var(--accent-200);
		border-radius: var(--radius-md);
		padding: var(--space-sm);
		margin-bottom: var(--space-sm);
		cursor: pointer;
		transition: all var(--transition-base);
	}

	.meal-item:hover {
		background-color: var(--accent-100);
		transform: translateY(-1px);
		box-shadow: var(--shadow-sm);
	}

	.meal-item:focus {
		outline: 2px solid var(--accent-500);
		outline-offset: 2px;
	}

	.meal-name {
		font-weight: 500;
		margin-bottom: var(--space-xs);
		color: var(--text-900);
	}

	.meal-servings {
		font-size: 0.875rem;
		color: var(--text-600);
	}

	.meal-notes {
		font-size: 0.875rem;
		margin-top: var(--space-xs);
	}

	.add-meal-hint {
		color: var(--text-400);
		font-size: 0.875rem;
		text-align: center;
		padding: var(--space-sm);
	}

	.meal-cell:hover .add-meal-hint {
		color: var(--accent-600);
	}

	.error {
		text-align: center;
		padding: 2rem;
		font-size: 1.125rem;
		color: var(--color-error);
	}

	.btn-secondary {
		padding: var(--space-sm) var(--space-md);
		background-color: var(--neutral-white);
		border: 1px solid var(--neutral-300);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-base);
		font-size: 1rem;
		color: var(--text-700);
	}

	.btn-secondary:hover {
		background-color: var(--neutral-100);
		border-color: var(--neutral-400);
	}

	.btn-ai-menu {
		background: linear-gradient(135deg, var(--accent-500) 0%, var(--accent-700) 100%);
		color: var(--neutral-white);
		border: none;
		padding: var(--space-sm) var(--space-md);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-base);
		font-size: 1rem;
	}

	.btn-ai-menu:hover {
		box-shadow: var(--shadow-warm-glow);
		transform: translateY(-1px);
	}

	/* Mobile responsiveness */
	@media (max-width: 768px) {
		.meal-planning-container {
			padding: var(--space-md);
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
			gap: var(--space-md);
			background-color: transparent;
			border: none;
		}

		.grid-header {
			display: none;
		}

		.day-header {
			border-radius: var(--radius-lg) var(--radius-lg) 0 0;
			border: 1px solid var(--neutral-200);
			border-bottom: none;
		}

		.meal-cell {
			border: 1px solid var(--neutral-200);
			border-top: none;
			border-radius: 0;
		}

		.meal-cell:last-child {
			border-radius: 0 0 var(--radius-lg) var(--radius-lg);
			margin-bottom: var(--space-md);
		}
	}

	/* Skeleton Loading */
	.skeleton-week-title {
		height: 1.75rem;
		width: 280px;
		background: linear-gradient(
			90deg,
			var(--neutral-100) 25%,
			var(--neutral-200) 50%,
			var(--neutral-100) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-md);
		margin: 0 auto;
	}

	.skeleton-day-name {
		height: 1.125rem;
		width: 80px;
		background: linear-gradient(
			90deg,
			var(--neutral-100) 25%,
			var(--neutral-200) 50%,
			var(--neutral-100) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-sm);
		margin-bottom: 0.25rem;
	}

	.skeleton-date {
		height: 0.875rem;
		width: 50px;
		background: linear-gradient(
			90deg,
			var(--neutral-100) 25%,
			var(--neutral-200) 50%,
			var(--neutral-100) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-sm);
	}

	.skeleton-meal {
		height: 3rem;
		width: 100%;
		background: linear-gradient(
			90deg,
			var(--neutral-100) 25%,
			var(--neutral-200) 50%,
			var(--neutral-100) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-md);
		margin-top: 0.5rem;
	}

	@keyframes shimmer {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}
</style>
