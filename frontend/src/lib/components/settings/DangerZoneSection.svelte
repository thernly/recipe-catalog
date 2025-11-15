<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	function handleDeleteAccount() {
		const confirmation = prompt(
			'Are you absolutely sure? Type "DELETE" to confirm account deletion:'
		);

		if (confirmation !== 'DELETE') {
			return;
		}

		dispatch('delete');
	}
</script>

<div class="settings-section danger-section">
	<h2 class="section-title danger-title">Danger Zone</h2>
	<p class="section-description">Irreversible and destructive actions</p>

	<div class="danger-card">
		<div class="danger-info">
			<h3 class="danger-card-title">Delete Account</h3>
			<p class="danger-card-description">
				Permanently delete your account and all associated data. This action cannot be undone.
			</p>
		</div>
		<button on:click={handleDeleteAccount} class="btn btn-danger"> Delete Account </button>
	</div>
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

	.danger-section .section-title {
		color: var(--error-700);
	}

	.danger-card {
		padding: 1.5rem;
		background: var(--error-50);
		border: 2px solid var(--error-200);
		border-radius: var(--radius-lg);
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
	}

	.danger-card-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--error-900);
		margin: 0 0 0.25rem 0;
	}

	.danger-card-description {
		font-size: 0.875rem;
		color: var(--error-700);
		margin: 0;
	}

	.btn-danger {
		padding: 0.75rem 1.5rem;
		background: var(--error-600);
		color: var(--neutral-white);
		border: none;
		border-radius: var(--radius-md);
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
		white-space: nowrap;
	}

	.btn-danger:hover {
		background: var(--error-700);
		box-shadow: var(--shadow-md);
	}

	@media (max-width: 1024px) {
		.danger-card {
			flex-direction: column;
			text-align: center;
		}
	}
</style>
