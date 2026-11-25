<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		getInviteLinkInfo,
		joinViaInviteLink,
		type HouseholdInviteLink,
	} from '#lib/api/households.js';
	import { auth } from '#lib/stores/auth.js';

	export let params: { code: string };

	let invite: HouseholdInviteLink | null = null;
	let loading = true;
	let error = ''; // code can't be used: replaces the page
	let actionError = ''; // join failed: shown under the button
	let joining = false;

	$: isLoggedIn = $auth.user !== null;

	onMount(async () => {
		try {
			invite = await getInviteLinkInfo(params.code);
			if (invite.used_at) error = 'This invite code has already been used';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load invite';
		} finally {
			loading = false;
		}
	});

	async function handleJoin() {
		if (!isLoggedIn) {
			goto(
				`/auth/login?redirect=${encodeURIComponent(`/join/${params.code}`)}`,
			);
			return;
		}

		joining = true;
		actionError = '';
		try {
			await joinViaInviteLink(params.code, true);
			goto('/settings');
		} catch (err) {
			actionError =
				err instanceof Error ? err.message : 'Failed to join household';
		} finally {
			joining = false;
		}
	}
</script>

<svelte:head>
	<title>Join Household - Recipe Catalog</title>
</svelte:head>

<div
	class="min-h-screen bg-neutral-50 flex items-center justify-center py-12 px-4"
>
	<div class="max-w-md w-full card text-center">
		<h1 class="text-2xl font-bold mb-6" style="color: var(--text-900);">
			Join a household
		</h1>

		{#if loading}
			<p style="color: var(--text-600);">Loading invite...</p>
		{:else if error || !invite}
			<p class="mb-6" style="color: var(--text-600);" role="alert">
				{error || 'Invite code not found'}
			</p>
			<a href="/" class="btn btn-primary">Go to Home</a>
		{:else}
			<p class="mb-1" style="color: var(--text-900);">
				You've been invited to join
			</p>
			<h2 class="text-2xl font-bold mb-1" style="color: var(--accent-600);">
				{invite.household_name || 'a household'}
			</h2>
			{#if invite.created_by_display_name}
				<p class="text-sm" style="color: var(--text-600);">
					Invited by {invite.created_by_display_name}
				</p>
			{/if}

			<p class="text-sm my-6" style="color: var(--text-700);">
				{#if isLoggedIn}
					Joining moves your recipes, collections and shopping lists into this
					household, where its members can see them. If you are in another
					shared household, you will leave it.
				{:else}
					Sign in or create an account to join.
				{/if}
			</p>

			<button
				type="button"
				class="btn btn-primary w-full"
				on:click={handleJoin}
				disabled={joining}
			>
				{joining
					? 'Joining...'
					: isLoggedIn
						? 'Join household'
						: 'Sign in to join'}
			</button>

			{#if actionError}
				<p
					class="text-sm mt-4"
					style="color: var(--color-error-text);"
					role="alert"
				>
					{actionError}
				</p>
			{/if}
		{/if}
	</div>
</div>
