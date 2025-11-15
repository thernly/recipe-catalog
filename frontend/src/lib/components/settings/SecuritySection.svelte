<script lang="ts">
	import { changePassword } from '$lib/api/users';

	let passwordForm = {
		current_password: '',
		new_password: '',
		confirm_password: ''
	};
	let saving = false;
	let success = false;
	let error = '';

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
</style>
