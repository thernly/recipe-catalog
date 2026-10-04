<script lang="ts">
	import { onMount } from 'svelte';
	import {
		listApiTokens,
		createApiToken,
		revokeApiToken,
		type ApiToken,
		type CreatedApiToken
	} from '$lib/api/api-tokens';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';

	let tokens: ApiToken[] = [];
	let loading = true;
	let loadError = '';

	let newName = '';
	let creating = false;
	let createError = '';
	let created: CreatedApiToken | null = null;
	let copied = false;

	let revokingId: number | null = null;

	async function loadTokens() {
		loading = true;
		loadError = '';
		try {
			tokens = await listApiTokens();
		} catch (err) {
			console.error('Failed to load API tokens:', err);
			loadError = 'Failed to load API tokens';
		} finally {
			loading = false;
		}
	}

	async function handleCreate() {
		createError = '';
		const name = newName.trim();
		if (!name) {
			createError = 'Give the token a name, such as the browser it is for';
			return;
		}

		creating = true;
		try {
			created = await createApiToken(name);
			copied = false;
			newName = '';
			await loadTokens();
		} catch (err) {
			console.error('Failed to create API token:', err);
			createError = err instanceof Error ? err.message : 'Failed to create API token';
		} finally {
			creating = false;
		}
	}

	async function copyToken() {
		if (!created) return;
		try {
			await navigator.clipboard.writeText(created.token);
			copied = true;
		} catch (err) {
			console.error('Failed to copy token:', err);
			toast.error('Could not copy. Select the token and copy it manually.');
		}
	}

	function dismissCreated() {
		created = null;
		copied = false;
	}

	function handleRevoke(token: ApiToken) {
		dialog.show({
			title: 'Revoke API Token',
			message: `Revoke "${token.name}"? Anything using it will stop working immediately.`,
			onConfirm: async () => {
				revokingId = token.id;
				try {
					await revokeApiToken(token.id);
					if (created?.id === token.id) dismissCreated();
					toast.success(`"${token.name}" revoked`);
					await loadTokens();
				} catch (err) {
					console.error('Failed to revoke API token:', err);
					toast.error('Failed to revoke token');
				} finally {
					revokingId = null;
				}
			}
		});
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString();
	}

	onMount(loadTokens);
</script>

<div class="settings-section">
	<h2 class="section-title">API Tokens</h2>
	<p class="section-description">
		Personal tokens let the Recipe Siphon browser extension send recipes straight to your
		catalog. A token can only import recipes and check that it works; it cannot read or change
		anything else. Create one per browser and revoke it when you stop using that browser.
	</p>

	{#if created}
		<div class="created-box" role="status">
			<p class="created-title">Token "{created.name}" created</p>
			<p class="created-hint">
				Copy it now and paste it into the extension's options. It will not be shown again.
			</p>
			<div class="token-row">
				<input
					class="form-input token-value"
					type="text"
					readonly
					value={created.token}
					aria-label="New API token"
					on:focus={(e) => e.currentTarget.select()}
				/>
				<button type="button" class="btn btn-primary" on:click={copyToken}>
					{copied ? 'Copied' : 'Copy'}
				</button>
			</div>
			<button type="button" class="btn btn-outline btn-sm" on:click={dismissCreated}>
				Done
			</button>
		</div>
	{/if}

	<form on:submit|preventDefault={handleCreate} class="create-form">
		<div class="form-group">
			<label for="api_token_name" class="form-label">Token name</label>
			<div class="token-row">
				<input
					id="api_token_name"
					type="text"
					bind:value={newName}
					maxlength="100"
					placeholder="e.g. Firefox on laptop"
					class="form-input"
				/>
				<button type="submit" class="btn btn-primary" disabled={creating}>
					{creating ? 'Creating...' : 'Create token'}
				</button>
			</div>
		</div>
		{#if createError}
			<div class="error-message">{createError}</div>
		{/if}
	</form>

	<h3 class="list-title">Active tokens</h3>
	{#if loading}
		<p class="text-sm" style="color: var(--text-500);">Loading...</p>
	{:else if loadError}
		<div class="error-message">{loadError}</div>
	{:else if tokens.length === 0}
		<p class="text-sm" style="color: var(--text-500);">No active tokens</p>
	{:else}
		<ul class="token-list">
			{#each tokens as token (token.id)}
				<li class="token-item">
					<div class="token-info">
						<p class="token-name">{token.name}</p>
						<p class="token-meta">
							<code>{token.token_prefix}…</code>
							· Created {formatDate(token.created_at)}
							· {token.last_used_at ? `Last used ${formatDate(token.last_used_at)}` : 'Never used'}
						</p>
					</div>
					<button
						type="button"
						class="btn btn-danger btn-sm"
						on:click={() => handleRevoke(token)}
						disabled={revokingId === token.id}
					>
						{revokingId === token.id ? 'Revoking...' : 'Revoke'}
					</button>
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

	.create-form {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		margin-bottom: 2rem;
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
		flex: 1;
		min-width: 0;
		padding: 0.75rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 1rem;
		color: var(--text-900);
		background: var(--neutral-white);
		transition: all var(--transition-fast);
	}

	.form-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.token-row {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}

	.token-value {
		font-family: monospace;
		font-size: 0.875rem;
	}

	.created-box {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		align-items: flex-start;
		padding: 1rem;
		margin-bottom: 2rem;
		background: var(--accent-50);
		border: 1px solid var(--accent-200);
		border-radius: var(--radius-md);
	}

	.created-box .token-row {
		width: 100%;
	}

	.created-title {
		font-weight: 600;
		color: var(--text-900);
		margin: 0;
	}

	.created-hint {
		font-size: 0.875rem;
		color: var(--text-700);
		margin: 0;
	}

	.list-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.75rem 0;
	}

	.token-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.token-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
	}

	.token-info {
		flex: 1;
		min-width: 0;
	}

	.token-name {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.25rem 0;
		overflow-wrap: anywhere;
	}

	.token-meta {
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

	.btn-outline {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-300);
		color: var(--text-900);
	}

	.btn-outline:hover {
		background: var(--neutral-50);
		border-color: var(--neutral-400);
	}

	.btn-danger {
		background: var(--error-600);
		color: var(--neutral-white);
		border: none;
	}

	.btn-danger:hover:not(:disabled) {
		background: var(--error-700);
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
