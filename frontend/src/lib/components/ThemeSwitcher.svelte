<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let currentTheme: 'classic' | 'professional' = 'classic';

	const dispatch = createEventDispatcher();

	const themes = [
		{
			id: 'classic' as const,
			name: 'Classic Minimal',
			description: 'Clean and simple with warm saffron accents',
			primary: '#3D4451',
			accent: '#F59E0B',
			preview: 'Charcoal & Saffron'
		},
		{
			id: 'professional' as const,
			name: 'Professional Warm',
			description: 'Bold navy with vibrant apricot highlights',
			primary: '#1E3A5F',
			accent: '#F97316',
			preview: 'Navy & Apricot'
		}
	];

	function selectTheme(themeId: 'classic' | 'professional') {
		currentTheme = themeId;
		// Apply theme immediately
		document.documentElement.setAttribute('data-theme', themeId);
		// Notify parent component
		dispatch('change', themeId);
	}
</script>

<div class="theme-switcher">
	<h3 class="switcher-title">Choose Your Theme</h3>
	<p class="switcher-description">Select a color scheme for your recipe catalog</p>

	<div class="theme-options">
		{#each themes as theme}
			<button
				class="theme-card"
				class:active={currentTheme === theme.id}
				on:click={() => selectTheme(theme.id)}
			>
				<!-- Theme Preview -->
				<div class="theme-preview">
					<div class="preview-colors">
						<div class="color-block" style="background-color: {theme.primary};" />
						<div class="color-block" style="background-color: {theme.accent};" />
					</div>
					{#if currentTheme === theme.id}
						<div class="active-badge">✓ Active</div>
					{/if}
				</div>

				<!-- Theme Info -->
				<div class="theme-info">
					<h4 class="theme-name">{theme.name}</h4>
					<p class="theme-description">{theme.description}</p>
					<p class="theme-colors">{theme.preview}</p>
				</div>
			</button>
		{/each}
	</div>
</div>

<style>
	.theme-switcher {
		width: 100%;
	}

	.switcher-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.5rem 0;
	}

	.switcher-description {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 1.5rem 0;
	}

	.theme-options {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
	}

	.theme-card {
		display: flex;
		flex-direction: column;
		background: var(--neutral-white);
		border: 2px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		overflow: hidden;
		cursor: pointer;
		transition: all var(--transition-fast);
		text-align: left;
		padding: 0;
	}

	.theme-card:hover {
		border-color: var(--accent-400);
		box-shadow: var(--shadow-md);
		transform: translateY(-2px);
	}

	.theme-card.active {
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.theme-preview {
		position: relative;
		height: 120px;
		background: linear-gradient(135deg, var(--neutral-100) 0%, var(--neutral-200) 100%);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.preview-colors {
		display: flex;
		gap: 0.5rem;
	}

	.color-block {
		width: 60px;
		height: 60px;
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
	}

	.active-badge {
		position: absolute;
		top: 0.75rem;
		right: 0.75rem;
		padding: 0.25rem 0.75rem;
		background: var(--accent-500);
		color: var(--neutral-white);
		font-size: 0.75rem;
		font-weight: 600;
		border-radius: var(--radius-full);
		box-shadow: var(--shadow-sm);
	}

	.theme-info {
		padding: 1rem;
	}

	.theme-name {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.5rem 0;
	}

	.theme-description {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 0.5rem 0;
		line-height: 1.4;
	}

	.theme-colors {
		font-size: 0.75rem;
		color: var(--text-500);
		font-weight: 500;
		margin: 0;
	}
</style>
