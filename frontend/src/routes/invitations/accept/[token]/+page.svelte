<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import {
		getInvitationByToken,
		acceptInvitation,
		declineInvitation,
		type HouseholdInvitation
	} from '$lib/api/households';
	import { auth } from '$lib/stores/auth';
	import { get } from 'svelte/store';

	let token = '';
	let invitation: HouseholdInvitation | null = null;
	let loading = true;
	let error = '';
	let accepting = false;
	let declining = false;

	const currentUser = get(auth).user;
	const isLoggedIn = currentUser !== null;

	async function loadInvitation() {
		loading = true;
		error = '';

		try {
			invitation = await getInvitationByToken(token);

			// Check if invitation is expired
			if (new Date(invitation.expires_at) < new Date()) {
				error = 'This invitation has expired';
			}

			// Check if already accepted
			if (invitation.accepted_at) {
				error = 'This invitation has already been accepted';
			}
		} catch (err) {
			console.error('Failed to load invitation:', err);
			error = err instanceof Error ? err.message : 'Failed to load invitation';
		} finally {
			loading = false;
		}
	}

	async function handleAccept() {
		if (!isLoggedIn) {
			// Redirect to login/signup with return URL
			goto(`/auth/login?redirect=/invitations/accept/${token}`);
			return;
		}

		accepting = true;
		error = '';

		try {
			await acceptInvitation({ token });
			goto('/settings?section=household&message=joined');
		} catch (err) {
			console.error('Failed to accept invitation:', err);
			error = err instanceof Error ? err.message : 'Failed to accept invitation';
		} finally {
			accepting = false;
		}
	}

	async function handleDecline() {
		declining = true;
		error = '';

		try {
			await declineInvitation(token);
			goto('/?message=invitation-declined');
		} catch (err) {
			console.error('Failed to decline invitation:', err);
			error = err instanceof Error ? err.message : 'Failed to decline invitation';
		} finally {
			declining = false;
		}
	}

	onMount(() => {
		token = $page.params.token!;
		loadInvitation();
	});
</script>

<svelte:head>
	<title>Household Invitation - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50 flex items-center justify-center py-12 px-4">
	<div class="max-w-md w-full">
		<div class="card">
			<div class="card-header">
				<h1 class="card-title">🏠 Household Invitation</h1>
			</div>

			{#if loading}
				<div class="text-center py-8">
					<div class="text-4xl mb-4">⏳</div>
					<p class="text-lg" style="color: var(--text-600);">Loading invitation...</p>
				</div>
			{:else if error}
				<div class="py-8">
					<div class="text-center mb-6">
						<div class="text-4xl mb-4">⚠️</div>
						<p class="text-lg font-semibold mb-2" style="color: var(--text-900);">
							Invalid Invitation
						</p>
						<p class="text-sm" style="color: var(--text-600);">{error}</p>
					</div>
					<div class="text-center">
						<a href="/" class="btn btn-primary">Go to Home</a>
					</div>
				</div>
			{:else if invitation}
				<div class="invitation-content">
					<div class="text-center mb-6">
						<p class="text-lg mb-2" style="color: var(--text-900);">You've been invited to join</p>
						<h2 class="text-2xl font-bold mb-1" style="color: var(--accent-600);">
							{invitation.household_name || 'a household'}
						</h2>
						{#if invitation.inviter_display_name}
							<p class="text-sm" style="color: var(--text-600);">
								Invited by {invitation.inviter_display_name}
							</p>
						{/if}
					</div>

					{#if !isLoggedIn}
						<div class="info-box mb-6">
							<p class="text-sm" style="color: var(--text-700);">
								You need to sign in or create an account to accept this invitation.
							</p>
						</div>
					{/if}

					<div class="invitation-details mb-6">
						<h3 class="details-title">What is a household?</h3>
						<p class="details-text">
							A household allows you to share recipes and collections with family members. You'll be
							able to:
						</p>
						<ul class="details-list">
							<li>View and edit shared recipes</li>
							<li>Access shared collections</li>
							<li>Collaborate on meal planning</li>
						</ul>
					</div>

					<div class="button-group">
						<button
							type="button"
							class="btn btn-primary btn-lg"
							on:click={handleAccept}
							disabled={accepting || declining}
						>
							{accepting ? 'Accepting...' : isLoggedIn ? 'Accept Invitation' : 'Sign In to Accept'}
						</button>
						<button
							type="button"
							class="btn btn-outline btn-lg"
							on:click={handleDecline}
							disabled={accepting || declining}
						>
							{declining ? 'Declining...' : 'Decline'}
						</button>
					</div>

					{#if error}
						<div class="error-message mt-4">{error}</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.card {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
		overflow: hidden;
	}

	.card-header {
		padding: 2rem;
		border-bottom: 1px solid var(--neutral-200);
		text-align: center;
	}

	.card-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0;
	}

	.invitation-content {
		padding: 2rem;
	}

	.info-box {
		padding: 1rem;
		background: var(--accent-50);
		border: 1px solid var(--accent-200);
		border-radius: var(--radius-md);
	}

	.invitation-details {
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		padding: 1.5rem;
	}

	.details-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.75rem 0;
	}

	.details-text {
		font-size: 0.875rem;
		color: var(--text-700);
		margin: 0 0 0.75rem 0;
	}

	.details-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.details-list li {
		font-size: 0.875rem;
		color: var(--text-700);
		padding-left: 1.5rem;
		position: relative;
		margin-bottom: 0.5rem;
	}

	.details-list li:before {
		content: '✓';
		position: absolute;
		left: 0;
		color: var(--success-600, #22c55e);
		font-weight: bold;
	}

	.button-group {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.btn-lg {
		padding: 0.875rem 1.5rem;
		font-size: 1rem;
		font-weight: 600;
	}

	.btn-outline {
		background: white;
		border: 1px solid var(--neutral-300);
		color: var(--text-900);
	}

	.btn-outline:hover:not(:disabled) {
		background: var(--neutral-50);
		border-color: var(--neutral-400);
	}

	.error-message {
		padding: 0.75rem;
		background: var(--error-50);
		border: 1px solid var(--error-200);
		border-radius: var(--radius-md);
		color: var(--error-700);
		font-size: 0.875rem;
		text-align: center;
	}

	.mt-4 {
		margin-top: 1rem;
	}

	.mb-6 {
		margin-bottom: 1.5rem;
	}
</style>
