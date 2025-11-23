<script lang="ts">
	import { changePassword } from '$lib/api/users';
	import {
		getLinkedProviders,
		unlinkProvider,
		initiateOAuthFlow,
		type LinkedProvider
	} from '$lib/api/oauth';
	import { auth } from '$lib/stores/auth';
	import { onMount } from 'svelte';

	let passwordForm = {
		current_password: '',
		new_password: '',
		confirm_password: ''
	};
	let saving = false;
	let success = false;
	let error = '';

	let linkedProviders: LinkedProvider[] = [];
	let loadingProviders = true;
	let providerError = '';
	let removingProvider: number | null = null;
	let hasPassword = false;

	async function savePassword() {
		error = '';
		success = false;

		// Validation
		if (passwordForm.new_password !== passwordForm.confirm_password) {
			error = 'New passwords do not match';
			return;
		}

		if (passwordForm.new_password.length < 8) {
			error = 'Password must be at least 8 characters';
			return;
		}

		saving = true;

		try {
			await changePassword({
				current_password: passwordForm.current_password,
				new_password: passwordForm.new_password
			});

			success = true;
			hasPassword = true;
			passwordForm = {
				current_password: '',
				new_password: '',
				confirm_password: ''
			};
			setTimeout(() => (success = false), 3000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to change password';
			console.error('Failed to change password:', err);
		} finally {
			saving = false;
		}
	}

	async function loadProviders() {
		loadingProviders = true;
		providerError = '';
		try {
			linkedProviders = await getLinkedProviders();
		} catch (err) {
			console.error('Failed to load providers:', err);
			providerError = 'Failed to load linked providers';
		} finally {
			loadingProviders = false;
		}
	}

	async function handleUnlinkProvider(providerId: number, providerName: string) {
		if (!hasPassword && linkedProviders.length <= 1) {
			providerError = 'Cannot remove last authentication method. Please set a password first.';
			return;
		}

		if (!confirm(`Remove ${providerName} from your account?`)) {
			return;
		}

		removingProvider = providerId;
		providerError = '';

		try {
			await unlinkProvider(providerId);
			await loadProviders();
		} catch (err) {
			console.error('Failed to unlink provider:', err);
			providerError =
				err instanceof Error ? err.message : 'Failed to remove provider. Please try again.';
		} finally {
			removingProvider = null;
		}
	}

	function handleLinkProvider(provider: string) {
		providerError = '';
		initiateOAuthFlow(provider);
	}

	function getProviderDisplayName(provider: string): string {
		switch (provider) {
			case 'google':
				return 'Google';
			case 'microsoft':
				return 'Microsoft';
			case 'github':
				return 'GitHub';
			default:
				return provider;
		}
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString();
	}

	onMount(async () => {
		// Assume user has password by default (will handle errors gracefully in password change form)
		// The backend will check if password exists when user attempts to change it
		hasPassword = true;

		await loadProviders();
	});
</script>

<div class="settings-section">
	<h2 class="section-title">Change Password</h2>
	<p class="section-description">Keep your account secure</p>

	<form on:submit|preventDefault={savePassword} class="settings-form">
		<div class="form-group">
			<label for="current_password" class="form-label">Current Password</label>
			<input
				id="current_password"
				type="password"
				bind:value={passwordForm.current_password}
				required
				class="form-input"
			/>
		</div>

		<div class="form-group">
			<label for="new_password" class="form-label">New Password</label>
			<input
				id="new_password"
				type="password"
				bind:value={passwordForm.new_password}
				required
				minlength="8"
				class="form-input"
			/>
			<p class="form-hint">Minimum 8 characters</p>
		</div>

		<div class="form-group">
			<label for="confirm_password" class="form-label">Confirm New Password</label>
			<input
				id="confirm_password"
				type="password"
				bind:value={passwordForm.confirm_password}
				required
				class="form-input"
			/>
		</div>

		{#if error}
			<div class="error-message">{error}</div>
		{/if}

		<div class="form-actions">
			<button type="submit" class="btn btn-primary" disabled={saving}>
				{saving ? 'Changing...' : 'Change Password'}
			</button>
			{#if success}
				<span class="success-message">✓ Password changed successfully!</span>
			{/if}
		</div>
	</form>
</div>

<!-- Linked Identity Providers Section -->
<div class="settings-section mt-8">
	<h2 class="section-title">Linked Accounts</h2>
	<p class="section-description">
		Manage identity providers linked to your account
		{#if !hasPassword && linkedProviders.length > 0}
			<span class="text-warning">(Passwordless account)</span>
		{/if}
	</p>

	{#if loadingProviders}
		<p class="text-sm" style="color: var(--text-500);">Loading...</p>
	{:else if linkedProviders.length > 0}
		<div class="provider-list">
			{#each linkedProviders as provider}
				<div class="provider-item">
					<div class="provider-info">
						<h3 class="provider-name">{getProviderDisplayName(provider.provider_name)}</h3>
						<p class="provider-email">{provider.email_at_provider}</p>
						<p class="provider-meta">
							Added {formatDate(provider.created_at)}
							{#if provider.last_used_at}
								· Last used {formatDate(provider.last_used_at)}
							{/if}
						</p>
					</div>
					<button
						type="button"
						class="btn btn-danger btn-sm"
						on:click={() =>
							handleUnlinkProvider(provider.id, getProviderDisplayName(provider.provider_name))}
						disabled={removingProvider === provider.id}
					>
						{removingProvider === provider.id ? 'Removing...' : 'Remove'}
					</button>
				</div>
			{/each}
		</div>
	{:else}
		<p class="text-sm" style="color: var(--text-500);">No identity providers linked</p>
	{/if}

	{#if providerError}
		<div class="error-message mt-4">{providerError}</div>
	{/if}

	<div class="mt-4">
		<p class="text-sm mb-2" style="color: var(--text-700); font-weight: 500;">
			Link a new provider:
		</p>
		<div class="provider-buttons">
			<button
				type="button"
				class="btn btn-outline"
				on:click={() => handleLinkProvider('google')}
			>
				Link Google
			</button>
			<button
				type="button"
				class="btn btn-outline"
				on:click={() => handleLinkProvider('microsoft')}
			>
				Link Microsoft
			</button>
			<button
				type="button"
				class="btn btn-outline"
				on:click={() => handleLinkProvider('github')}
			>
				Link GitHub
			</button>
		</div>
	</div>

	{#if !hasPassword && linkedProviders.length > 0}
		<div class="warning-box mt-4">
			<strong>Note:</strong> You cannot remove your last authentication method. Please set a password
			below before unlinking all providers.
		</div>
	{/if}
</div>

<style>
	.settings-section {
		max-width: 600px;
	}

	.section-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0 0 0.5rem 0;
	}

	.section-description {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 2rem 0;
	}

	.settings-form {
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
		border: 1px solid var(--neutral-200);
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

	.form-hint {
		font-size: 0.75rem;
		color: var(--text-500);
		margin: 0;
	}

	.error-message {
		padding: 0.75rem;
		background: var(--error-50);
		border: 1px solid var(--error-200);
		border-radius: var(--radius-md);
		color: var(--error-700);
		font-size: 0.875rem;
	}

	.form-actions {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.success-message {
		color: var(--success-600);
		font-size: 0.875rem;
		font-weight: 500;
	}

	.provider-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin-top: 1rem;
	}

	.provider-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
	}

	.provider-info {
		flex: 1;
	}

	.provider-name {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.25rem 0;
	}

	.provider-email {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 0.25rem 0;
	}

	.provider-meta {
		font-size: 0.75rem;
		color: var(--text-500);
		margin: 0;
	}

	.provider-buttons {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.warning-box {
		padding: 0.75rem;
		background: var(--warning-50, #fff3cd);
		border: 1px solid var(--warning-200, #ffc107);
		border-radius: var(--radius-md);
		color: var(--warning-800, #856404);
		font-size: 0.875rem;
	}

	.text-warning {
		color: var(--warning-600, #f59e0b);
		font-weight: 500;
	}

	.mt-4 {
		margin-top: 1rem;
	}

	.mt-8 {
		margin-top: 2rem;
	}

	.mb-2 {
		margin-bottom: 0.5rem;
	}

	.btn-outline {
		background: white;
		border: 1px solid var(--neutral-300);
		color: var(--text-900);
	}

	.btn-outline:hover {
		background: var(--neutral-50);
		border-color: var(--neutral-400);
	}

	.btn-danger {
		background: var(--error-600, #dc3545);
		color: white;
		border: none;
	}

	.btn-danger:hover:not(:disabled) {
		background: var(--error-700, #c82333);
	}

	.btn-danger:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}
</style>
