<script lang="ts">
	import { updateCooking, type RecipeCooking } from '#lib/api/recipes.js';
	import { toast } from '#lib/stores/toast.js';

	/** The household's rating (1-5) and the day the recipe was last cooked */
	export let recipeId: number;
	export let rating: number | null = null;
	export let lastCookedOn: string | null = null;

	// The cook's own calendar day as YYYY-MM-DD (the en-CA date format)
	const today = () => new Date().toLocaleDateString('en-CA');

	async function save(changes: Partial<RecipeCooking>) {
		try {
			({ rating, last_cooked_on: lastCookedOn } = await updateCooking(
				recipeId,
				changes,
			));
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to save');
		}
	}

	// Local midnight, so the day shown is the day that was saved
	$: cookedLabel = lastCookedOn
		? new Date(`${lastCookedOn}T00:00`).toLocaleDateString(undefined, {
				day: 'numeric',
				month: 'short',
				year: 'numeric',
			})
		: null;
</script>

<div class="cooking no-print">
	<div class="stars" role="group" aria-label="Household rating">
		{#each [1, 2, 3, 4, 5] as star (star)}
			<!-- Tapping the current rating again clears it -->
			<button
				type="button"
				aria-label="Rate {star} out of 5"
				aria-pressed={rating === star}
				on:click={() => save({ rating: rating === star ? null : star })}
			>
				{star <= (rating ?? 0) ? '★' : '☆'}
			</button>
		{/each}
	</div>
	<span>{cookedLabel ? `Last cooked ${cookedLabel}` : 'Not cooked yet'}</span>
	{#if lastCookedOn !== today()}
		<button
			type="button"
			class="link"
			on:click={() => save({ last_cooked_on: today() })}
		>
			Cooked today
		</button>
	{/if}
	{#if lastCookedOn}
		<button
			type="button"
			class="link"
			on:click={() => save({ last_cooked_on: null })}
		>
			Clear
		</button>
	{/if}
</div>

<style>
	.cooking {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem;
		margin-top: 0.5rem;
		font-size: 0.875rem;
		color: var(--text-600);
	}

	.stars button {
		padding: 0 0.125rem;
		font-size: 1.5rem;
		line-height: 1;
		color: var(--accent-500);
	}

	.link {
		text-decoration: underline;
		color: var(--primary-600);
	}
</style>
