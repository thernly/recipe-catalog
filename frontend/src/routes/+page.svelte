<script lang="ts">
	let theme = 'classic';

	function toggleTheme() {
		theme = theme === 'classic' ? 'professional' : 'classic';
		document.documentElement.setAttribute('data-theme', theme);
		localStorage.setItem('theme', theme);
	}

	import { onMount } from 'svelte';

	onMount(() => {
		const savedTheme = localStorage.getItem('theme') || 'classic';
		theme = savedTheme;
		document.documentElement.setAttribute('data-theme', savedTheme);
	});
</script>

<svelte:head>
	<title>Recipe Catalog - Privacy-Focused Recipe Management</title>
</svelte:head>

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
			<a
				href="/auth/login"
				class="px-4 py-2 rounded-md hover:bg-white/10 transition text-sm"
			>
				Sign In
			</a>
			<a
				href="/auth/register"
				class="px-4 py-2 rounded-md hover:bg-white/10 transition text-sm"
			>
				Sign Up
			</a>
			<button
				on:click={toggleTheme}
				class="px-4 py-2 rounded-md hover:bg-white/10 transition"
				title="Toggle theme"
			>
				{theme === 'classic' ? '🎨' : '💼'}
			</button>
		</div>
	</nav>

	<!-- Hero Section -->
	<main class="container-custom py-16">
		<div class="max-w-4xl mx-auto text-center">
			<h1 class="text-5xl font-bold mb-6" style="color: var(--text-900);">
				Your Personal Recipe Collection
			</h1>
			<p class="text-xl mb-8" style="color: var(--text-600);">
				A privacy-focused web application for organizing and managing your favorite recipes.
				Import from websites, add family recipes, and keep everything in one place.
			</p>

			<div class="flex justify-center gap-4 mb-12">
				<a href="/auth/register" class="btn btn-primary">Get Started</a>
				<a href="/auth/login" class="btn btn-secondary">Sign In</a>
			</div>

			<!-- Feature Cards -->
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
				<div class="card">
					<div class="text-4xl mb-4">🔐</div>
					<h3 class="text-xl font-semibold mb-2">Privacy First</h3>
					<p style="color: var(--text-600);">
						No tracking, no analytics, no third-party data sharing. Your recipes are yours.
					</p>
				</div>

				<div class="card">
					<div class="text-4xl mb-4">📚</div>
					<h3 class="text-xl font-semibold mb-2">Organize Everything</h3>
					<p style="color: var(--text-600);">
						Import from websites or add manually. Organize into collections, search, and filter.
					</p>
				</div>

				<div class="card">
					<div class="text-4xl mb-4">☁️</div>
					<h3 class="text-xl font-semibold mb-2">Access Anywhere</h3>
					<p style="color: var(--text-600);">
						Cloud-synced recipes available on all your devices. Export anytime.
					</p>
				</div>
			</div>

			<!-- Status Info -->
			<div class="mt-16 p-6 rounded-lg" style="background: var(--accent-50);">
				<p class="text-sm font-semibold" style="color: var(--accent-800);">
					🚧 Currently in Development
				</p>
				<p class="text-sm mt-2" style="color: var(--accent-700);">
					This project is being built with SvelteKit + FastAPI + SQLite. Check back soon!
				</p>
			</div>

			<!-- Tech Stack -->
			<div class="mt-12">
				<h2 class="text-2xl font-semibold mb-6">Built With Modern Technology</h2>
				<div class="flex flex-wrap justify-center gap-4">
					<span class="px-4 py-2 rounded-full" style="background: var(--neutral-200);">
						SvelteKit
					</span>
					<span class="px-4 py-2 rounded-full" style="background: var(--neutral-200);">
						FastAPI
					</span>
					<span class="px-4 py-2 rounded-full" style="background: var(--neutral-200);">
						SQLite/D1
					</span>
					<span class="px-4 py-2 rounded-full" style="background: var(--neutral-200);">
						Tailwind CSS
					</span>
					<span class="px-4 py-2 rounded-full" style="background: var(--neutral-200);">
						Cloudflare
					</span>
				</div>
			</div>
		</div>
	</main>

	<!-- Footer -->
	<footer class="mt-24 py-8 text-center" style="background: var(--neutral-100);">
		<p style="color: var(--text-600);">
			Recipe Catalog © 2025 | Privacy-Focused Recipe Management
		</p>
	</footer>
</div>
