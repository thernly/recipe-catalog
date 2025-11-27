<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		getCurrentUser,
		getPreferences,
		getUserStats,
		deleteAccount,
		type User,
		type UserPreferences,
		type UserStats
	} from '$lib/api/users';
	import { auth } from '$lib/stores/auth';
	import ProfileSection from '$lib/components/settings/ProfileSection.svelte';
	import PreferencesSection from '$lib/components/settings/PreferencesSection.svelte';
	import SecuritySection from '$lib/components/settings/SecuritySection.svelte';
	import HouseholdSection from '$lib/components/settings/HouseholdSection.svelte';
	import StatsSection from '$lib/components/settings/StatsSection.svelte';
	import FiltersSection from '$lib/components/settings/FiltersSection.svelte';
	import DangerZoneSection from '$lib/components/settings/DangerZoneSection.svelte';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';
	import { User as UserIcon, Palette, Lock, Home, BarChart3, Search, AlertTriangle } from 'lucide-svelte';

	let user: User | null = null;
	let preferences: UserPreferences | null = null;
	let stats: UserStats | null = null;
	let loading = true;
	let error: string | null = null;

	// Active section
	let activeSection: 'profile' | 'preferences' | 'security' | 'household' | 'stats' | 'filters' | 'danger' = 'profile';

	// Helper function to apply theme
	function applyTheme(themeId: string) {
		let actualTheme = themeId;

		// If system theme is selected, detect the actual theme
		if (themeId === 'system') {
			const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
			actualTheme = prefersDark ? 'dark' : 'light';
		}

		// Apply theme to document
		document.documentElement.setAttribute('data-theme', actualTheme);
	}

	// Load user data
	async function loadUserData() {
		loading = true;
		error = null;

		try {
			const [userData, prefsData, statsData] = await Promise.all([
				getCurrentUser(),
				getPreferences(),
				getUserStats()
			]);

			user = userData;
			preferences = prefsData;
			stats = statsData;

			// Apply current theme
			applyTheme(prefsData.theme);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load user data';
			console.error('Failed to load user data:', err);
		} finally {
			loading = false;
		}
	}

	// Handle profile update
	function handleProfileUpdate(e: CustomEvent) {
		user = e.detail;
	}

	// Handle preferences update
	function handlePreferencesUpdate(e: CustomEvent) {
		preferences = e.detail;
	}

	// Delete account
	async function handleDeleteAccount() {
		try {
			await deleteAccount();
			auth.logout();
			goto('/auth/login');
		} catch (err) {
			toast.error('Failed to delete account: ' + (err instanceof Error ? err.message : 'Unknown error'));
			console.error('Failed to delete account:', err);
		}
	}

	onMount(() => {
		loadUserData();
	});
</script>

<svelte:head>
	<title>Settings - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	<div class="container-custom py-8">
		<h1 class="text-4xl font-bold mb-8" style="color: var(--text-900);">Settings</h1>

		{#if loading}
			<!-- Loading state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⏳</div>
				<p class="text-lg" style="color: var(--text-600);">Loading settings...</p>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⚠️</div>
				<p class="text-lg mb-2" style="color: var(--text-900);">Failed to load settings</p>
				<p class="text-sm mb-4" style="color: var(--text-600);">{error}</p>
				<button on:click={loadUserData} class="btn btn-primary">Try Again</button>
			</div>
		{:else if user && preferences && stats}
			<!-- Settings layout -->
			<div class="settings-layout">
				<!-- Sidebar navigation -->
				<aside class="settings-sidebar">
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'profile'}
						on:click={() => (activeSection = 'profile')}
					>
						<UserIcon size={18} aria-hidden="true" />
						<span>Profile</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'preferences'}
						on:click={() => (activeSection = 'preferences')}
					>
						<Palette size={18} aria-hidden="true" />
						<span>Preferences</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'security'}
						on:click={() => (activeSection = 'security')}
					>
						<Lock size={18} aria-hidden="true" />
						<span>Security</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'household'}
						on:click={() => (activeSection = 'household')}
					>
						<Home size={18} aria-hidden="true" />
						<span>Household</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'stats'}
						on:click={() => (activeSection = 'stats')}
					>
						<BarChart3 size={18} aria-hidden="true" />
						<span>Statistics</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'filters'}
						on:click={() => (activeSection = 'filters')}
					>
						<Search size={18} aria-hidden="true" />
						<span>Filters</span>
					</button>
					<button
						class="sidebar-link danger flex items-center gap-2"
						class:active={activeSection === 'danger'}
						on:click={() => (activeSection = 'danger')}
					>
						<AlertTriangle size={18} aria-hidden="true" />
						<span>Danger Zone</span>
					</button>
				</aside>

				<!-- Main content -->
				<div class="settings-content">
					{#if activeSection === 'profile'}
						<ProfileSection {user} on:update={handleProfileUpdate} />
					{:else if activeSection === 'preferences'}
						<PreferencesSection {preferences} on:update={handlePreferencesUpdate} />
					{:else if activeSection === 'security'}
						<SecuritySection />
					{:else if activeSection === 'household'}
						<HouseholdSection />
					{:else if activeSection === 'stats'}
						<StatsSection {stats} {user} />
					{:else if activeSection === 'filters'}
						<FiltersSection />
					{:else if activeSection === 'danger'}
						<DangerZoneSection on:delete={handleDeleteAccount} />
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.settings-layout {
		display: grid;
		grid-template-columns: 250px 1fr;
		gap: 2rem;
		align-items: start;
	}

	.settings-sidebar {
		position: sticky;
		top: 2rem;
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.sidebar-link {
		padding: 0.75rem 1rem;
		text-align: left;
		background: transparent;
		border: none;
		border-radius: var(--radius-md);
		color: var(--text-700);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.sidebar-link:hover {
		background: var(--neutral-100);
		color: var(--text-900);
	}

	.sidebar-link.active {
		background: var(--accent-50);
		color: var(--accent-700);
		font-weight: 600;
	}

	.sidebar-link.danger {
		color: var(--error-600);
	}

	.sidebar-link.danger:hover {
		background: var(--error-50);
		color: var(--error-700);
	}

	.settings-content {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 2rem;
	}

	@media (max-width: 1024px) {
		.settings-layout {
			grid-template-columns: 1fr;
		}

		.settings-sidebar {
			position: static;
			flex-direction: row;
			overflow-x: auto;
		}
	}
</style>
