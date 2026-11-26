<script lang="ts">
	import { auth } from '#lib/stores/auth.js';
	import { afterNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { getPreferences, updatePreferences } from '#lib/api/users.js';
	import type { User, Theme } from '#lib/types/index.js';
	import {
		UtensilsCrossed,
		Leaf,
		Wine,
		Sparkles,
		Menu,
		X,
	} from '@lucide/svelte';
	import { logger } from '#lib/utils/logger.js';
	import { handleError } from '#lib/utils/errors.js';

	function isActive(path: string): boolean {
		return (
			page.url.pathname === path || page.url.pathname.startsWith(path + '/')
		);
	}

	/** aria-current for a nav link: "page" on the exact page, "location" inside its section. */
	function current(path: string): 'page' | 'location' | undefined {
		if (page.url.pathname === path) return 'page';
		return isActive(path) ? 'location' : undefined;
	}

	let user: User | null = null;
	let currentTheme: Theme = 'garden-fresh';

	// Narrow screens: the links live in a menu, closed again after each navigation
	let menuOpen = false;
	afterNavigate(() => {
		menuOpen = false;
	});

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
		const newTheme =
			currentTheme === 'garden-fresh' ? 'bistro' : 'garden-fresh';
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

<svelte:window on:keydown={(e) => e.key === 'Escape' && (menuOpen = false)} />

<nav
	class="navbar no-print sticky top-0 z-50 h-16 flex items-center justify-between"
	style="background: var(--color-navbar-bg); color: var(--color-navbar-text);"
>
	<div class="flex items-center gap-6">
		<!-- Shown only on narrow screens, where the links collapse into a menu -->
		<button
			type="button"
			class="menu-toggle"
			aria-label="Menu"
			aria-expanded={menuOpen}
			aria-controls="main-menu"
			on:click={() => (menuOpen = !menuOpen)}
		>
			{#if menuOpen}
				<X size={24} aria-hidden="true" />
			{:else}
				<Menu size={24} aria-hidden="true" />
			{/if}
		</button>

		<a href="/dashboard" class="logo-link">
			<UtensilsCrossed size={32} aria-hidden="true" />
			<span class="logo-text font-semibold text-xl">Recipe Catalog</span>
		</a>

		<div id="main-menu" class="nav-links" class:open={menuOpen}>
			<a
				href="/dashboard"
				class="nav-link"
				class:active={isActive('/dashboard')}
				aria-current={current('/dashboard')}
			>
				Dashboard
			</a>

			<a
				href="/recipes"
				class="nav-link"
				class:active={isActive('/recipes')}
				aria-current={current('/recipes')}
			>
				Recipes
			</a>

			<a
				href="/ai-generate"
				class="nav-link"
				class:active={isActive('/ai-generate')}
				aria-current={current('/ai-generate')}
			>
				<Sparkles size={18} aria-hidden="true" />
				<span>AI Generate</span>
			</a>
			<a
				href="/meal-plans"
				class="nav-link"
				class:active={isActive('/meal-plans')}
				aria-current={current('/meal-plans')}
			>
				Meal Plans
			</a>
			<a
				href="/shopping-lists"
				class="nav-link"
				class:active={isActive('/shopping-lists')}
				aria-current={current('/shopping-lists')}
			>
				Shopping Lists
			</a>
			<a
				href="/export"
				class="nav-link"
				class:active={isActive('/export')}
				aria-current={current('/export')}
			>
				Export
			</a>
			<a
				href="/settings"
				class="nav-link"
				class:active={isActive('/settings')}
				aria-current={current('/settings')}
			>
				Settings
			</a>
		</div>
	</div>

	<div class="flex items-center gap-3">
		<button
			on:click={toggleTheme}
			class="theme-toggle"
			aria-label={currentTheme === 'garden-fresh'
				? 'Switch to Bistro theme'
				: 'Switch to Garden Fresh theme'}
			title={currentTheme === 'garden-fresh'
				? 'Garden Fresh theme'
				: 'Bistro theme'}
		>
			{#if currentTheme === 'garden-fresh'}
				<Leaf size={22} aria-hidden="true" />
			{:else}
				<Wine size={22} aria-hidden="true" />
			{/if}
		</button>
		{#if user}
			<span class="user-email text-base">{user.email}</span>
		{/if}
		<button on:click={handleLogout} class="nav-link logout-btn">
			Logout
		</button>
	</div>
</nav>

<style>
	.navbar {
		padding: 0 1.5rem;
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-left: 1rem;
	}

	.menu-toggle {
		display: none;
		min-width: 2.75rem;
		min-height: 2.75rem;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-md);
		background: transparent;
		border: none;
		color: inherit;
		cursor: pointer;
	}

	.menu-toggle:hover {
		background: rgba(255, 255, 255, 0.1);
	}

	.user-email {
		max-width: 14rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/* Measured in the browser: logo and links take about 1030px and the theme and
	   Logout buttons about 140px, so one row needs roughly 1220px without the
	   email and 1450px with it. */
	@media (max-width: 1500px) {
		.user-email {
			display: none;
		}
	}

	@media (max-width: 1280px) {
		.navbar {
			padding: 0 0.75rem;
		}

		.menu-toggle {
			display: flex;
		}

		.nav-links {
			display: none;
			position: absolute;
			top: 100%;
			left: 0;
			right: 0;
			margin-left: 0;
			padding: 0.5rem 0.75rem 1rem;
			flex-direction: column;
			align-items: stretch;
			background: var(--color-navbar-bg);
			box-shadow: var(--shadow-md);
			max-height: calc(100vh - 4rem);
			overflow-y: auto;
		}

		.nav-links.open {
			display: flex;
		}
	}

	@media (max-width: 480px) {
		.logo-text {
			display: none;
		}
	}

	.logo-link {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		white-space: nowrap;
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
		white-space: nowrap;
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
