<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { auth } from '$lib/stores/auth';

	let loading = true;
	let error = '';
	let provider = '';

	onMount(async () => {
		provider = $page.params.provider;
		const code = $page.url.searchParams.get('code');
		const state = $page.url.searchParams.get('state');
		const errorParam = $page.url.searchParams.get('error');
		const errorDescription = $page.url.searchParams.get('error_description');

		// Check for OAuth errors
		if (errorParam) {
			loading = false;
			if (errorParam === 'access_denied') {
				error = 'You cancelled the login process. Please try again.';
			} else {
				error = errorDescription || `Authentication error: ${errorParam}`;
			}
			return;
		}

		// Validate required params
		if (!code || !state) {
			loading = false;
			error = 'Invalid callback parameters. Please try logging in again.';
			return;
		}

		try {
			// Exchange code for token by calling backend callback endpoint
			const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
			const callbackUrl = `${apiUrl}/api/auth/${provider}/callback?code=${code}&state=${state}`;

			const response = await fetch(callbackUrl, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || 'Authentication failed');
			}

			const data = await response.json();

			// Store the access token
			if (data.access_token) {
				localStorage.setItem('auth_token', data.access_token);
				await auth.init();
				goto('/dashboard');
			} else {
				throw new Error('No access token received');
			}
		} catch (err) {
			loading = false;
			error = err instanceof Error ? err.message : 'Authentication failed. Please try again.';
			console.error('OAuth callback error:', err);
		}
	});
</script>

<svelte:head>
	<title>Authenticating... - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50 flex items-center justify-center py-12 px-4">
	<div class="max-w-md w-full text-center">
		{#if loading}
			<div class="card">
				<div class="mb-4">
					<div class="spinner"></div>
				</div>
				<h1 class="text-2xl font-bold mb-2" style="color: var(--text-900);">
					Signing you in...
				</h1>
				<p style="color: var(--text-600);">
					Please wait while we complete authentication with {provider}
				</p>
			</div>
		{:else if error}
			<div class="card">
				<div class="mb-4 text-6xl">⚠️</div>
				<h1 class="text-2xl font-bold mb-2" style="color: var(--text-900);">
					Authentication Failed
				</h1>
				<p class="mb-6" style="color: var(--text-600);">{error}</p>
				<div class="flex gap-4 justify-center">
					<a href="/auth/login" class="btn btn-primary">Back to Login</a>
					<a href="/" class="btn btn-outline">Go Home</a>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.spinner {
		width: 48px;
		height: 48px;
		border: 4px solid var(--neutral-200);
		border-top-color: var(--accent-500);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.btn-outline {
		background: white;
		border: 1px solid var(--neutral-300);
		color: var(--text-900);
		padding: 0.75rem 1.5rem;
		border-radius: var(--radius-md);
		text-decoration: none;
		display: inline-block;
		transition: all var(--transition-fast);
	}

	.btn-outline:hover {
		background: var(--neutral-50);
		border-color: var(--neutral-400);
	}
</style>
