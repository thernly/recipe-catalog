<script lang="ts">
	import { downloadBlob } from '#lib/utils/download.js';
	import { onMount } from 'svelte';
	import { getUserStats } from '#lib/api/users.js';
	import type { UserStats } from '#lib/api/users.js';
	import { apiRequest } from '#lib/api/client.js';
	import { TOAST_DURATION } from '#lib/constants.js';
	import ExportCard from '#lib/components/export/ExportCard.svelte';

	let stats: UserStats | null = null;
	let loading = true;
	let error: string | null = null;

	// Export state
	let exporting = false;
	let exportStatus = '';

	// Load user stats
	async function loadStats() {
		loading = true;
		error = null;

		try {
			stats = await getUserStats();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load statistics';
			console.error('Failed to load stats:', err);
		} finally {
			loading = false;
		}
	}

	// Whose recipes go into "Export Recipes" and "Complete Backup"
	let scope: 'mine' | 'household' = 'mine';

	// Export function
	async function exportData(
		endpoint: string,
		format: string,
		filename: string,
	) {
		exporting = true;
		exportStatus = '';

		try {
			const params = new URLSearchParams();
			if (format) params.set('format', format);
			// Collections are always your own
			if (endpoint !== 'collections') params.set('scope', scope);
			const blob = await apiRequest<Blob>(`/export/${endpoint}?${params}`, {
				responseType: 'blob',
			});

			// Create download link
			downloadBlob(blob, filename);

			exportStatus = `✓ Export successful! Download started.`;
			setTimeout(() => (exportStatus = ''), TOAST_DURATION);
		} catch (err) {
			exportStatus = `✗ Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`;
			console.error('Export failed:', err);
		} finally {
			exporting = false;
		}
	}

	// Export recipes
	async function exportRecipes(format: 'json' | 'markdown' | 'text') {
		const extensions = { json: 'json', markdown: 'md', text: 'txt' };
		const filename = `recipes_export_${new Date().toISOString().split('T')[0]}.${extensions[format]}`;
		await exportData('recipes', format, filename);
	}

	// Export collections
	async function exportCollections(format: 'json' | 'markdown') {
		const extensions = { json: 'json', markdown: 'md' };
		const filename = `collections_export_${new Date().toISOString().split('T')[0]}.${extensions[format]}`;
		await exportData('collections', format, filename);
	}

	// Export all data
	async function exportAllData() {
		const filename = `complete_backup_${new Date().toISOString().split('T')[0]}.json`;
		// The 'all' endpoint doesn't accept a format parameter, so we don't pass it
		await exportData('all', '', filename);
	}

	onMount(() => {
		loadStats();
	});
</script>

