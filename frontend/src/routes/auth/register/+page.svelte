<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { getAvailableProviders, initiateOAuthFlow, type ProviderInfo } from '$lib/api/oauth';
	import { Check, X, AlertCircle } from 'lucide-svelte';

	let email = '';
	let password = '';
	let confirmPassword = '';
	let displayName = '';
	let error = '';
	let loading = false;
	let providers: ProviderInfo[] = [];
	let loadingProviders = true;

	// Field touched states for showing validation
	let emailTouched = false;
	let passwordTouched = false;
	let confirmPasswordTouched = false;

	// Shake animation trigger
	let shakeError = false;

	// Password validation states
	$: passwordLength = password.length >= 12;
	$: passwordUppercase = /[A-Z]/.test(password);
	$: passwordLowercase = /[a-z]/.test(password);
	$: passwordNumber = /[0-9]/.test(password);
	$: passwordValid = passwordLength && passwordUppercase && passwordLowercase && passwordNumber;
	$: passwordsMatch = password === confirmPassword && confirmPassword.length > 0;
	$: emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

	function triggerShake() {
		shakeError = true;
		setTimeout(() => shakeError = false, 500);
	}

	async function handleRegister() {
		error = '';

		// Mark all fields as touched
		emailTouched = true;
		passwordTouched = true;
		confirmPasswordTouched = true;

		// Validate email
		if (!emailValid) {
			error = 'Please enter a valid email address';
			triggerShake();
			return;
		}

		// Validate password strength
		if (!passwordValid) {
			error = 'Password does not meet requirements';
			triggerShake();
			return;
		}

		// Validate passwords match
		if (!passwordsMatch) {
			error = 'Passwords do not match';
			triggerShake();
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
			triggerShake();
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
				<div class="form-field">
					<label for="email" class="block text-sm font-medium mb-2" style="color: var(--text-900);">
						Email Address
					</label>
					<div class="input-wrapper">
						<input
							id="email"
							type="email"
							bind:value={email}
							on:blur={() => emailTouched = true}
							required
							class="form-input"
							class:valid={emailTouched && emailValid}
							class:invalid={emailTouched && email.length > 0 && !emailValid}
							placeholder="you@example.com"
							disabled={loading}
						/>
						{#if emailTouched && email.length > 0}
							<span class="input-icon" class:success={emailValid} class:error={!emailValid}>
								{#if emailValid}
									<Check size={18} />
								{:else}
									<AlertCircle size={18} />
								{/if}
							</span>
						{/if}
					</div>
					{#if emailTouched && email.length > 0 && !emailValid}
						<p class="field-error">Please enter a valid email address</p>
					{/if}
				</div>

				<!-- Password -->
				<div class="form-field">
					<label
						for="password"
						class="block text-sm font-medium mb-2"
						style="color: var(--text-900);"
					>
						Password
					</label>
					<div class="input-wrapper">
						<input
							id="password"
							type="password"
							bind:value={password}
							on:blur={() => passwordTouched = true}
							required
							class="form-input"
							class:valid={passwordTouched && passwordValid}
							class:invalid={passwordTouched && password.length > 0 && !passwordValid}
							placeholder="••••••••"
							disabled={loading}
						/>
						{#if passwordTouched && password.length > 0}
							<span class="input-icon" class:success={passwordValid} class:error={!passwordValid}>
								{#if passwordValid}
									<Check size={18} />
								{:else}
									<AlertCircle size={18} />
								{/if}
							</span>
						{/if}
					</div>
					<!-- Password requirements checklist -->
					{#if password.length > 0 || passwordTouched}
						<div class="password-requirements">
							<div class="requirement" class:met={passwordLength}>
								{#if passwordLength}<Check size={14} />{:else}<X size={14} />{/if}
								<span>At least 12 characters</span>
							</div>
							<div class="requirement" class:met={passwordUppercase}>
								{#if passwordUppercase}<Check size={14} />{:else}<X size={14} />{/if}
								<span>One uppercase letter</span>
							</div>
							<div class="requirement" class:met={passwordLowercase}>
								{#if passwordLowercase}<Check size={14} />{:else}<X size={14} />{/if}
								<span>One lowercase letter</span>
							</div>
							<div class="requirement" class:met={passwordNumber}>
								{#if passwordNumber}<Check size={14} />{:else}<X size={14} />{/if}
								<span>One number</span>
							</div>
						</div>
					{:else}
						<p class="mt-2 text-xs" style="color: var(--text-500);">
							Must be at least 12 characters with uppercase, lowercase, and numbers
						</p>
					{/if}
				</div>

				<!-- Confirm Password -->
				<div class="form-field">
					<label
						for="confirmPassword"
						class="block text-sm font-medium mb-2"
						style="color: var(--text-900);"
					>
						Confirm Password
					</label>
					<div class="input-wrapper">
						<input
							id="confirmPassword"
							type="password"
							bind:value={confirmPassword}
							on:blur={() => confirmPasswordTouched = true}
							required
							class="form-input"
							class:valid={confirmPasswordTouched && passwordsMatch}
							class:invalid={confirmPasswordTouched && confirmPassword.length > 0 && !passwordsMatch}
							placeholder="••••••••"
							disabled={loading}
						/>
						{#if confirmPasswordTouched && confirmPassword.length > 0}
							<span class="input-icon" class:success={passwordsMatch} class:error={!passwordsMatch}>
								{#if passwordsMatch}
									<Check size={18} />
								{:else}
									<AlertCircle size={18} />
								{/if}
							</span>
						{/if}
					</div>
					{#if confirmPasswordTouched && confirmPassword.length > 0 && !passwordsMatch}
						<p class="field-error">Passwords do not match</p>
					{/if}
				</div>

				<!-- Error Message -->
				{#if error}
					<div
						class="error-message"
						class:shake={shakeError}
					>
						<AlertCircle size={18} />
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

<style>
	.form-field {
		margin-bottom: 0;
	}

	.input-wrapper {
		position: relative;
	}

	.form-input {
		width: 100%;
		padding: 0.75rem 2.5rem 0.75rem 1rem;
		border: 1px solid var(--neutral-300);
		border-radius: var(--radius-md);
		font-size: 1rem;
		background: white;
		transition: all var(--transition-fast);
	}

	.form-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.form-input.valid {
		border-color: var(--success-500, #22c55e);
	}

	.form-input.valid:focus {
		box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
	}

	.form-input.invalid {
		border-color: var(--error-500, #ef4444);
	}

	.form-input.invalid:focus {
		box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
	}

	.input-icon {
		position: absolute;
		right: 0.75rem;
		top: 50%;
		transform: translateY(-50%);
		display: flex;
		align-items: center;
	}

	.input-icon.success {
		color: var(--success-500, #22c55e);
	}

	.input-icon.error {
		color: var(--error-500, #ef4444);
	}

	.field-error {
		margin-top: 0.375rem;
		font-size: 0.8125rem;
		color: var(--error-500, #ef4444);
		animation: slideDown 0.2s ease-out;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-0.25rem);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.password-requirements {
		margin-top: 0.75rem;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.375rem;
	}

	.requirement {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.75rem;
		color: var(--text-500);
		transition: color var(--transition-fast);
	}

	.requirement.met {
		color: var(--success-500, #22c55e);
	}

	.requirement.met :global(svg) {
		color: var(--success-500, #22c55e);
	}

	.requirement:not(.met) :global(svg) {
		color: var(--neutral-400);
	}

	.error-message {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 1rem;
		border-radius: var(--radius-md);
		background: var(--color-error-bg, #fef2f2);
		color: var(--color-error-text, #dc2626);
	}

	.error-message.shake {
		animation: shake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97);
	}

	@keyframes shake {
		0%, 100% { transform: translateX(0); }
		10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
		20%, 40%, 60%, 80% { transform: translateX(4px); }
	}
</style>
