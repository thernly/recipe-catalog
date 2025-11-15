<script lang="ts">
	import { onMount } from 'svelte';
	import { getUserStats } from '$lib/api/users';
	import type { UserStats } from '$lib/api/users';

	let stats: UserStats | null = null;
	let loading = true;
	let error: string | null = null;

	// Export state
	let exporting = false;
	let exportStatus = '';

	const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

	// Export function
	async function exportData(endpoint: string, format: string, filename: string) {
		exporting = true;
		exportStatus = '';

		try {
			// Get auth token
			const token = localStorage.getItem('auth_token');
			if (!token) {
				throw new Error('Not authenticated');
			}

			// Build URL with format parameter
			const url = `${API_URL}/api/export/${endpoint}?format=${format}`;

			// Fetch the export
			const response = await fetch(url, {
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (!response.ok) {
				throw new Error(`Export failed: ${response.statusText}`);
			}

			// Get the blob
			const blob = await response.blob();

			// Create download link
			const downloadUrl = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = downloadUrl;
			a.download = filename;
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(downloadUrl);
			document.body.removeChild(a);

			exportStatus = `✓ Export successful! Download started.`;
			setTimeout(() => (exportStatus = ''), 5000);
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
		await exportData('all', 'json', filename);
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
			<h1 class="text-4xl font-bold" style="color: var(--text-900);">Export Your Data</h1>
			<p class="subtitle">Download your recipes and collections in various formats</p>
		</div>

		{#if loading}
			<!-- Loading state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⏳</div>
				<p class="text-lg" style="color: var(--text-600);">Loading export options...</p>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⚠️</div>
				<p class="text-lg mb-2" style="color: var(--text-900);">Failed to load export options</p>
				<p class="text-sm mb-4" style="color: var(--text-600);">{error}</p>
				<button on:click={loadStats} class="btn btn-primary">Try Again</button>
			</div>
		{:else if stats}
			<!-- Export status message -->
			{#if exportStatus}
				<div class="status-message" class:success={exportStatus.includes('✓')}>
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

			<!-- Export Options -->
			<div class="export-grid">
				<!-- Export Recipes -->
				<div class="export-card">
					<div class="card-header">
						<div class="card-icon">📖</div>
						<div>
							<h2 class="card-title">Export Recipes</h2>
							<p class="card-description">Download all your recipes in your preferred format</p>
						</div>
					</div>

					<div class="card-content">
						<div class="format-section">
							<h3 class="format-title">Available Formats:</h3>

							<button
								on:click={() => exportRecipes('json')}
								disabled={exporting}
								class="format-button"
							>
								<div class="format-info">
									<span class="format-name">📄 JSON</span>
									<span class="format-desc">Complete data, machine-readable</span>
								</div>
								<span class="download-icon">⬇️</span>
							</button>

							<button
								on:click={() => exportRecipes('markdown')}
								disabled={exporting}
								class="format-button"
							>
								<div class="format-info">
									<span class="format-name">📝 Markdown</span>
									<span class="format-desc">Human-readable, formatted text</span>
								</div>
								<span class="download-icon">⬇️</span>
							</button>

							<button
								on:click={() => exportRecipes('text')}
								disabled={exporting}
								class="format-button"
							>
								<div class="format-info">
									<span class="format-name">📃 Plain Text</span>
									<span class="format-desc">Simple, universal format</span>
								</div>
								<span class="download-icon">⬇️</span>
							</button>
						</div>
					</div>
				</div>

				<!-- Export Collections -->
				<div class="export-card">
					<div class="card-header">
						<div class="card-icon">📚</div>
						<div>
							<h2 class="card-title">Export Collections</h2>
							<p class="card-description">Download your collections and their recipes</p>
						</div>
					</div>

					<div class="card-content">
						<div class="format-section">
							<h3 class="format-title">Available Formats:</h3>

							<button
								on:click={() => exportCollections('json')}
								disabled={exporting}
								class="format-button"
							>
								<div class="format-info">
									<span class="format-name">📄 JSON</span>
									<span class="format-desc">Complete collection data</span>
								</div>
								<span class="download-icon">⬇️</span>
							</button>

							<button
								on:click={() => exportCollections('markdown')}
								disabled={exporting}
								class="format-button"
							>
								<div class="format-info">
									<span class="format-name">📝 Markdown</span>
									<span class="format-desc">Formatted collection lists</span>
								</div>
								<span class="download-icon">⬇️</span>
							</button>
						</div>
					</div>
				</div>

				<!-- Complete Backup -->
				<div class="export-card featured">
					<div class="card-header">
						<div class="card-icon">💾</div>
						<div>
							<h2 class="card-title">Complete Backup</h2>
							<p class="card-description">
								Download everything: recipes, collections, and preferences
							</p>
						</div>
					</div>

					<div class="card-content">
						<p class="backup-info">
							This export includes all your data in a single JSON file. Perfect for backups or
							migrating to another instance.
						</p>

						<button on:click={exportAllData} disabled={exporting} class="btn btn-primary btn-large">
							{exporting ? 'Exporting...' : '⬇️ Download Complete Backup'}
						</button>
					</div>
				</div>
			</div>

			<!-- Info Box -->
			<div class="info-box">
				<h3 class="info-title">ℹ️ About Data Exports</h3>
				<ul class="info-list">
					<li>All exports are generated on-demand and include only your data</li>
					<li>Exports do not include images - only image URLs are exported</li>
					<li>JSON exports can be used for backups or data portability</li>
					<li>Markdown and text exports are great for printing or offline reading</li>
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
		padding: 1rem;
		margin-bottom: 1.5rem;
		background: var(--error-50);
		border: 1px solid var(--error-200);
		border-radius: var(--radius-md);
		color: var(--error-700);
		text-align: center;
		font-weight: 500;
	}

	.status-message.success {
		background: var(--success-50);
		border-color: var(--success-200);
		color: var(--success-700);
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

	.export-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.export-card {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
		transition: all var(--transition-fast);
	}

	.export-card.featured {
		border-color: var(--accent-300);
		box-shadow: 0 0 0 2px var(--accent-100);
	}

	.export-card:hover {
		box-shadow: var(--shadow-md);
	}

	.card-header {
		display: flex;
		gap: 1rem;
		margin-bottom: 1.5rem;
		align-items: start;
	}

	.card-icon {
		font-size: 2rem;
	}

	.card-title {
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0 0 0.25rem 0;
	}

	.card-description {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0;
	}

	.card-content {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.format-section {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.format-title {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-700);
		margin: 0 0 0.5rem 0;
	}

	.format-button {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
		text-align: left;
	}

	.format-button:hover:not(:disabled) {
		background: var(--accent-50);
		border-color: var(--accent-300);
		transform: translateY(-1px);
		box-shadow: var(--shadow-sm);
	}

	.format-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.format-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.format-name {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-900);
	}

	.format-desc {
		font-size: 0.75rem;
		color: var(--text-600);
	}

	.download-icon {
		font-size: 1.25rem;
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
