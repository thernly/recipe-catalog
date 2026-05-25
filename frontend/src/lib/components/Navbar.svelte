<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { getPreferences, updatePreferences } from '$lib/api/users';
	import type { User, Theme } from '$lib/types';
	import { UtensilsCrossed, Leaf, Wine, Sparkles } from '@lucide/svelte';
	import { logger } from '$lib/utils/logger';
	import { handleError } from '$lib/utils/errors';

	function isActive(path: string): boolean {
		return $page.url.pathname === path || $page.url.pathname.startsWith(path + '/');
	}

	let user: User | null = null;
	let currentTheme: Theme = 'garden-fresh';

	onMount(() => {
		const unsubscribe = auth.subscribe((state) => {
			user = state.user;
		});

		// Load current theme from user preferences
		getPreferences()
			.then((prefs) => {
				currentTheme = prefs.theme;
				document.documentElement.setAttribute('data-theme', currentTheme);
			})
			.catch((err) => {
				logger.warn('Could not load theme preferences, using default', err);
			});

		return unsubscribe;
	});

	function handleLogout() {
		auth.logout();
		goto('/');
	}

	async function toggleTheme() {
		const newTheme = currentTheme === 'garden-fresh' ? 'bistro' : 'garden-fresh';
		currentTheme = newTheme as Theme;
		document.documentElement.setAttribute('data-theme', newTheme);

		// Save theme preference to backend
		try {
			await updatePreferences({ theme: newTheme as Theme });
		} catch (err) {
			handleError(err, 'Failed to save theme preference');
		}
	}
</script>

<nav
	class="no-print sticky top-0 z-50 h-16 flex items-center justify-between px-6"
	style="background: var(--color-navbar-bg); color: var(--color-navbar-text);"
>
	<div class="flex items-center gap-6">
		<a href="/dashboard" class="logo-link">
			<UtensilsCrossed size={32} aria-hidden="true" />
			<span class="font-semibold text-xl">Recipe Catalog</span>
		</a>

		<div class="flex items-center gap-2 ml-4">
			<a href="/dashboard" class="nav-link" class:active={isActive('/dashboard')}>
				Dashboard
			</a>
			<a href="/recipes" class="nav-link" class:active={$page.url.pathname === '/recipes' || $page.url.pathname.startsWith('/recipes/')}>
				Recipes
			</a>
			<a href="/ai-generate" class="nav-link" class:active={isActive('/ai-generate')}>
				<Sparkles size={18} aria-hidden="true" />
				<span>AI Generate</span>
			</a>
			<a href="/meal-plans" class="nav-link" class:active={isActive('/meal-plans')}>
				Meal Plans
			</a>
			<a href="/export" class="nav-link" class:active={isActive('/export')}>
				Export
			</a>
			<a href="/settings" class="nav-link" class:active={isActive('/settings')}>
				Settings
			</a>
		</div>
	</div>

	<div class="flex items-center gap-3">
		<button
			on:click={toggleTheme}
			class="theme-toggle"
			aria-label={currentTheme === 'garden-fresh' ? 'Switch to Bistro theme' : 'Switch to Garden Fresh theme'}
			title={currentTheme === 'garden-fresh' ? 'Garden Fresh theme' : 'Bistro theme'}
		>
			{#if currentTheme === 'garden-fresh'}
				<Leaf size={22} aria-hidden="true" />
			{:else}
				<Wine size={22} aria-hidden="true" />
			{/if}
		</button>
		{#if user}
			<span class="text-base">{user.email}</span>
		{/if}
		<button on:click={handleLogout} class="nav-link logout-btn">
			Logout
		</button>
	</div>
</nav>

<style>
	.logo-link {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		color: inherit;
		text-decoration: none;
		transition: opacity var(--transition-fast);
	}

	.logo-link:hover {
		opacity: 0.8;
		color: inherit;
	}

	.nav-link {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		padding: var(--space-sm) var(--space-md);
		min-height: 2.75rem;
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
		text-decoration: none;
		font-weight: 500;
		color: inherit;
		border-bottom: 3px solid transparent;
		margin-bottom: -3px;
	}

	.nav-link:hover {
		background: rgba(255, 255, 255, 0.1);
	}

	.nav-link.active {
		border-bottom-color: var(--accent-400);
		background: rgba(255, 255, 255, 0.1);
		font-weight: 600;
	}

	.theme-toggle {
		min-width: 2.75rem;
		min-height: 2.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
		background: transparent;
		border: none;
		color: inherit;
		cursor: pointer;
	}

	.theme-toggle:hover {
		background: rgba(255, 255, 255, 0.1);
	}

	.logout-btn {
		background: transparent;
		border: none;
		cursor: pointer;
	}
</style>
