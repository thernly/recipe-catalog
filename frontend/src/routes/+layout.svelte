<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { auth } from '$lib/stores/auth';
	import Navbar from '$lib/components/Navbar.svelte';
	import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';
	import Toast from '$lib/components/Toast.svelte';
	import { dialog } from '$lib/stores/dialog';
	import type { User } from '$lib/types';

	let user: User | null = null;
	let isAuthPage = false;

	// Subscribe to auth state
	onMount(() => {
		const unsubscribe = auth.subscribe((state) => {
			user = state.user;
		});

		// Initialize auth
		auth.init();

		return unsubscribe;
	});

	// Check if current page is auth or landing page
	$: isAuthPage = $page.url.pathname === '/' || $page.url.pathname.startsWith('/auth');
</script>

<!-- Show Navbar only for authenticated users and not on landing/auth pages -->
{#if user && !isAuthPage}
	<Navbar />
{/if}

<slot />

<!-- Global components -->
<ConfirmDialog
	open={$dialog.open}
	title={$dialog.title}
	message={$dialog.message}
	onConfirm={$dialog.onConfirm}
	onCancel={() => dialog.close()}
/>
<Toast />
