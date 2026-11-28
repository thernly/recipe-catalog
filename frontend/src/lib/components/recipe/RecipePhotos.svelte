<script lang="ts">
	import type { RecipeData } from '#lib/types/index.js';

	/** The recipe's stored pictures, the address of its main picture, and its name for alt text */
	export let images: RecipeData['images'] = [];
	export let imageUrl: string | null | undefined = null;
	export let name: string;

	let index = 0;
	let touchX: number | null = null;

	// Stored picture data first; an entry without data shows its address instead.
	$: sources = (images ?? [])
		.map((img) =>
			img.data?.trim()
				? `data:${img.mimeType};base64,${img.data}`
				: img.url?.trim() || '',
		)
		.filter(Boolean);
	$: photos = sources.length ? sources : imageUrl ? [imageUrl] : [];
	// Another recipe (same page, new photos) starts again at its first photo
	$: startOver(photos);

	function startOver(_photos: string[]) {
		index = 0;
	}

	function go(step: number) {
		index = (index + step + photos.length) % photos.length;
	}

	function touchEnd(event: TouchEvent) {
		if (touchX === null) return;
		const moved = event.changedTouches[0].clientX - touchX;
		touchX = null;
		if (Math.abs(moved) > 40) go(moved < 0 ? 1 : -1);
	}
</script>

{#if photos.length}
	<div
		class="recipe-hero-image mb-6"
		role="group"
		aria-label="Photos of {name}"
		on:touchstart={(e) => (touchX = e.touches[0].clientX)}
		on:touchend={touchEnd}
	>
		<img
			src={photos[index]}
			alt={photos.length > 1
				? `${name}, photo ${index + 1} of ${photos.length}`
				: name}
		/>
		{#if photos.length > 1}
			<button
				type="button"
				class="nav prev no-print"
				aria-label="Previous photo"
				on:click={() => go(-1)}
			>
				‹
			</button>
			<button
				type="button"
				class="nav next no-print"
				aria-label="Next photo"
				on:click={() => go(1)}
			>
				›
			</button>
			<span class="count no-print" aria-live="polite">
				{index + 1} of {photos.length}
			</span>
		{/if}
	</div>
{/if}

<style>
	.recipe-hero-image {
		width: 100%;
		height: 50vh;
		max-height: 500px;
		min-height: 300px;
		overflow: hidden;
		background: var(--neutral-100);
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-xl);
		margin: 0 auto;
		box-shadow: var(--shadow-lg);
		position: relative;
	}

	.recipe-hero-image::after {
		content: '';
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 60%;
		background: linear-gradient(
			to top,
			rgba(0, 0, 0, 0.5) 0%,
			rgba(0, 0, 0, 0.2) 40%,
			transparent 100%
		);
		pointer-events: none;
		border-radius: 0 0 var(--radius-xl) var(--radius-xl);
	}

	.recipe-hero-image img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		transition: transform var(--transition-slow);
	}

	.recipe-hero-image:hover img {
		transform: scale(1.02);
	}

	/* Over a photo, so fixed dark-on-light colours rather than theme tokens */
	.nav {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		z-index: 1;
		width: 44px;
		height: 44px;
		border-radius: 9999px;
		background: rgba(0, 0, 0, 0.55);
		color: #fff;
		font-size: 1.75rem;
		line-height: 1;
	}

	.nav:hover,
	.nav:focus-visible {
		background: rgba(0, 0, 0, 0.75);
	}

	.prev {
		left: 0.75rem;
	}

	.next {
		right: 0.75rem;
	}

	.count {
		position: absolute;
		bottom: 0.75rem;
		right: 0.75rem;
		z-index: 1;
		padding: 0.125rem 0.625rem;
		border-radius: 9999px;
		background: rgba(0, 0, 0, 0.55);
		color: #fff;
		font-size: 0.875rem;
		font-variant-numeric: tabular-nums;
	}
</style>