<svelte:head>
	<title>Export Data - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	<div class="container-custom py-8">
		<div class="header-section">
			<h1 class="text-4xl font-bold" style="color: var(--text-900);">
				Export Your Data
			</h1>
			<p class="subtitle">
				Download your recipes and collections in various formats
			</p>
		</div>

		{#if loading}
			<!-- Loading state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⏳</div>
				<p class="text-lg" style="color: var(--text-600);">
					Loading export options...
				</p>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⚠️</div>
				<p class="text-lg mb-2" style="color: var(--text-900);">
					Failed to load export options
				</p>
				<p class="text-sm mb-4" style="color: var(--text-600);">{error}</p>
				<button on:click={loadStats} class="btn btn-primary">Try Again</button>
			</div>
		{:else if stats}
			<!-- Export status message -->
			{#if exportStatus}
				<div
					class="status-message"
					class:success={exportStatus.includes('✓')}
					role="status"
				>
					{exportStatus}
				</div>
			{/if}

			<!-- Quick Stats -->
			<div class="stats-overview">
				<div class="stat-box">
					<div class="stat-icon">📖</div>
					<div class="stat-content">
						<div class="stat-value">{stats.total_recipes}</div>
						<div class="stat-label">Total Recipes</div>
					</div>
				</div>
				<div class="stat-box">
					<div class="stat-icon">📚</div>
					<div class="stat-content">
						<div class="stat-value">{stats.total_collections}</div>
						<div class="stat-label">Collections</div>
					</div>
				</div>
			</div>

			<label class="scope-choice">
				<span>Recipes to include</span>
				<select bind:value={scope} disabled={exporting}>
					<option value="mine">Only recipes I added</option>
					<option value="household">Everyone's recipes in my household</option>
				</select>
			</label>

			<!-- Export Options -->
			<div class="export-grid">
				<!-- Export Recipes -->
				<ExportCard
					icon="📖"
					title="Export Recipes"
					description="Download all your recipes in your preferred format"
					{exporting}
					formats={[
						{
							name: 'JSON',
							emoji: '📄',
							desc: 'Complete data, machine-readable',
							value: 'json',
						},
						{
							name: 'Markdown',
							emoji: '📝',
							desc: 'Human-readable, formatted text',
							value: 'markdown',
						},
						{
							name: 'Plain Text',
							emoji: '📃',
							desc: 'Simple, universal format',
							value: 'text',
						},
					]}
					on:export={(e) => exportRecipes(e.detail)}
				/>

				<!-- Export Collections -->
				<ExportCard
					icon="📚"
					title="Export Collections"
					description="Download your collections and their recipes"
					{exporting}
					formats={[
						{
							name: 'JSON',
							emoji: '📄',
							desc: 'Complete collection data',
							value: 'json',
						},
						{
							name: 'Markdown',
							emoji: '📝',
							desc: 'Formatted collection lists',
							value: 'markdown',
						},
					]}
					on:export={(e) => exportCollections(e.detail)}
				/>

				<!-- Complete Backup -->
				<ExportCard
					icon="💾"
					title="Complete Backup"
					description="Download your recipes and collections, plus the household's meal plans and shopping lists"
					{exporting}
					featured={true}
				>
					<p class="backup-info">
						One JSON file you can put back with "Restore a Complete Backup" on
						the <a href="/import" class="underline">Import page</a>.
						{#if scope === 'household'}
							Includes recipes added by other household members. On restore, a
							recipe the household no longer has is added as the restoring
							person's own.
						{:else}
							Recipes added by other household members are not included.
						{/if}
					</p>

					<button
						on:click={exportAllData}
						disabled={exporting}
						class="btn btn-primary btn-large"
					>
						{exporting ? 'Exporting...' : '⬇️ Download Complete Backup'}
					</button>
				</ExportCard>
			</div>

			<!-- Info Box -->
			<div class="info-box">
				<h3 class="info-title">ℹ️ About Data Exports</h3>
				<ul class="info-list">
					<li>
						All exports are generated on-demand. They include only what you
						added, unless you choose everyone's recipes above
					</li>
					<li>
						JSON and Markdown exports include any photo stored with a recipe,
						which can make the file large; text exports list image links only
					</li>
					<li>JSON exports can be used for backups or data portability</li>
					<li>
						Markdown and text exports are great for printing or offline reading
					</li>
					<li>Your data remains private and secure during export</li>
				</ul>
			</div>
		{/if}
	</div>
</div>

<style>
	.header-section {
		margin-bottom: 2rem;
	}

	.subtitle {
		font-size: 1.125rem;
		color: var(--text-600);
		margin-top: 0.5rem;
	}

	.status-message {
		padding: 1rem 1.5rem;
		margin-bottom: 1.5rem;
		background: var(--error-50);
		border: 2px solid var(--error-300);
		border-radius: var(--radius-md);
		color: var(--error-800);
		text-align: center;
		font-weight: 600;
		font-size: 1rem;
		box-shadow: 0 2px 8px rgba(220, 38, 38, 0.1);
	}

	.status-message.success {
		background: var(--success-50);
		border-color: var(--success-300);
		color: var(--success-800);
		box-shadow: 0 2px 8px rgba(34, 197, 94, 0.1);
	}

	.stats-overview {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.stat-box {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.stat-icon {
		font-size: 2.5rem;
	}

	.stat-content {
		flex: 1;
	}

	.stat-value {
		font-size: 2rem;
		font-weight: 700;
		color: var(--text-900);
		line-height: 1;
	}

	.stat-label {
		font-size: 0.875rem;
		color: var(--text-600);
		margin-top: 0.25rem;
	}

	.scope-choice {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
		font-weight: 600;
		color: var(--text-900);
	}

	.scope-choice select {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--neutral-300);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
		color: var(--text-900);
		font-weight: 400;
	}

	.export-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.backup-info {
		font-size: 0.875rem;
		color: var(--text-700);
		line-height: 1.6;
		margin: 0 0 1rem 0;
	}

	.btn-large {
		width: 100%;
		padding: 1rem;
		font-size: 1rem;
	}

	.info-box {
		background: var(--primary-50);
		border: 1px solid var(--primary-200);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
	}

	.info-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 1rem 0;
	}

	.info-list {
		margin: 0;
		padding-left: 1.5rem;
		color: var(--text-700);
		font-size: 0.875rem;
		line-height: 1.8;
	}

	.info-list li {
		margin-bottom: 0.5rem;
	}

	@media (max-width: 768px) {
		.export-grid {
			grid-template-columns: 1fr;
		}

		.stats-overview {
			grid-template-columns: 1fr;
		}
	}
</style>
