<script lang="ts">
	import type { User } from '$lib/api/users';
	import { updateProfile } from '$lib/api/users';
	import { createEventDispatcher } from 'svelte';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';

	export let user: User;

	const dispatch = createEventDispatcher();

	let profileForm = {
		email: user.email,
		display_name: user.display_name
	};
	let saving = false;
	let success = false;

	async function saveProfile() {
		saving = true;
		success = false;

		try {
			const updated = await updateProfile({
				email: profileForm.email,
				display_name: profileForm.display_name
			});
			dispatch('update', updated);
			success = true;
			setTimeout(() => (success = false), 3000);
		} catch (err) {
			toast.error('Failed to update profile: ' + (err instanceof Error ? err.message : 'Unknown error'));
			console.error('Failed to update profile:', err);
		} finally {
			saving = false;
		}
	}
</script>

<div class="settings-section">
	<h2 class="section-title">Profile Information</h2>
	<p class="section-description">Update your account details</p>

	<form on:submit|preventDefault={saveProfile} class="settings-form">
		<div class="form-group">
			<label for="email" class="form-label">Email</label>
			<input
				id="email"
				type="email"
				bind:value={profileForm.email}
				required
				class="form-input"
			/>
		</div>

		<div class="form-group">
			<label for="display_name" class="form-label">Display Name</label>
			<input
				id="display_name"
				type="text"
				bind:value={profileForm.display_name}
				required
				class="form-input"
			/>
		</div>

		<div class="form-actions">
			<button type="submit" class="btn btn-primary" disabled={saving}>
				{saving ? 'Saving...' : 'Save Changes'}
			</button>
			{#if success}
				<span class="success-message">✓ Profile updated successfully!</span>
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
