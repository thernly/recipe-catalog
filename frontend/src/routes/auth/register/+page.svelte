<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let email = '';
	let password = '';
	let confirmPassword = '';
	let displayName = '';
	let error = '';
	let loading = false;

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
			await auth.register(email, password, displayName || undefined);
			goto('/dashboard');
		} catch (err: any) {
			error = err.message || 'Registration failed. Please try again.';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		// If already logged in, redirect to dashboard
		auth.subscribe((state) => {
			if (state.user) {
				goto('/dashboard');
			}
		});
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

			<!-- Divider -->
			<div class="mt-6 flex items-center">
				<div class="flex-1 border-t" style="border-color: var(--neutral-200);"></div>
				<span class="px-4 text-sm" style="color: var(--text-500);">OR</span>
				<div class="flex-1 border-t" style="border-color: var(--neutral-200);"></div>
			</div>

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
