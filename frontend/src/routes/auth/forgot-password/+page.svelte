<script lang="ts">
	import { goto } from '$app/navigation';
	import { apiRequest } from '$lib/api/client';

	let email = '';
	let loading = false;
	let success = false;
	let error = '';

	async function handleSubmit() {
		if (!email) {
			error = 'Please enter your email address';
			return;
		}

		loading = true;
		error = '';
		success = false;

		try {
			await apiRequest('/api/auth/forgot-password', {
				method: 'POST',
				body: JSON.stringify({ email }),
				requireAuth: false
			});

			success = true;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to send reset email';
			console.error('Forgot password error:', err);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Forgot Password - Recipe Catalog</title>
</svelte:head>

<div class="auth-page">
	<div class="auth-container">
		<div class="auth-card">
			<div class="auth-header">
				<h1 class="auth-title">Reset Password</h1>
				<p class="auth-subtitle">Enter your email address and we'll send you a reset link</p>
			</div>

			{#if success}
				<!-- Success message -->
				<div class="success-box">
					<div class="success-icon">✓</div>
					<h2 class="success-title">Check Your Email</h2>
					<p class="success-text">
						If an account exists with <strong>{email}</strong>, you will receive a password reset
						link shortly.
					</p>
					<p class="success-hint">The link will expire in 1 hour.</p>
					<button on:click={() => goto('/auth/login')} class="btn btn-primary btn-block">
						Return to Login
					</button>
				</div>
			{:else}
				<!-- Form -->
				<form on:submit|preventDefault={handleSubmit} class="auth-form">
					<div class="form-group">
						<label for="email" class="form-label">Email Address</label>
						<input
							id="email"
							type="email"
							bind:value={email}
							required
							class="form-input"
							placeholder="you@example.com"
							disabled={loading}
						/>
					</div>

					{#if error}
						<div class="error-box">{error}</div>
					{/if}

					<button type="submit" class="btn btn-primary btn-block" disabled={loading}>
						{loading ? 'Sending...' : 'Send Reset Link'}
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
		margin: 0 0 0.75rem 0;
		line-height: 1.6;
	}

	.success-hint {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 2rem 0;
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
