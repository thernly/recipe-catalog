<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let user: any = null;

	onMount(() => {
		const unsubscribe = auth.subscribe((state) => {
			if (!state.user) {
				goto('/auth/login');
			} else {
				user = state.user;
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
		<!-- Navbar -->
		<nav
			class="sticky top-0 z-50 h-16 flex items-center justify-between px-6"
			style="background: var(--color-navbar-bg); color: var(--color-navbar-text);"
		>
			<div class="flex items-center gap-3">
				<span class="text-2xl">🍽️</span>
				<span class="font-semibold text-lg">Recipe Catalog</span>
			</div>

			<div class="flex items-center gap-4">
				<span class="text-sm">{user.email}</span>
				<button
					on:click={handleLogout}
					class="px-4 py-2 rounded-md hover:bg-white/10 transition text-sm"
				>
					Logout
				</button>
			</div>
		</nav>

		<!-- Main Content -->
		<main class="container-custom py-12">
			<div class="max-w-4xl mx-auto">
				<!-- Welcome Header -->
				<div class="mb-12">
					<h1 class="text-4xl font-bold mb-2" style="color: var(--text-900);">
						Welcome{user.display_name ? `, ${user.display_name}` : ''}! 👋
					</h1>
					<p class="text-lg" style="color: var(--text-600);">
						Your personal recipe collection dashboard
					</p>
				</div>

				<!-- Stats Cards -->
				<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
					<div class="card text-center">
						<div class="text-4xl mb-2">📚</div>
						<h3 class="text-2xl font-bold mb-1" style="color: var(--text-900);">0</h3>
						<p style="color: var(--text-600);">Total Recipes</p>
					</div>

					<div class="card text-center">
						<div class="text-4xl mb-2">⭐</div>
						<h3 class="text-2xl font-bold mb-1" style="color: var(--text-900);">0</h3>
						<p style="color: var(--text-600);">Favorites</p>
					</div>

					<div class="card text-center">
						<div class="text-4xl mb-2">📂</div>
						<h3 class="text-2xl font-bold mb-1" style="color: var(--text-900);">1</h3>
						<p style="color: var(--text-600);">Collections</p>
					</div>
				</div>

				<!-- Quick Actions -->
				<div class="card">
					<h2 class="text-2xl font-semibold mb-6" style="color: var(--text-900);">Quick Actions</h2>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<button class="btn btn-primary text-left p-6">
							<div class="text-2xl mb-2">➕</div>
							<h3 class="font-semibold mb-1">Add Recipe</h3>
							<p class="text-sm opacity-90">Manually add a new recipe</p>
						</button>

						<button class="btn btn-secondary text-left p-6">
							<div class="text-2xl mb-2">🔍</div>
							<h3 class="font-semibold mb-1">Browse Recipes</h3>
							<p class="text-sm opacity-90">View all your recipes</p>
						</button>

						<button class="btn btn-secondary text-left p-6">
							<div class="text-2xl mb-2">📥</div>
							<h3 class="font-semibold mb-1">Import from Extension</h3>
							<p class="text-sm opacity-90">Import recipes from websites</p>
						</button>

						<button class="btn btn-secondary text-left p-6">
							<div class="text-2xl mb-2">📤</div>
							<h3 class="font-semibold mb-1">Export Data</h3>
							<p class="text-sm opacity-90">Download your recipes</p>
						</button>
					</div>
				</div>

				<!-- Getting Started -->
				<div class="mt-12 p-6 rounded-lg" style="background: var(--accent-50);">
					<h3 class="text-lg font-semibold mb-3" style="color: var(--accent-800);">
						🚀 Getting Started
					</h3>
					<ul class="space-y-2" style="color: var(--accent-700);">
						<li>✓ Account created successfully</li>
						<li>• Add your first recipe to get started</li>
						<li>• Install the browser extension to import recipes</li>
						<li>• Create collections to organize your recipes</li>
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
