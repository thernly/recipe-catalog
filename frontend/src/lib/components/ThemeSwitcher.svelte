<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';

	export let currentTheme: string = 'light';

	const dispatch = createEventDispatcher();

	const themes = [
		{
			id: 'garden-fresh' as const,
			name: 'Garden Fresh',
			description: 'Fresh herb greens with warm terracotta accents, inspired by farmers markets',
			primary: '#1B4332',
			accent: '#D35400',
			preview: 'Herb Green & Terracotta'
		},
		{
			id: 'bistro' as const,
			name: 'Bistro',
			description: 'Sophisticated burgundy with champagne gold, inspired by upscale dining',
			primary: '#722F37',
			accent: '#C9B037',
			preview: 'Burgundy & Gold'
		},
		{
			id: 'dark' as const,
			name: 'Dark',
			description: 'Easy on the eyes with dark backgrounds',
			primary: '#1f2937',
			accent: '#60a5fa',
			preview: 'Dark Blue'
		},
		{
			id: 'high-contrast' as const,
			name: 'High Contrast',
			description: 'Maximum readability with high contrast',
			primary: '#000000',
			accent: '#0052cc',
			preview: 'Black & Blue'
		},
		{
			id: 'system' as const,
			name: 'System',
			description: 'Follow your device theme preference',
			primary: '#6b7280',
			accent: '#6b7280',
			preview: 'Auto'
		}
	];

	function getSystemTheme(): 'garden-fresh' | 'dark' {
		if (typeof window !== 'undefined' && window.matchMedia) {
			return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'garden-fresh';
		}
		return 'garden-fresh';
	}

	function applyTheme(themeId: string) {
		let actualTheme = themeId;

		// If system theme is selected, detect the actual theme
		if (themeId === 'system') {
			actualTheme = getSystemTheme();
		}

		// Apply theme to document
		document.documentElement.setAttribute('data-theme', actualTheme);
	}

	function selectTheme(themeId: string) {
		currentTheme = themeId;
		applyTheme(themeId);
		dispatch('change', themeId);
	}

	// Listen for system theme changes when 'system' is selected
	onMount(() => {
		if (typeof window !== 'undefined' && window.matchMedia) {
			const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

			const handleThemeChange = () => {
				if (currentTheme === 'system') {
					applyTheme('system');
				}
			};

			// Modern browsers
			if (mediaQuery.addEventListener) {
				mediaQuery.addEventListener('change', handleThemeChange);
				return () => mediaQuery.removeEventListener('change', handleThemeChange);
			}
		}
	});
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
				<div class="theme-preview" class:system={theme.id === 'system'}>
					{#if theme.id === 'system'}
						<div class="system-icon">⚙️</div>
					{:else}
						<div class="preview-colors">
							<div class="color-block" style="background-color: {theme.primary};"></div>
							<div class="color-block" style="background-color: {theme.accent};"></div>
						</div>
					{/if}
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

	.system-icon {
		font-size: 3rem;
	}

	.theme-preview.system {
		background: linear-gradient(
			135deg,
			var(--neutral-100) 0%,
			var(--neutral-200) 50%,
			var(--neutral-300) 100%
		);
	}
</style>
