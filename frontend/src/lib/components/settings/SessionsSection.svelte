<script lang="ts">
	import { onMount } from 'svelte';
	import {
		listSessions,
		revokeSession,
		describeUserAgent,
		type Session,
	} from '#lib/api/sessions.js';
	import { dialog } from '#lib/stores/dialog.js';
	import { toast } from '#lib/stores/toast.js';

	let sessions: Session[] = [];
	let loading = true;
	let loadError = '';
	let revokingId: number | null = null;

	async function loadSessions() {
		loading = true;
		loadError = '';
		try {
			sessions = await listSessions();
		} catch (err) {
			console.error('Failed to load sessions:', err);
			loadError = 'Failed to load sessions';
		} finally {
			loading = false;
		}
	}

	function handleRevoke(session: Session) {
		const label = describeUserAgent(session.user_agent);
		dialog.show({
			title: 'Sign Out Session',
			confirmLabel: 'Sign out',
			message: `Sign out ${label}? It will be asked to log in again shortly.`,
			onConfirm: async () => {
				revokingId = session.id;
				try {
					await revokeSession(session.id);
					toast.success(`${label} signed out`);
					await loadSessions();
				} catch (err) {
					console.error('Failed to revoke session:', err);
					toast.error('Failed to sign out session');
				} finally {
					revokingId = null;
				}
			},
		});
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleString();
	}

	onMount(loadSessions);
</script>

<div class="settings-section">
	<h2 class="section-title">Active Sessions</h2>
	<p class="section-description">
		Browsers where you are signed in. Sign out any you don't recognise. Changing
		your password signs out every other session.
	</p>

	{#if loading}
		<p class="text-sm" style="color: var(--text-500);">Loading...</p>
	{:else if loadError}
		<div class="error-message">{loadError}</div>
	{:else if sessions.length === 0}
		<p class="text-sm" style="color: var(--text-500);">No active sessions</p>
	{:else}
		<ul class="session-list">
			{#each sessions as session (session.id)}
				<li class="session-item">
					<div class="session-info">
						<p class="session-name">
							{describeUserAgent(session.user_agent)}
							{#if session.current}
								<span class="current-badge">This device</span>
							{/if}
						</p>
						<p class="session-meta">
							Last active {formatDate(session.last_active_at)}
						</p>
					</div>
					{#if !session.current}
						<button
							type="button"
							class="btn btn-danger btn-sm"
							on:click={() => handleRevoke(session)}
							disabled={revokingId === session.id}
						>
							{revokingId === session.id ? 'Signing out...' : 'Sign out'}
						</button>
					{/if}
				</li>
			{/each}
		</ul>
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

	.session-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.session-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
	}

	.session-info {
		flex: 1;
		min-width: 0;
	}

	.session-name {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.25rem 0;
	}

	.current-badge {
		margin-left: 0.5rem;
		padding: 0.125rem 0.5rem;
		border-radius: var(--radius-sm);
		background: var(--accent-100);
		color: var(--accent-700);
		font-size: 0.75rem;
		font-weight: 600;
	}

	.session-meta {
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

	.btn-danger {
		background: var(--error-600);
		color: #ffffff;
		border: none;
	}

	.btn-danger:hover:not(:disabled) {
		background: var(--error-600);
		filter: brightness(0.9);
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
