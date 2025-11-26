<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { getAvailableProviders, initiateOAuthFlow, type ProviderInfo } from '$lib/api/oauth';

	let email = '';
	let password = '';
	let confirmPassword = '';
	let displayName = '';
	let error = '';
	let loading = false;
	let providers: ProviderInfo[] = [];
	let loadingProviders = true;

	async function handleRegister() {
		error = '';

		// Validate passwords match
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		// Validate password strength
		if (password.length < 12) {
			error = 'Password must be at least 12 characters long';
			return;
		}

		if (!/[A-Z]/.test(password)) {
			error = 'Password must contain at least one uppercase letter';
			return;
		}

		if (!/[a-z]/.test(password)) {
			error = 'Password must contain at least one lowercase letter';
			return;
		}

		if (!/[0-9]/.test(password)) {
			error = 'Password must contain at least one number';
			return;
		}

		loading = true;

		try {
			// Register the user
			await auth.register(email, password, displayName || undefined);
			// Login separately for clearer error handling
			await auth.login(email, password);
			goto('/dashboard');
		} catch (err: any) {
			error = err.message || 'Registration failed. Please try again.';
		} finally {
			loading = false;
		}
	}

	function handleOAuthSignup(provider: string) {
		error = '';
		initiateOAuthFlow(provider);
	}

	function getProviderIcon(provider: string): string {
		switch (provider) {
			case 'google':
				return 'G';
			case 'microsoft':
				return 'M';
			case 'github':
				return '';
			default:
				return '';
		}
	}

	onMount(async () => {
		// If already logged in, redirect to dashboard
		const currentAuth = get(auth);
		if (currentAuth.user) {
			goto('/dashboard');
			return;
		}

		// Load available OAuth providers
		try {
			providers = await getAvailableProviders();
		} catch (err) {
			console.error('Failed to load OAuth providers:', err);
		} finally {
			loadingProviders = false;
		}
	});
</script>

<svelte:head>
	<title>Sign Up - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50 flex items-center justify-center py-12 px-4">
	<div class="max-w-md w-full">
		<!-- Header -->
		<div class="text-center mb-8">
			<h1 class="text-4xl font-bold mb-2" style="color: var(--text-900);">Create Account</h1>
			<p style="color: var(--text-600);">Join Recipe Catalog to start organizing your recipes</p>
		</div>

		<!-- Register Form -->
		<div class="card">
			<!-- OAuth Providers -->
			{#if !loadingProviders && providers.length > 0}
				<div class="space-y-3 mb-6">
					{#each providers.filter((p) => p.enabled) as provider}
						<button
							type="button"
							on:click={() => handleOAuthSignup(provider.name)}
							class="w-full px-4 py-3 rounded-md border border-neutral-300 hover:border-neutral-400 transition-colors flex items-center justify-center gap-3 font-medium"
							style="background: white; color: var(--text-900);"
						>
							<span class="text-xl">{getProviderIcon(provider.name)}</span>
							<span>Sign up with {provider.display_name}</span>
						</button>
					{/each}
				</div>

				<!-- Divider -->
				<div class="mb-6 flex items-center">
					<div class="flex-1 border-t" style="border-color: var(--neutral-200);"></div>
					<span class="px-4 text-sm" style="color: var(--text-500);">OR</span>
					<div class="flex-1 border-t" style="border-color: var(--neutral-200);"></div>
				</div>
			{/if}

			<form on:submit|preventDefault={handleRegister} class="space-y-6">
				<!-- Display Name -->
				<div>
					<label
						for="displayName"
						class="block text-sm font-medium mb-2"
						style="color: var(--text-900);"
					>
						Display Name (Optional)
					</label>
					<input
						id="displayName"
						type="text"
						bind:value={displayName}
						class="w-full px-4 py-3 rounded-md border border-neutral-300 focus:outline-none focus:ring-2"
						style="border-color: var(--neutral-300); background: white;"
						placeholder="Your name"
						disabled={loading}
					/>
				</div>

				<!-- Email -->
				<div>
					<label for="email" class="block text-sm font-medium mb-2" style="color: var(--text-900);">
						Email Address
					</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						required
						class="w-full px-4 py-3 rounded-md border border-neutral-300 focus:outline-none focus:ring-2"
						style="border-color: var(--neutral-300); background: white;"
						placeholder="you@example.com"
						disabled={loading}
					/>
				</div>

				<!-- Password -->
				<div>
					<label
						for="password"
						class="block text-sm font-medium mb-2"
						style="color: var(--text-900);"
					>
						Password
					</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						required
						class="w-full px-4 py-3 rounded-md border border-neutral-300 focus:outline-none focus:ring-2"
						style="border-color: var(--neutral-300); background: white;"
						placeholder="••••••••"
						disabled={loading}
					/>
					<p class="mt-2 text-xs" style="color: var(--text-500);">
						Must be at least 12 characters with uppercase, lowercase, and numbers
					</p>
				</div>

				<!-- Confirm Password -->
				<div>
					<label
						for="confirmPassword"
						class="block text-sm font-medium mb-2"
						style="color: var(--text-900);"
					>
						Confirm Password
					</label>
					<input
						id="confirmPassword"
						type="password"
						bind:value={confirmPassword}
						required
						class="w-full px-4 py-3 rounded-md border border-neutral-300 focus:outline-none focus:ring-2"
						style="border-color: var(--neutral-300); background: white;"
						placeholder="••••••••"
						disabled={loading}
					/>
				</div>

				<!-- Error Message -->
				{#if error}
					<div
						class="p-4 rounded-md"
						style="background: var(--color-error-bg); color: var(--color-error-text);"
					>
						<p class="text-sm">{error}</p>
					</div>
				{/if}

				<!-- Submit Button -->
				<button
					type="submit"
					class="w-full btn btn-primary"
					disabled={loading}
					style="opacity: {loading ? 0.6 : 1}; cursor: {loading ? 'not-allowed' : 'pointer'};"
				>
					{loading ? 'Creating account...' : 'Create Account'}
				</button>
			</form>

			<!-- Login Link -->
			<div class="mt-6 text-center">
				<p style="color: var(--text-600);">
					Already have an account?
					<a href="/auth/login" class="font-medium" style="color: var(--color-link);"> Sign in </a>
				</p>
			</div>
		</div>

		<!-- Back to Home -->
		<div class="mt-6 text-center">
			<a href="/" class="text-sm" style="color: var(--text-500);">← Back to home</a>
		</div>
	</div>
</div>
