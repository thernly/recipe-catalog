<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { apiRequest } from '$lib/api/client';

	let token = '';
	let loading = true;
	let success = false;
	let error = '';

	onMount(async () => {
		token = $page.params.token;
		await verifyEmail();
	});

	async function verifyEmail() {
		loading = true;
		error = '';

		try {
			await apiRequest(`/api/auth/verify-email/${token}`, {
				method: 'POST',
				requireAuth: false
			});

			success = true;

			// Redirect to login after 5 seconds
			setTimeout(() => {
				goto('/auth/login');
			}, 5000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to verify email';
			console.error('Email verification error:', err);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Verify Email - Recipe Catalog</title>
</svelte:head>

<div class="auth-page">
	<div class="auth-container">
		<div class="auth-card">
			{#if loading}
				<!-- Loading state -->
				<div class="status-box">
					<div class="loading-spinner">⏳</div>
					<h1 class="status-title">Verifying Your Email...</h1>
					<p class="status-text">Please wait while we verify your email address.</p>
				</div>
			{:else if success}
				<!-- Success state -->
				<div class="status-box">
					<div class="success-icon">✓</div>
					<h1 class="status-title">Email Verified!</h1>
					<p class="status-text">
						Your email has been successfully verified. You can now use all features of Recipe
						Catalog.
					</p>
					<p class="status-hint">Redirecting to login page...</p>
					<button on:click={() => goto('/auth/login')} class="btn btn-primary btn-block">
						Go to Login
					</button>
				</div>
			{:else if error}
				<!-- Error state -->
				<div class="status-box">
					<div class="error-icon">⚠️</div>
					<h1 class="status-title">Verification Failed</h1>
					<p class="status-text error-text">{error}</p>

					<div class="error-actions">
						<p class="action-hint">This verification link may have expired or already been used.</p>
						<button on:click={() => goto('/auth/resend-verification')} class="btn btn-secondary">
							Request New Link
						</button>
						<button on:click={() => goto('/auth/login')} class="btn btn-primary">
							Go to Login
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.auth-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, var(--primary-50) 0%, var(--accent-50) 100%);
		padding: 2rem;
	}

	.auth-container {
		width: 100%;
		max-width: 28rem;
	}

	.auth-card {
		background: var(--neutral-white);
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-lg);
		padding: 2.5rem;
	}

	.status-box {
		text-align: center;
	}

	.loading-spinner {
		font-size: 4rem;
		margin-bottom: 1.5rem;
		animation: spin 2s linear infinite;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	.success-icon {
		width: 4rem;
		height: 4rem;
		background: var(--success-100);
		color: var(--success-600);
		border-radius: var(--radius-full);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		margin: 0 auto 1.5rem;
		animation: scaleIn 0.3s ease-out;
	}

	.error-icon {
		font-size: 4rem;
		margin-bottom: 1.5rem;
	}

	@keyframes scaleIn {
		from {
			transform: scale(0);
		}
		to {
			transform: scale(1);
		}
	}

	.status-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0 0 1rem 0;
	}

	.status-text {
		font-size: 1rem;
		color: var(--text-700);
		margin: 0 0 1rem 0;
		line-height: 1.6;
	}

	.status-text.error-text {
		color: var(--error-700);
		background: var(--error-50);
		padding: 0.75rem;
		border-radius: var(--radius-md);
		border: 1px solid var(--error-200);
	}

	.status-hint {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 2rem 0;
	}

	.error-actions {
		margin-top: 2rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.action-hint {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 1rem 0;
	}

	.btn-block {
		width: 100%;
	}
</style>
