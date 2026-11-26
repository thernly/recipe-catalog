<script lang="ts">
	import '@fontsource-variable/outfit';
	import '@fontsource-variable/lora';
	import '../app.css';
	import { watchTheme } from '#lib/stores/theme.js';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { auth } from '#lib/stores/auth.js';
	import Navbar from '#lib/components/Navbar.svelte';
	import ConfirmDialog from '#lib/components/ConfirmDialog.svelte';
	import Toast from '#lib/components/Toast.svelte';
	import { dialog } from '#lib/stores/dialog.js';
	import type { User } from '#lib/types/index.js';

	let user: User | null = null;

	// Subscribe to auth state
	onMount(() => {
		const stopTheme = watchTheme();
		const unsubscribe = auth.subscribe((state) => {
			user = state.user;
		});

		// Initialize auth
		auth.init();

		return () => {
			unsubscribe();
			stopTheme();
		};
	});
</script>

<!-- Show Navbar only for authenticated users and not on landing/auth pages -->
{#if user && !(page.url.pathname === '/' || page.url.pathname.startsWith('/auth'))}
	<Navbar />
{/if}

<slot></slot>

<!-- Global components -->
<ConfirmDialog
	open={$dialog.open}
	title={$dialog.title}
	message={$dialog.message}
	confirmLabel={$dialog.confirmLabel}
	danger={$dialog.danger}
	onConfirm={$dialog.onConfirm}
	onCancel={() => dialog.close()}
/>
<Toast />
