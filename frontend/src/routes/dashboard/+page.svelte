<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import type { User } from '$lib/types';
	import { getUserStats, type UserStats } from '$lib/api/users';
	import { BookOpen, Star, Folder, Plus, Search, Download, Upload, Rocket, Check, Hand } from 'lucide-svelte';

	let user: User | null = null;
	let stats: UserStats | null = null;
	let loadingStats = true;

	async function loadStats() {
		loadingStats = true;
		try {
			stats = await getUserStats();
		} catch (err) {
			console.error('Failed to load stats:', err);
			// Set default stats if loading fails
			stats = {
				total_recipes: 0,
				total_collections: 0,
				recipes_imported: 0,
				recipes_manual: 0,
				recipes_this_month: 0
			};
		} finally {
			loadingStats = false;
		}
	}

	onMount(() => {
		const unsubscribe = auth.subscribe((state) => {
			if (!state.user) {
				goto('/auth/login');
			} else {
				user = state.user;
				// Load stats when user is available
				loadStats();
			}
		});

		// Initialize auth
		auth.init();

		return unsubscribe;
	});

	function handleLogout() {
		auth.logout();
		goto('/');
	}
</script>

<svelte:head>
	<title>Dashboard - Recipe Catalog</title>
</svelte:head>

{#if user}
	<div class="min-h-screen bg-neutral-50">
		<!-- Main Content -->
		<main class="container-custom py-12">
			<div class="max-w-4xl mx-auto">
				<!-- Welcome Header -->
				<div class="mb-12">
					<h1 class="text-4xl font-bold mb-2 flex items-center gap-3" style="color: var(--text-900);">
						<span>Welcome{user.display_name ? `, ${user.display_name}` : ''}!</span>
						<Hand size={36} class="inline-block" aria-hidden="true" />
					</h1>
					<p class="text-lg" style="color: var(--text-600);">
						Your personal recipe collection dashboard
					</p>
				</div>

				<!-- Stats Cards -->
				<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
					<button on:click={() => goto('/recipes')} class="stat-card">
						<div class="stat-icon" style="color: var(--accent-500);">
							<BookOpen size={48} aria-hidden="true" />
						</div>
						<h3 class="stat-number">
							{loadingStats ? '...' : stats?.total_recipes ?? 0}
						</h3>
						<p class="stat-label">Total Recipes</p>
					</button>

					<button on:click={() => goto('/recipes')} class="stat-card">
						<div class="stat-icon" style="color: var(--accent-500);">
							<Star size={48} aria-hidden="true" />
						</div>
						<h3 class="stat-number">
							{loadingStats ? '...' : 0}
						</h3>
						<p class="stat-label">Favorites</p>
					</button>

					<button on:click={() => goto('/recipes')} class="stat-card">
						<div class="stat-icon" style="color: var(--accent-500);">
							<Folder size={48} aria-hidden="true" />
						</div>
						<h3 class="stat-number">
							{loadingStats ? '...' : stats?.total_collections ?? 0}
						</h3>
						<p class="stat-label">Collections</p>
					</button>
				</div>

				<!-- Quick Actions -->
				<div class="card">
					<h2 class="text-2xl font-semibold mb-6" style="color: var(--text-900);">Quick Actions</h2>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<button on:click={() => goto('/recipes/new')} class="quick-action-btn btn-primary">
							<div class="action-icon">
								<Plus size={28} aria-hidden="true" />
							</div>
							<h3 class="action-title">Add Recipe</h3>
							<p class="action-description">Manually add a new recipe</p>
						</button>

						<button on:click={() => goto('/recipes')} class="quick-action-btn btn-secondary">
							<div class="action-icon">
								<Search size={28} aria-hidden="true" />
							</div>
							<h3 class="action-title">Browse Recipes</h3>
							<p class="action-description">View all your recipes</p>
						</button>

						<button on:click={() => goto('/import')} class="quick-action-btn btn-secondary">
							<div class="action-icon">
								<Download size={28} aria-hidden="true" />
							</div>
							<h3 class="action-title">Import from Extension</h3>
							<p class="action-description">Import recipes from websites</p>
						</button>

						<button on:click={() => goto('/export')} class="quick-action-btn btn-secondary">
							<div class="action-icon">
								<Upload size={28} aria-hidden="true" />
							</div>
							<h3 class="action-title">Export Data</h3>
							<p class="action-description">Download your recipes</p>
						</button>
					</div>
				</div>

				<!-- Getting Started -->
				<div class="mt-12 p-6 rounded-lg" style="background: var(--accent-50);">
					<h3 class="text-lg font-semibold mb-3 flex items-center gap-2" style="color: var(--accent-800);">
						<Rocket size={20} aria-hidden="true" />
						<span>Getting Started</span>
					</h3>
					<ul class="space-y-3" style="color: var(--accent-700);">
						<li class="flex items-center gap-2">
							<Check size={16} aria-hidden="true" />
							<span>Account created successfully</span>
						</li>
						{#if !loadingStats && stats}
							{#if stats.total_recipes === 0}
								<li class="flex items-center gap-2">
									<span class="w-4 h-4 rounded-full border-2 border-current flex-shrink-0" aria-hidden="true"></span>
									<a href="/recipes/new" class="link font-medium">Add your first recipe</a>
									<span class="text-sm">to get started</span>
								</li>
							{:else}
								<li class="flex items-center gap-2">
									<Check size={16} aria-hidden="true" />
									<span>Added {stats.total_recipes} recipe{stats.total_recipes !== 1 ? 's' : ''}</span>
								</li>
							{/if}
							<li class="flex items-center gap-2">
								<span class="w-4 h-4 rounded-full border-2 border-current flex-shrink-0" aria-hidden="true"></span>
								<a href="/import" class="link font-medium">Install the browser extension</a>
								<span class="text-sm">to import recipes from websites</span>
							</li>
							<li class="flex items-center gap-2">
								<span class="w-4 h-4 rounded-full border-2 border-current flex-shrink-0" aria-hidden="true"></span>
								<a href="/ai-generate" class="link font-medium">Try AI recipe generation</a>
								<span class="text-sm">to create custom recipes</span>
							</li>
						{/if}
					</ul>
				</div>
			</div>
		</main>
	</div>
{:else}
	<div class="min-h-screen flex items-center justify-center">
		<p class="text-lg" style="color: var(--text-600);">Loading...</p>
	</div>
{/if}

<style>
	.stat-card {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 1.75rem;
		text-align: center;
		transition: all var(--transition-base);
		box-shadow: var(--shadow-sm);
		cursor: pointer;
		width: 100%;
		font: inherit;
	}

	.stat-card:hover {
		transform: translateY(-2px);
		box-shadow: var(--shadow-warm-glow);
		border-color: var(--accent-300);
		background: var(--accent-50);
	}

	.stat-card:active {
		transform: translateY(0);
	}

	.stat-icon {
		display: flex;
		justify-content: center;
		margin-bottom: 1rem;
	}

	.stat-number {
		font-family: var(--font-display);
		font-size: 2.5rem;
		font-weight: 700;
		color: var(--text-900);
		margin-bottom: 0.5rem;
		line-height: 1;
	}

	.stat-label {
		font-family: var(--font-ui);
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-600);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.quick-action-btn {
		padding: 1.5rem;
		text-align: left;
		border-radius: var(--radius-lg);
		min-height: 140px;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		justify-content: flex-start;
		transition: all var(--transition-base);
	}

	.quick-action-btn:hover {
		transform: translateY(-2px);
		box-shadow: var(--shadow-warm-glow);
	}

	.quick-action-btn:active {
		transform: translateY(0);
	}

	.action-icon {
		margin-bottom: 0.75rem;
	}

	.action-title {
		font-family: var(--font-display);
		font-size: 1.125rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}

	.action-description {
		font-size: 0.875rem;
		opacity: 0.9;
	}

	.link {
		color: var(--accent-600);
		text-decoration: none;
		transition: all var(--transition-base);
		border-bottom: 1px solid var(--accent-300);
	}

	.link:hover {
		color: var(--accent-700);
		border-bottom-color: var(--accent-600);
	}
</style>
