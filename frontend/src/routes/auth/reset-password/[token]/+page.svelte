<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { apiRequest } from '$lib/api/client';

	let token = '';
	let password = '';
	let confirmPassword = '';
	let loading = false;
	let success = false;
	let error = '';

	// Password validation
	let passwordErrors: string[] = [];
	$: {
		passwordErrors = [];
		if (password.length > 0 && password.length < 12) {
			passwordErrors.push('Must be at least 12 characters');
		}
		if (password.length > 0 && !/[A-Z]/.test(password)) {
			passwordErrors.push('Must contain uppercase letter');
		}
		if (password.length > 0 && !/[a-z]/.test(password)) {
			passwordErrors.push('Must contain lowercase letter');
		}
		if (password.length > 0 && !/\d/.test(password)) {
			passwordErrors.push('Must contain a number');
		}
	}

	onMount(() => {
		token = $page.params.token!;
	});

	async function handleSubmit() {
		error = '';

		// Validation
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		if (passwordErrors.length > 0) {
			error = 'Please fix password requirements';
			return;
		}

		loading = true;

		try {
			await apiRequest('/api/auth/reset-password', {
				method: 'POST',
				body: JSON.stringify({ token, new_password: password }),
				requireAuth: false
			});

			success = true;

			// Redirect to login after 3 seconds
			setTimeout(() => {
				goto('/auth/login');
			}, 3000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to reset password';
			console.error('Reset password error:', err);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Reset Password - Recipe Catalog</title>
</svelte:head>

<div class="auth-page">
	<div class="auth-container">
		<div class="auth-card">
			<div class="auth-header">
				<h1 class="auth-title">Create New Password</h1>
				<p class="auth-subtitle">Choose a strong password for your account</p>
			</div>

			{#if success}
				<!-- Success message -->
				<div class="success-box">
					<div class="success-icon">✓</div>
					<h2 class="success-title">Password Reset Complete</h2>
					<p class="success-text">
						Your password has been successfully updated. You will be redirected to the login page
						shortly.
					</p>
					<button on:click={() => goto('/auth/login')} class="btn btn-primary btn-block">
						Go to Login
					</button>
				</div>
			{:else}
				<!-- Form -->
				<form on:submit|preventDefault={handleSubmit} class="auth-form">
					<div class="form-group">
						<label for="password" class="form-label">New Password</label>
						<input
							id="password"
							type="password"
							bind:value={password}
							required
							class="form-input"
							placeholder="Enter new password"
							disabled={loading}
						/>
						{#if password.length > 0 && passwordErrors.length > 0}
							<div class="validation-hints">
								{#each passwordErrors as hint}
									<div class="validation-hint error">✗ {hint}</div>
								{/each}
							</div>
						{/if}
					</div>

					<div class="form-group">
						<label for="confirmPassword" class="form-label">Confirm Password</label>
						<input
							id="confirmPassword"
							type="password"
							bind:value={confirmPassword}
							required
							class="form-input"
							placeholder="Confirm new password"
							disabled={loading}
						/>
						{#if confirmPassword.length > 0 && password !== confirmPassword}
							<div class="validation-hint error">✗ Passwords do not match</div>
						{:else if confirmPassword.length > 0 && password === confirmPassword}
							<div class="validation-hint success">✓ Passwords match</div>
						{/if}
					</div>

					<div class="password-requirements">
						<p class="requirements-title">Password Requirements:</p>
						<ul class="requirements-list">
							<li class:met={password.length >= 12}>At least 12 characters</li>
							<li class:met={/[A-Z]/.test(password)}>One uppercase letter</li>
							<li class:met={/[a-z]/.test(password)}>One lowercase letter</li>
							<li class:met={/\d/.test(password)}>One number</li>
						</ul>
					</div>

					{#if error}
						<div class="error-box">{error}</div>
					{/if}

					<button
						type="submit"
						class="btn btn-primary btn-block"
						disabled={loading || passwordErrors.length > 0 || password !== confirmPassword}
					>
						{loading ? 'Resetting...' : 'Reset Password'}
					</button>

					<div class="auth-footer">
						<p class="footer-text">
							Remember your password?
							<a href="/auth/login" class="footer-link">Sign in</a>
						</p>
					</div>
				</form>
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

	.auth-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.auth-title {
		font-size: 2rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0 0 0.5rem 0;
	}

	.auth-subtitle {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0;
		line-height: 1.5;
	}

	.auth-form {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.form-label {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-700);
	}

	.form-input {
		padding: 0.75rem;
		border: 1px solid var(--neutral-300);
		border-radius: var(--radius-md);
		font-size: 1rem;
		color: var(--text-900);
		transition: all var(--transition-fast);
		background: var(--neutral-white);
	}

	.form-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.form-input:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.validation-hints {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.validation-hint {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		border-radius: var(--radius-sm);
	}

	.validation-hint.error {
		color: var(--error-700);
		background: var(--error-50);
	}

	.validation-hint.success {
		color: var(--success-700);
		background: var(--success-50);
	}

	.password-requirements {
		padding: 1rem;
		background: var(--neutral-50);
		border-radius: var(--radius-md);
	}

	.requirements-title {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--text-700);
		margin: 0 0 0.5rem 0;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.requirements-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.requirements-list li {
		font-size: 0.875rem;
		color: var(--text-600);
		padding-left: 1.25rem;
		position: relative;
	}

	.requirements-list li::before {
		content: '○';
		position: absolute;
		left: 0;
		color: var(--text-400);
	}

	.requirements-list li.met {
		color: var(--success-700);
		font-weight: 500;
	}

	.requirements-list li.met::before {
		content: '✓';
		color: var(--success-600);
	}

	.btn-block {
		width: 100%;
	}

	.error-box {
		padding: 0.75rem;
		background: var(--error-50);
		border: 1px solid var(--error-200);
		border-radius: var(--radius-md);
		color: var(--error-700);
		font-size: 0.875rem;
		text-align: center;
	}

	.success-box {
		text-align: center;
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
	}

	.success-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0 0 1rem 0;
	}

	.success-text {
		font-size: 1rem;
		color: var(--text-700);
		margin: 0 0 2rem 0;
		line-height: 1.6;
	}

	.auth-footer {
		text-align: center;
		margin-top: 1rem;
	}

	.footer-text {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0;
	}

	.footer-link {
		color: var(--accent-600);
		text-decoration: none;
		font-weight: 600;
		transition: color var(--transition-fast);
	}

	.footer-link:hover {
		color: var(--accent-700);
		text-decoration: underline;
	}
</style>
