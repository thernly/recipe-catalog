<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let user: any = null;

	onMount(() => {
		const unsubscribe = auth.subscribe((state) => {
			user = state.user;
		});

		return unsubscribe;
	});

	function handleLogout() {
		auth.logout();
		goto('/');
	}
</script>

<nav
	class="sticky top-0 z-50 h-16 flex items-center justify-between px-6"
	style="background: var(--color-navbar-bg); color: var(--color-navbar-text);"
>
	<div class="flex items-center gap-6">
		<a href="/dashboard" class="flex items-center gap-3 hover:opacity-80 transition">
			<span class="text-2xl">🍽️</span>
			<span class="font-semibold text-lg">Recipe Catalog</span>
		</a>

		<div class="flex items-center gap-4 ml-4">
			<a
				href="/dashboard"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-sm"
			>
				Dashboard
			</a>
			<a
				href="/recipes"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-sm"
			>
				Recipes
			</a>
			<a
				href="/export"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-sm"
			>
				Export
			</a>
			<a
				href="/settings"
				class="px-3 py-2 rounded-md hover:bg-white/10 transition text-sm"
			>
				Settings
			</a>
		</div>
	</div>

	<div class="flex items-center gap-4">
		{#if user}
			<span class="text-sm">{user.email}</span>
		{/if}
		<button
			on:click={handleLogout}
			class="px-4 py-2 rounded-md hover:bg-white/10 transition text-sm"
		>
			Logout
		</button>
	</div>
</nav>
