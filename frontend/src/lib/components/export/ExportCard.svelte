<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let icon: string;
	export let title: string;
	export let description: string;
	export let formats: Array<{ name: string; emoji: string; desc: string; value: string }> = [];
	export let featured = false;
	export let exporting = false;

	const dispatch = createEventDispatcher();

	function handleExport(format: string) {
		dispatch('export', format);
	}
</script>

<div class="export-card" class:featured>
	<div class="card-header">
		<div class="card-icon">{icon}</div>
		<div>
			<h2 class="card-title">{title}</h2>
			<p class="card-description">{description}</p>
		</div>
	</div>

	<div class="card-content">
		<slot>
			{#if formats.length > 0}
				<div class="format-section">
					<h3 class="format-title">Available Formats:</h3>

					{#each formats as format}
						<button
							on:click={() => handleExport(format.value)}
							disabled={exporting}
							class="format-button"
						>
							<div class="format-info">
								<span class="format-name">{format.emoji} {format.name}</span>
								<span class="format-desc">{format.desc}</span>
							</div>
							<span class="download-icon">⬇️</span>
						</button>
					{/each}
				</div>
			{/if}
		</slot>
	</div>
</div>

<style>
	.export-card {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
		transition: all var(--transition-fast);
	}

	.export-card.featured {
		border-color: var(--accent-300);
		box-shadow: 0 0 0 2px var(--accent-100);
	}

	.export-card:hover {
		box-shadow: var(--shadow-md);
	}

	.card-header {
		display: flex;
		gap: 1rem;
		margin-bottom: 1.5rem;
		align-items: start;
	}

	.card-icon {
		font-size: 2rem;
	}

	.card-title {
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0 0 0.25rem 0;
	}

	.card-description {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0;
	}

	.card-content {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.format-section {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.format-title {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-700);
		margin: 0 0 0.5rem 0;
	}

	.format-button {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
		text-align: left;
	}

	.format-button:hover:not(:disabled) {
		background: var(--accent-50);
		border-color: var(--accent-300);
		transform: translateY(-1px);
		box-shadow: var(--shadow-sm);
	}

	.format-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.format-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.format-name {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-900);
	}

	.format-desc {
		font-size: 0.75rem;
		color: var(--text-600);
	}

	.download-icon {
		font-size: 1.25rem;
	}
</style>
