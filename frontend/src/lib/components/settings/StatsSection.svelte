<script lang="ts">
	import type { UserStats, User } from '$lib/api/users';

	export let stats: UserStats;
	export let user: User;
</script>

<div class="settings-section">
	<h2 class="section-title">Your Statistics</h2>
	<p class="section-description">Overview of your recipe collection</p>

	<div class="stats-grid">
		<div class="stat-card">
			<div class="stat-icon">📖</div>
			<div class="stat-value">{stats.total_recipes}</div>
			<div class="stat-label">Total Recipes</div>
		</div>

		<div class="stat-card">
			<div class="stat-icon">📚</div>
			<div class="stat-value">{stats.total_collections}</div>
			<div class="stat-label">Collections</div>
		</div>

		<div class="stat-card">
			<div class="stat-icon">📥</div>
			<div class="stat-value">{stats.recipes_imported}</div>
			<div class="stat-label">Imported</div>
		</div>

		<div class="stat-card">
			<div class="stat-icon">✍️</div>
			<div class="stat-value">{stats.recipes_manual}</div>
			<div class="stat-label">Manual Entry</div>
		</div>

		<div class="stat-card">
			<div class="stat-icon">📅</div>
			<div class="stat-value">{stats.recipes_this_month}</div>
			<div class="stat-label">This Month</div>
		</div>

		<div class="stat-card">
			<div class="stat-icon">👤</div>
			<div class="stat-value">{user.display_name}</div>
			<div class="stat-label">Member Since {new Date(user.created_at).getFullYear()}</div>
		</div>
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

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
	}

	.stat-card {
		padding: 1.5rem;
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		text-align: center;
	}

	.stat-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.stat-value {
		font-size: 2rem;
		font-weight: 700;
		color: var(--text-900);
		margin-bottom: 0.25rem;
	}

	.stat-label {
		font-size: 0.75rem;
		color: var(--text-600);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	@media (max-width: 1024px) {
		.stats-grid {
			grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		}
	}
</style>
