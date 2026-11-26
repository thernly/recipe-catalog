<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		addPlannedMeal,
		getCurrentWeekMealPlan,
		getWeekStart,
		formatDateISO,
		getWeekDates,
		mealName,
		type MealPlan,
		type PlannedMeal,
	} from '#lib/api/meal-plans.js';
	import {
		generateFromMealPlan,
		previewFromMealPlan,
		createShoppingList,
		formatQuantityUnit,
		setLastShoppingListId,
		type ShoppingItemPreview,
	} from '#lib/api/shopping-lists.js';
	import AddToShoppingListDialog from '#lib/components/AddToShoppingListDialog.svelte';
	import AddMealDialog from './AddMealDialog.svelte';
	import EditMealDialog from './EditMealDialog.svelte';
	import { toast } from '#lib/stores/toast.js';
	import { dialog } from '#lib/stores/dialog.js';
	import { downloadBlob } from '#lib/utils/download.js';
	import { mealPlanToIcs } from '#lib/utils/meal-plan-calendar.js';
	import {
		rememberAddedToList,
		wasAddedToList,
	} from '#lib/utils/added-weeks.js';

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
	let showAddToListDialog = false;

	// Adding a week to a list it is already on doubles every amount, so ask first
	function handleAddToExistingList(listId: number | null) {
		if (!mealPlan || !listId) return;
		if (!wasAddedToList(mealPlan.id, listId)) return addToList(listId);
		showAddToListDialog = false;
		dialog.show({
			title: 'Add This Week Again?',
			message:
				'This week has already been added to that list. Adding it again will double the amounts.',
			onConfirm: () => addToList(listId),
		});
	}

	// Meals unticked under "Meals to shop for" are left off the shopping list
	// (leftovers, a night out, something already bought). Reset with the week.
	// Free-text meals ("Leftovers") have no recipe, so nothing to shop for.
	let skippedMealIds: number[] = [];
	$: plannedMeals = (mealPlan?.planned_meals ?? [])
		.filter((meal) => meal.recipe_id != null)
		.sort(
			(a, b) =>
				a.day_of_week - b.day_of_week ||
				mealTypes.indexOf(a.meal_type) - mealTypes.indexOf(b.meal_type),
		);
	$: chosenMealIds = plannedMeals
		.map((meal) => meal.id)
		.filter((id) => !skippedMealIds.includes(id));

	function toggleMeal(id: number) {
		skippedMealIds = skippedMealIds.includes(id)
			? skippedMealIds.filter((skipped) => skipped !== id)
			: [...skippedMealIds, id];
	}

	// Only sent when some meal is left out; without it the server takes them all
	const chosenMeals = () =>
		chosenMealIds.length < plannedMeals.length
			? { selected_meal_ids: chosenMealIds }
			: {};

	// What the chosen meals would put on a list. Dropped whenever the meals or
	// the ticks change, so it never shows a stale answer.
	let preview: ShoppingItemPreview[] | null = null;
	let loadingPreview = false;
	$: if (chosenMealIds) preview = null;

	async function handlePreview() {
		if (!mealPlan) return;
		loadingPreview = true;
		try {
			preview = await previewFromMealPlan({
				meal_plan_id: mealPlan.id,
				...chosenMeals(),
			});
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : 'Failed to load the ingredients',
			);
		} finally {
			loadingPreview = false;
		}
	}

	async function addToList(listId: number) {
		if (!mealPlan) return;
		generatingShoppingList = true;
		try {
			await generateFromMealPlan({
				meal_plan_id: mealPlan.id,
				shopping_list_id: listId,
				...chosenMeals(),
			});
			rememberAddedToList(mealPlan.id, listId);
			setLastShoppingListId(listId);
			showAddToListDialog = false;
			toast.success('Meal plan ingredients added to your shopping list');
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : 'Failed to add to shopping list',
			);
		} finally {
			generatingShoppingList = false;
		}
	}

	const dayNames = [
		'Monday',
		'Tuesday',
		'Wednesday',
		'Thursday',
		'Friday',
		'Saturday',
		'Sunday',
	];
	// "Other" only gets a column when the week has such a meal; without one,
	// a meal moved to "Other" would disappear from the grid.
	$: mealTypes = [
		'breakfast',
		'lunch',
		'dinner',
		'snack',
		...(mealPlan?.planned_meals.some((meal) => meal.meal_type === 'other')
			? ['other']
			: []),
	];

	$: weekDates = getWeekDates(currentWeekStart);

	// keepPage: reload the week already on screen (after a meal is added, edited
	// or removed) without swapping the grid for the loading message, so the
	// scroll position survives. Changing week still shows the message.
	async function loadMealPlan(keepPage = false) {
		loading = !keepPage || !mealPlan;
		if (!keepPage) skippedMealIds = [];
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

	// "Today": this week, with today's row brought into view (on a phone the
	// week is a long list and today may be far down it)
	async function goToToday() {
		if (formatDateISO(currentWeekStart) !== formatDateISO(getWeekStart())) {
			currentWeekStart = getWeekStart();
			await loadMealPlan();
		}
		await tick();
		document
			.querySelector('.day-header.today')
			?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
	}

	// Copy last week: each of its meals is added to the week on screen, same
	// day and meal. Meals already here are kept.
	let copyingLastWeek = false;

	async function copyLastWeek() {
		if (!mealPlan) return;
		const targetId = mealPlan.id;
		copyingLastWeek = true;
		try {
			const previous = new Date(currentWeekStart);
			previous.setDate(previous.getDate() - 7);
			const lastWeek = await getCurrentWeekMealPlan(formatDateISO(previous));
			const meals = lastWeek.planned_meals;
			if (meals.length === 0) {
				toast.info('Last week has no meals to copy');
				return;
			}
			// One at a time: there is no bulk route, and a week is at most a few dozen
			for (const meal of meals) {
				await addPlannedMeal(targetId, {
					// A recipe meal, or a free-text one ("Leftovers")
					...(meal.recipe_id
						? { recipe_id: meal.recipe_id }
						: { title: meal.title ?? '' }),
					day_of_week: meal.day_of_week,
					meal_type: meal.meal_type,
					servings: meal.servings ?? undefined,
					notes: meal.notes ?? undefined,
				});
			}
			toast.success(
				`Copied ${meals.length} ${meals.length === 1 ? 'meal' : 'meals'} from last week`,
			);
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : 'Failed to copy last week',
			);
		} finally {
			copyingLastWeek = false;
			await loadMealPlan(true);
		}
	}

	function handleCopyLastWeek() {
		if (!mealPlan || mealPlan.planned_meals.length === 0) return copyLastWeek();
		dialog.show({
			title: 'Copy Last Week',
			message:
				"This week already has meals. Last week's meals will be added alongside them.",
			confirmLabel: 'Copy',
			danger: false,
			onConfirm: copyLastWeek,
		});
	}

	// The plan is a parameter, not read from the outer variable: the template
	// only re-runs this for a cell when something it is passed changes, so a
	// reload that keeps the grid on screen would otherwise leave cells stale.
	function getMealsForCell(
		plan: MealPlan | null,
		day: number,
		mealType: string,
	): PlannedMeal[] {
		if (!plan) return [];
		return plan.planned_meals.filter(
			(meal) => meal.day_of_week === day && meal.meal_type === mealType,
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
		await loadMealPlan(true);
	}

	async function handleMealUpdated() {
		showEditDialog = false;
		selectedMeal = null;
		await loadMealPlan(true);
	}

	async function handleMealDeleted() {
		showEditDialog = false;
		selectedMeal = null;
		await loadMealPlan(true);
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
			toast.error(
				'No meals in this meal plan to generate a shopping list from.',
			);
			return;
		}

		generatingShoppingList = true;
		try {
			const newList = await generateFromMealPlan({
				meal_plan_id: mealPlan.id,
				list_name: `Shopping list for week of ${formatDate(weekDates[0])}`,
				...chosenMeals(),
			});
			rememberAddedToList(mealPlan.id, newList.id);
			goto(`/shopping-lists/${newList.id}`);
		} catch (err) {
			error =
				err instanceof Error ? err.message : 'Failed to generate shopping list';
			console.error('Failed to generate shopping list:', err);
		} finally {
			generatingShoppingList = false;
		}
	}

	// A calendar file of the week on screen, for Google, Apple or Outlook
	function handleExportCalendar() {
		if (!mealPlan) return;
		downloadBlob(
			new Blob([mealPlanToIcs(mealPlan, location.origin)], {
				type: 'text/calendar',
			}),
			`meal-plan-${mealPlan.week_start_date}.ics`,
		);
	}

	async function handleCreateBlankList() {
		creatingBlankList = true;
		try {
			const newList = await createShoppingList({
				name: `Shopping list for week of ${formatDate(weekDates[0])}`,
				description: 'Blank shopping list',
			});
			goto(`/shopping-lists/${newList.id}`);
		} catch (err) {
			error =
				err instanceof Error ? err.message : 'Failed to create shopping list';
			console.error('Failed to create shopping list:', err);
		} finally {
			creatingBlankList = false;
		}
	}

	onMount(() => {
		loadMealPlan();
	});
