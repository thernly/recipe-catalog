<script lang="ts">
	import { auth } from '#lib/stores/auth.js';
	import { theme } from '#lib/stores/theme.js';
	import { afterNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { getPreferences, updatePreferences } from '#lib/api/users.js';
	import type { User, Theme } from '#lib/types/index.js';
	import {
		UtensilsCrossed,
		Leaf,
		Wine,
		Moon,
		Contrast,
		Monitor,
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

	// The button steps through every theme Settings offers, so pressing it never
	// lands on a different theme than the one it names. The store applies the
	// theme (including "system", which is not a theme of its own).
	const THEMES = [
		{ id: 'garden-fresh', name: 'Garden Fresh', icon: Leaf },
		{ id: 'bistro', name: 'Bistro', icon: Wine },
		{ id: 'dark', name: 'Dark', icon: Moon },
		{ id: 'high-contrast', name: 'High Contrast', icon: Contrast },
		{ id: 'system', name: 'System', icon: Monitor },
	];
	$: themeIndex = Math.max(
		0,
		THEMES.findIndex((option) => option.id === $theme),
	);
	$: currentTheme = THEMES[themeIndex];
	$: nextTheme = THEMES[(themeIndex + 1) % THEMES.length];

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
			.then((prefs) => theme.set(prefs.theme))
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
		const newTheme = nextTheme.id as Theme;
		theme.set(newTheme);

		// Save theme preference to backend
		try {
			await updatePreferences({ theme: newTheme });
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
				href="/import"
				class="nav-link"
				class:active={isActive('/import')}
				aria-current={current('/import')}
			>
				Import
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
			aria-label="Switch to {nextTheme.name} theme"
			title="{currentTheme.name} theme"
		>
			<svelte:component this={currentTheme.icon} size={22} aria-hidden="true" />
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

	/* Measured in the browser before the Import link was added: logo and links
	   took about 1030px and the theme and Logout buttons about 140px, so one row
	   needed roughly 1220px without the email and 1450px with it. Both
	   breakpoints were then raised by 100px for Import (not re-measured). */
	@media (max-width: 1600px) {
		.user-email {
			display: none;
		}
	}

	@media (max-width: 1380px) {
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
