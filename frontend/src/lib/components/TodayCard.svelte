<script lang="ts">
	import { onMount } from 'svelte';
	import {
		listMealPlans,
		getMealPlan,
		getWeekStart,
		formatDateISO,
		type PlannedMeal,
	} from '#lib/api/meal-plans.js';
	import {
		listShoppingLists,
		type ShoppingListSummary,
	} from '#lib/api/shopping-lists.js';
	import { CalendarDays, ShoppingCart } from '@lucide/svelte';

	const MEAL_ORDER = ['breakfast', 'lunch', 'dinner', 'snack', 'other'];

	let loading = true;
	let meals: PlannedMeal[] = [];
	let shoppingList: ShoppingListSummary | null = null;

	// Looks the week up in the list of plans rather than asking for "the current
	// plan", which would create an empty one just because the dashboard was opened.
	async function loadMeals(today: Date) {
		const weekStart = formatDateISO(getWeekStart(today));
		const summary = (await listMealPlans()).find(
			(plan) =>
				plan.week_start_date.startsWith(weekStart) && plan.meal_count > 0,
		);
		if (!summary) return;
		const dayOfWeek = (today.getDay() + 6) % 7; // 0 = Monday, as the planner stores it
		meals = (await getMealPlan(summary.id)).planned_meals
			.filter((meal) => meal.day_of_week === dayOfWeek)
			.sort(
				(a, b) =>
					MEAL_ORDER.indexOf(a.meal_type) - MEAL_ORDER.indexOf(b.meal_type),
			);
	}

	async function loadShoppingList() {
		const lists = await listShoppingLists('active');
		// The newest active list is the one being shopped from
		shoppingList =
			[...lists].sort((a, b) => b.created_at.localeCompare(a.created_at))[0] ??
			null;
	}

	onMount(async () => {
		// Either half failing (or being offline) just leaves that half empty
		await Promise.allSettled([loadMeals(new Date()), loadShoppingList()]);
		loading = false;
	});
</script>

<div class="card mb-12">
	<h2 class="text-2xl font-semibold mb-4" style="color: var(--text-900);">
		Today
	</h2>

	{#if loading}
		<p style="color: var(--text-600);">Loading...</p>
	{:else}
		<div class="today-row">
			<CalendarDays size={20} aria-hidden="true" />
			<div class="flex-1">
				{#if meals.length > 0}
					<ul class="space-y-1">
						{#each meals as meal (meal.id)}
							<li>
								<span class="meal-type">{meal.meal_type}</span>
								<a href="/recipes/{meal.recipe_id}" class="today-link">
									{meal.recipe_name || `Recipe #${meal.recipe_id}`}
								</a>
							</li>
						{/each}
					</ul>
				{:else}
					<p style="color: var(--text-600);">Nothing planned for today.</p>
				{/if}
				<a href="/meal-plans" class="today-link text-sm">Open the meal plan</a>
			</div>
		</div>

		<div class="today-row">
			<ShoppingCart size={20} aria-hidden="true" />
			<div class="flex-1">
				{#if shoppingList}
					<a href="/shopping-lists/{shoppingList.id}" class="today-link">
						{shoppingList.name}
					</a>
					<span class="text-sm" style="color: var(--text-600);">
						{shoppingList.checked_count} of {shoppingList.item_count} checked
					</span>
				{:else}
					<p style="color: var(--text-600);">No active shopping list.</p>
				{/if}
				<div>
					<a href="/shopping-lists" class="today-link text-sm">
						All shopping lists
					</a>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.today-row {
		display: flex;
		gap: 0.75rem;
		align-items: flex-start;
		padding: 0.75rem 0;
		color: var(--text-700);
	}

	.today-row + .today-row {
		border-top: 1px solid var(--neutral-200);
	}

	.meal-type {
		display: inline-block;
		min-width: 5.5rem;
		font-size: 0.875rem;
		text-transform: capitalize;
		color: var(--text-600);
	}

	.today-link {
		color: var(--accent-600);
		font-weight: 500;
		border-bottom: 1px solid var(--accent-300);
	}

	.today-link:hover {
		color: var(--accent-700);
		border-bottom-color: var(--accent-600);
	}
</style>
