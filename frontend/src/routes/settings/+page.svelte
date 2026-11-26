<script lang="ts">
	import { theme } from '#lib/stores/theme.js';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		getCurrentUser,
		getPreferences,
		getUserStats,
		deleteAccount,
		type User,
		type UserPreferences,
		type UserStats,
	} from '#lib/api/users.js';
	import { auth } from '#lib/stores/auth.js';
	import ProfileSection from '#lib/components/settings/ProfileSection.svelte';
	import PreferencesSection from '#lib/components/settings/PreferencesSection.svelte';
	import SecuritySection from '#lib/components/settings/SecuritySection.svelte';
	import ApiTokensSection from '#lib/components/settings/ApiTokensSection.svelte';
	import HouseholdSection from '#lib/components/settings/HouseholdSection.svelte';
	import StatsSection from '#lib/components/settings/StatsSection.svelte';
	import FiltersSection from '#lib/components/settings/FiltersSection.svelte';
	import DangerZoneSection from '#lib/components/settings/DangerZoneSection.svelte';
	import { toast } from '#lib/stores/toast.js';
	import {
		User as UserIcon,
		Palette,
		Lock,
		KeyRound,
		Home,
		BarChart3,
		Search,
		AlertTriangle,
	} from '@lucide/svelte';

	let user: User | null = null;
	let preferences: UserPreferences | null = null;
	let stats: UserStats | null = null;
	let loading = true;
	let error: string | null = null;

	// The open section is kept in the page address (/settings#household), so a
	// refresh stays put, Back returns to the previous section, and other pages
	// can link straight to one.
	const SECTIONS = [
		'profile',
		'preferences',
		'security',
		'api-tokens',
		'household',
		'stats',
		'filters',
		'danger',
	] as const;
	type Section = (typeof SECTIONS)[number];
	let activeSection: Section = 'profile';

	function sectionFromAddress(): Section {
		const named = location.hash.slice(1) as Section;
		return SECTIONS.includes(named) ? named : 'profile';
	}

	function select(section: Section) {
		activeSection = section;
		location.hash = section;
	}

	// Load user data
	async function loadUserData() {
		loading = true;
		error = null;

		try {
			const [userData, prefsData, statsData] = await Promise.all([
				getCurrentUser(),
				getPreferences(),
				getUserStats(),
			]);

			user = userData;
			preferences = prefsData;
			stats = statsData;

			// Apply current theme
			theme.set(prefsData.theme);
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
			toast.error(
				'Failed to delete account: ' +
					(err instanceof Error ? err.message : 'Unknown error'),
			);
			console.error('Failed to delete account:', err);
		}
	}

	onMount(() => {
		activeSection = sectionFromAddress();
		loadUserData();
	});
</script>

<svelte:window on:hashchange={() => (activeSection = sectionFromAddress())} />

<svelte:head>
	<title>Settings - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	<div class="container-custom py-8">
		<h1 class="text-4xl font-bold mb-8" style="color: var(--text-900);">
			Settings
		</h1>

		{#if loading}
			<!-- Loading state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⏳</div>
				<p class="text-lg" style="color: var(--text-600);">
					Loading settings...
				</p>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⚠️</div>
				<p class="text-lg mb-2" style="color: var(--text-900);">
					Failed to load settings
				</p>
				<p class="text-sm mb-4" style="color: var(--text-600);">{error}</p>
				<button on:click={loadUserData} class="btn btn-primary">
					Try Again
				</button>
			</div>
		{:else if user && preferences && stats}
			<!-- Settings layout -->
			<div class="settings-layout">
				<!-- Sidebar navigation -->
				<nav class="settings-sidebar" aria-label="Settings sections">
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'profile'}
						aria-current={activeSection === 'profile' || undefined}
						on:click={() => select('profile')}
					>
						<UserIcon size={18} aria-hidden="true" />
						<span>Profile</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'preferences'}
						aria-current={activeSection === 'preferences' || undefined}
						on:click={() => select('preferences')}
					>
						<Palette size={18} aria-hidden="true" />
						<span>Preferences</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'security'}
						aria-current={activeSection === 'security' || undefined}
						on:click={() => select('security')}
					>
						<Lock size={18} aria-hidden="true" />
						<span>Security</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'api-tokens'}
						aria-current={activeSection === 'api-tokens' || undefined}
						on:click={() => select('api-tokens')}
					>
						<KeyRound size={18} aria-hidden="true" />
						<span>API Tokens</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'household'}
						aria-current={activeSection === 'household' || undefined}
						on:click={() => select('household')}
					>
						<Home size={18} aria-hidden="true" />
						<span>Household</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'stats'}
						aria-current={activeSection === 'stats' || undefined}
						on:click={() => select('stats')}
					>
						<BarChart3 size={18} aria-hidden="true" />
						<span>Statistics</span>
					</button>
					<button
						class="sidebar-link flex items-center gap-2"
						class:active={activeSection === 'filters'}
						aria-current={activeSection === 'filters' || undefined}
						on:click={() => select('filters')}
					>
						<Search size={18} aria-hidden="true" />
						<span>Filters</span>
					</button>
					<button
						class="sidebar-link danger flex items-center gap-2"
						class:active={activeSection === 'danger'}
						aria-current={activeSection === 'danger' || undefined}
						on:click={() => select('danger')}
					>
						<AlertTriangle size={18} aria-hidden="true" />
						<span>Danger Zone</span>
					</button>
					<p class="app-version">Version {__APP_VERSION__}</p>
				</nav>

				<!-- Main content -->
				<div class="settings-content">
					{#if activeSection === 'profile'}
						<ProfileSection {user} on:update={handleProfileUpdate} />
					{:else if activeSection === 'preferences'}
						<PreferencesSection
							{preferences}
							on:update={handlePreferencesUpdate}
						/>
					{:else if activeSection === 'security'}
						<SecuritySection />
					{:else if activeSection === 'api-tokens'}
						<ApiTokensSection />
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
		color: var(--color-error-text);
	}

	.sidebar-link.danger:hover {
		background: var(--error-50);
		color: var(--error-700);
	}

	.app-version {
		margin-top: 0.5rem;
		padding: 0.5rem 1rem 0;
		border-top: 1px solid var(--neutral-200);
		font-size: 0.75rem;
		color: var(--text-500);
		white-space: nowrap;
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