</script>

<svelte:head>
	<title>Meal Plans - Recipe Catalog</title>
</svelte:head>

<div class="meal-planning-container">
	<div class="header">
		<h1>Meal Planning</h1>
		<div class="week-navigation">
			<button on:click={previousWeek} class="btn-secondary">
				<span>&larr;</span> Previous Week
			</button>
			<button on:click={goToToday} class="btn-secondary">Today</button>
			<button on:click={nextWeek} class="btn-secondary">
				Next Week <span>&rarr;</span>
			</button>
		</div>
	</div>

	<div
		class="actions-bar"
		style="text-align: center; margin-bottom: 1rem; display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;"
	>
		<button on:click={() => goto('/ai-menu')} class="btn-ai-menu">
			✨ AI Menu Suggestions
		</button>
		{#if mealPlan && mealPlan.planned_meals.length > 0}
			<button
				on:click={handleGenerateShoppingList}
				class="btn-primary"
				disabled={generatingShoppingList || chosenMealIds.length === 0}
			>
				{generatingShoppingList
					? '⏳ Generating...'
					: '🛒 Generate Shopping List from Meal Plan'}
			</button>
			<button
				on:click={() => (showAddToListDialog = true)}
				class="btn-secondary"
				disabled={generatingShoppingList || chosenMealIds.length === 0}
			>
				➕ Add to Existing List
			</button>
			<button on:click={handleExportCalendar} class="btn-secondary">
				📅 Export to Calendar
			</button>
		{/if}
		{#if mealPlan}
			<button
				on:click={handleCopyLastWeek}
				class="btn-secondary"
				disabled={copyingLastWeek}
			>
				{copyingLastWeek ? '⏳ Copying...' : '📋 Copy Last Week'}
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

	{#if plannedMeals.length > 0}
		<details class="meals-to-shop">
			<summary>
				Meals to shop for ({chosenMealIds.length} of {plannedMeals.length})
			</summary>
			<p>Untick a meal to leave its ingredients off the shopping list.</p>
			{#each plannedMeals as meal (meal.id)}
				<label>
					<input
						type="checkbox"
						checked={!skippedMealIds.includes(meal.id)}
						on:change={() => toggleMeal(meal.id)}
					/>
					{dayNames[meal.day_of_week]}
					{meal.meal_type}: {mealName(meal)}
				</label>
			{/each}
			<button
				type="button"
				on:click={handlePreview}
				class="btn-secondary"
				disabled={loadingPreview || chosenMealIds.length === 0}
			>
				{loadingPreview ? '⏳ Loading...' : 'Preview ingredients'}
			</button>
			{#if preview}
				{#if preview.length === 0}
					<p>These meals have no ingredients to shop for.</p>
				{:else}
					<ul aria-label="Ingredients these meals need">
						{#each preview as item, index (index)}
							<li>
								{item.item_name}
								{#if formatQuantityUnit(item.quantity, item.unit)}
									({formatQuantityUnit(item.quantity, item.unit)})
								{/if}
								{#if item.notes}<em>{item.notes}</em>{/if}
							</li>
						{/each}
					</ul>
				{/if}
			{/if}
		</details>
	{/if}

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

		<div class="meal-grid" style="--meal-columns: {mealTypes.length}">
			<!-- Header row with meal types -->
			<div class="grid-header"></div>
			{#each mealTypes as mealType (mealType)}
				<div class="grid-header meal-type-header">
					{mealType.charAt(0).toUpperCase() + mealType.slice(1)}
				</div>
			{/each}

			<!-- Grid rows for each day -->
			{#each weekDates as date, dayIndex (date.toISOString())}
				<div class="day-header" class:today={isToday(date)}>
					<div class="day-name">{dayNames[dayIndex]}</div>
					<div class="day-date">{formatDate(date)}</div>
				</div>

				{#each mealTypes as mealType (mealType)}
					<div class="meal-cell">
						<!-- Shown on narrow screens, where the header row is hidden -->
						<div class="cell-label">{mealType}</div>
						{#each getMealsForCell(mealPlan, dayIndex, mealType) as meal (meal.id)}
							<button
								type="button"
								class="meal-item"
								on:click={() => openEditDialog(meal)}
							>
								<span class="meal-name">
									{mealName(meal)}
								</span>
								{#if meal.servings}
									<span class="meal-servings">{meal.servings} servings</span>
								{/if}
								{#if meal.notes}
									<span class="meal-notes" title={meal.notes}>
										<span aria-hidden="true">📝</span><span class="sr-only">
											Has notes
										</span>
									</span>
								{/if}
							</button>
						{/each}
						<button
							type="button"
							class="add-meal-hint"
							aria-label="Add {mealType} on {dayNames[dayIndex]}"
							on:click={() => openAddDialog(dayIndex, mealType)}
						>
							+ Add meal
						</button>
					</div>
				{/each}
			{/each}
		</div>
	{/if}
</div>

<AddToShoppingListDialog
	open={showAddToListDialog}
	heading="Add meal plan ingredients to…"
	allowNew={false}
	busy={generatingShoppingList}
	onPick={handleAddToExistingList}
	onClose={() => (showAddToListDialog = false)}
/>

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

	.meals-to-shop {
		max-width: 32rem;
		margin: 0 auto 1rem;
		color: var(--text-700);
	}

	.meals-to-shop summary {
		cursor: pointer;
		text-align: center;
		color: var(--primary-600);
	}

	.meals-to-shop p {
		margin: 0.5rem 0;
		font-size: 0.875rem;
		color: var(--text-600);
	}

	.meals-to-shop label {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		padding: 0.375rem 0;
		text-transform: capitalize;
	}

	.meals-to-shop button {
		margin-top: 0.5rem;
	}

	.meals-to-shop ul {
		margin: 0.5rem 0 0;
		padding-left: 1.25rem;
		list-style: disc;
	}

	.meals-to-shop em {
		margin-left: 0.25rem;
		font-size: 0.875rem;
		color: var(--text-600);
	}

	.week-header h2 {
		font-size: 1.5rem;
		margin: 0;
	}

	.meal-grid {
		display: grid;
		grid-template-columns: 150px repeat(var(--meal-columns, 4), 1fr);
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
		background: linear-gradient(
			135deg,
			var(--accent-50) 0%,
			var(--accent-100) 100%
		);
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

	.meal-cell:has(.meal-item) {
		border-style: solid;
		border-color: var(--neutral-200);
	}

	.cell-label {
		display: none;
		text-transform: capitalize;
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-700);
		margin-bottom: var(--space-xs);
	}

	.meal-item {
		display: block;
		width: 100%;
		text-align: left;
		font: inherit;
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

	.meal-name,
	.meal-servings,
	.meal-notes {
		display: block;
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
		display: block;
		width: 100%;
		background: none;
		border: none;
		cursor: pointer;
		font: inherit;
		color: var(--text-400);
		font-size: 0.875rem;
		text-align: center;
		padding: var(--space-sm);
	}

	.meal-cell:hover .add-meal-hint {
		color: var(--accent-600);
	}

	.loading,
	.error {
		text-align: center;
		padding: 2rem;
		font-size: 1.125rem;
	}

	.error {
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

	/* Colours come from the global .btn-primary; the shape matches the
	   buttons beside it */
	.btn-primary {
		padding: var(--space-sm) var(--space-md);
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		font-size: 1rem;
	}

	.btn-ai-menu {
		background: linear-gradient(
			135deg,
			var(--accent-500) 0%,
			var(--accent-700) 100%
		);
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

		.cell-label {
			display: block;
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
</style>
