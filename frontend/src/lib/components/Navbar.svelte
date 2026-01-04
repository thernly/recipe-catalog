<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { getPreferences, updatePreferences } from '$lib/api/users';
	import type { User, Theme } from '$lib/types';
	import { UtensilsCrossed, Palette, Briefcase, Sparkles } from 'lucide-svelte';
	import { logger } from '$lib/utils/logger';
	import { handleError } from '$lib/utils/errors';

	let user: User | null = null;
	let currentTheme: Theme = 'classic';

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
		const newTheme = currentTheme === 'classic' ? 'professional' : 'classic';
		currentTheme = newTheme;
		document.documentElement.setAttribute('data-theme', newTheme);

		// Save theme preference to backend
		try {
			await updatePreferences({ theme: newTheme });
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
		<a href="/dashboard" class="flex items-center gap-3 hover:opacity-80 transition">
			<UtensilsCrossed size={32} aria-hidden="true" />
			<span class="font-semibold text-xl">Recipe Catalog</span>
		</a>

		<div class="flex items-center gap-4 ml-4">
			<a
				href="/dashboard"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-base font-medium"
			>
				Dashboard
			</a>
			<a
				href="/recipes"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-base font-medium"
			>
				Recipes
			</a>
			<a
				href="/ai-generate"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-base font-medium flex items-center gap-2"
			>
				<Sparkles size={18} aria-hidden="true" />
				<span>AI Generate</span>
			</a>
			<a
				href="/meal-plans"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-base font-medium"
			>
				Meal Plans
			</a>
			<a
				href="/export"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-base font-medium"
			>
				Export
			</a>
			<a
				href="/settings"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-base font-medium"
			>
				Settings
			</a>
		</div>
	</div>

	<div class="flex items-center gap-4">
		<button
			on:click={toggleTheme}
			class="px-3 py-2 rounded-md hover:bg-white/10 transition"
			aria-label={currentTheme === 'classic' ? 'Switch to professional theme' : 'Switch to classic theme'}
		>
			{#if currentTheme === 'classic'}
				<Palette size={22} aria-hidden="true" />
			{:else}
				<Briefcase size={22} aria-hidden="true" />
			{/if}
		</button>
		{#if user}
			<span class="text-base">{user.email}</span>
		{/if}
		<button
			on:click={handleLogout}
			class="px-4 py-2 rounded-md hover:bg-white/10 transition text-base font-medium"
		>
			Logout
		</button>
	</div>
</nav>
