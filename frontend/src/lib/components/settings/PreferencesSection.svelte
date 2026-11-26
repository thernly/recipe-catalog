<script lang="ts">
	import { theme } from '#lib/stores/theme.js';
	import type { UserPreferences } from '#lib/api/users.js';
	import { updatePreferences } from '#lib/api/users.js';
	import { createEventDispatcher } from 'svelte';
	import ThemeSwitcher from '#lib/components/ThemeSwitcher.svelte';
	import { toast } from '#lib/stores/toast.js';

	export let preferences: UserPreferences;

	const dispatch = createEventDispatcher();

	let form = { ...preferences };
	let saving = false;
	let success = false;

	const dietaryOptions = [
		'Vegetarian',
		'Vegan',
		'Gluten-Free',
		'Dairy-Free',
		'Nut-Free',
		'Low-Carb',
		'Keto',
		'Paleo',
		'Halal',
		'Kosher',
	];

	function toggleDietary(option: string) {
		if (!form.dietary_preferences) {
			form.dietary_preferences = [];
		}
		if (form.dietary_preferences.includes(option)) {
			form.dietary_preferences = form.dietary_preferences.filter(
				(p) => p !== option,
			);
		} else {
			form.dietary_preferences = [...form.dietary_preferences, option];
		}
	}

	async function savePreferences() {
		saving = true;
		success = false;

		try {
			const updated = await updatePreferences(form);
			dispatch('update', updated);
			success = true;

			// Apply theme change
			theme.set(form.theme);

			setTimeout(() => (success = false), 3000);
		} catch (err) {
			toast.error(
				'Failed to update preferences: ' +
					(err instanceof Error ? err.message : 'Unknown error'),
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
		<!-- Default view, default sort, recipes per page and email notifications are
		     stored by the server but used nowhere, so they are not offered here. -->
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

		<fieldset class="form-group" aria-describedby="dietary-preferences-help">
			<legend class="form-label">Dietary Preferences</legend>
			<p
				id="dietary-preferences-help"
				class="text-sm mb-2"
				style="color: var(--text-600);"
			>
				Select your dietary preferences to personalize AI-generated menu
				suggestions
			</p>
			<div class="dietary-options">
				{#each dietaryOptions as option (option)}
					<button
						type="button"
						on:click={() => toggleDietary(option)}
						aria-pressed={form.dietary_preferences?.includes(option) ?? false}
						class="dietary-option {form.dietary_preferences?.includes(option)
							? 'active'
							: ''}"
					>
						{option}
					</button>
				{/each}
			</div>
		</fieldset>

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

	.settings-form fieldset {
		border: 0;
		padding: 0;
		margin: 0;
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
		color: var(--color-success-text);
		font-size: 0.875rem;
		font-weight: 500;
	}

	.dietary-options {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 0.5rem;
	}

	.dietary-option {
		padding: 0.5rem 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
		color: var(--text-700);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.dietary-option:hover {
		background: var(--neutral-50);
		border-color: var(--accent-300);
	}

	.dietary-option.active {
		background: var(--color-btn-primary-bg);
		color: var(--color-btn-primary-text);
		border-color: var(--color-btn-primary-bg);
	}
</style>
