<script lang="ts">
	import type { UserPreferences } from '$lib/api/users';
	import { updatePreferences } from '$lib/api/users';
	import { createEventDispatcher } from 'svelte';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';

	export let preferences: UserPreferences;

	const dispatch = createEventDispatcher();

	let form = { ...preferences };
	let saving = false;
	let success = false;

	async function savePreferences() {
		saving = true;
		success = false;

		try {
			const updated = await updatePreferences(form);
			dispatch('update', updated);
			success = true;

			// Apply theme change
			document.documentElement.setAttribute('data-theme', form.theme);

			setTimeout(() => (success = false), 3000);
		} catch (err) {
			alert(
				'Failed to update preferences: ' + (err instanceof Error ? err.message : 'Unknown error')
			);
			console.error('Failed to update preferences:', err);
		} finally {
			saving = false;
		}
	}

	function handleThemeChange(e: CustomEvent) {
		form.theme = e.detail;
		savePreferences();
	}
</script>

<div class="settings-section">
	<h2 class="section-title">Preferences</h2>
	<p class="section-description">Customize your experience</p>

	<!-- Theme Switcher -->
	<div class="preference-group">
		<ThemeSwitcher currentTheme={form.theme} on:change={handleThemeChange} />
	</div>

	<!-- Other Preferences -->
	<form on:submit|preventDefault={savePreferences} class="settings-form">
		<div class="form-group">
			<label for="default_view" class="form-label">Default View</label>
			<select id="default_view" bind:value={form.default_view} class="form-input">
				<option value="grid">Grid</option>
				<option value="list">List</option>
			</select>
		</div>

		<div class="form-group">
			<label for="default_sort" class="form-label">Default Sort</label>
			<select id="default_sort" bind:value={form.default_sort} class="form-input">
				<option value="recently_added">Recently Added</option>
				<option value="alphabetical">A-Z</option>
				<option value="time_asc">Shortest Time</option>
				<option value="time_desc">Longest Time</option>
			</select>
		</div>

		<div class="form-group">
			<label for="recipes_per_page" class="form-label">Recipes Per Page</label>
			<input
				id="recipes_per_page"
				type="number"
				min="12"
				max="100"
				step="12"
				bind:value={form.recipes_per_page}
				class="form-input"
			/>
		</div>

		<div class="form-group">
			<label for="timezone" class="form-label">Timezone</label>
			<input
				id="timezone"
				type="text"
				bind:value={form.timezone}
				class="form-input"
				placeholder="UTC"
			/>
		</div>

		<div class="form-group">
			<label class="checkbox-label">
				<input
					type="checkbox"
					bind:checked={form.email_notifications}
					class="form-checkbox"
				/>
				<span>Enable email notifications</span>
			</label>
		</div>

		<div class="form-actions">
			<button type="submit" class="btn btn-primary" disabled={saving}>
				{saving ? 'Saving...' : 'Save Preferences'}
			</button>
			{#if success}
				<span class="success-message">✓ Preferences saved!</span>
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

	.preference-group {
		margin-bottom: 2rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid var(--neutral-200);
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

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		color: var(--text-700);
	}

	.form-checkbox {
		width: 1.25rem;
		height: 1.25rem;
		cursor: pointer;
		accent-color: var(--accent-500);
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
