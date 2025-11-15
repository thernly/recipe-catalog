<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		getCurrentUser,
		updateProfile,
		changePassword,
		getPreferences,
		updatePreferences,
		getUserStats,
		deleteAccount,
		type User,
		type UserPreferences,
		type UserStats
	} from '$lib/api/users';
	import { auth } from '$lib/stores/auth';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';

	let user: User | null = null;
	let preferences: UserPreferences | null = null;
	let stats: UserStats | null = null;
	let loading = true;
	let error: string | null = null;

	// Active section
	let activeSection: 'profile' | 'preferences' | 'security' | 'stats' | 'danger' = 'profile';

	// Profile form
	let profileForm = {
		email: '',
		display_name: ''
	};
	let profileSaving = false;
	let profileSuccess = false;

	// Password form
	let passwordForm = {
		current_password: '',
		new_password: '',
		confirm_password: ''
	};
	let passwordSaving = false;
	let passwordSuccess = false;
	let passwordError = '';

	// Preferences form
	let preferencesForm = {
		theme: 'classic' as 'classic' | 'professional',
		default_view: 'grid' as 'grid' | 'list',
		default_sort: 'recently_added',
		recipes_per_page: 24,
		email_notifications: true,
		timezone: 'UTC'
	};
	let preferencesSaving = false;
	let preferencesSuccess = false;

	// Load user data
	async function loadUserData() {
		loading = true;
		error = null;

		try {
			const [userData, prefsData, statsData] = await Promise.all([
				getCurrentUser(),
				getPreferences(),
				getUserStats()
			]);

			user = userData;
			preferences = prefsData;
			stats = statsData;

			// Populate forms
			profileForm.email = user.email;
			profileForm.display_name = user.display_name;

			preferencesForm = { ...prefsData };

			// Apply current theme
			document.documentElement.setAttribute('data-theme', prefsData.theme);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load user data';
			console.error('Failed to load user data:', err);
		} finally {
			loading = false;
		}
	}

	// Save profile
	async function saveProfile() {
		profileSaving = true;
		profileSuccess = false;

		try {
			user = await updateProfile({
				email: profileForm.email,
				display_name: profileForm.display_name
			});
			profileSuccess = true;
			setTimeout(() => (profileSuccess = false), 3000);
		} catch (err) {
			alert('Failed to update profile: ' + (err instanceof Error ? err.message : 'Unknown error'));
			console.error('Failed to update profile:', err);
		} finally {
			profileSaving = false;
		}
	}

	// Change password
	async function savePassword() {
		passwordError = '';
		passwordSuccess = false;

		// Validation
		if (passwordForm.new_password !== passwordForm.confirm_password) {
			passwordError = 'New passwords do not match';
			return;
		}

		if (passwordForm.new_password.length < 8) {
			passwordError = 'Password must be at least 8 characters';
			return;
		}

		passwordSaving = true;

		try {
			await changePassword({
				current_password: passwordForm.current_password,
				new_password: passwordForm.new_password
			});

			passwordSuccess = true;
			passwordForm = {
				current_password: '',
				new_password: '',
				confirm_password: ''
			};
			setTimeout(() => (passwordSuccess = false), 3000);
		} catch (err) {
			passwordError = err instanceof Error ? err.message : 'Failed to change password';
			console.error('Failed to change password:', err);
		} finally {
			passwordSaving = false;
		}
	}

	// Save preferences
	async function savePreferences() {
		preferencesSaving = true;
		preferencesSuccess = false;

		try {
			preferences = await updatePreferences(preferencesForm);
			preferencesSuccess = true;

			// Apply theme change
			document.documentElement.setAttribute('data-theme', preferencesForm.theme);

			setTimeout(() => (preferencesSuccess = false), 3000);
		} catch (err) {
			alert(
				'Failed to update preferences: ' + (err instanceof Error ? err.message : 'Unknown error')
			);
			console.error('Failed to update preferences:', err);
		} finally {
			preferencesSaving = false;
		}
	}

	// Handle theme change
	function handleThemeChange(e: CustomEvent) {
		preferencesForm.theme = e.detail;
		savePreferences();
	}

	// Delete account
	async function handleDeleteAccount() {
		const confirmation = prompt(
			'Are you absolutely sure? Type "DELETE" to confirm account deletion:'
		);

		if (confirmation !== 'DELETE') {
			return;
		}

		try {
			await deleteAccount();
			auth.logout();
			goto('/auth/login');
		} catch (err) {
			alert('Failed to delete account: ' + (err instanceof Error ? err.message : 'Unknown error'));
			console.error('Failed to delete account:', err);
		}
	}

	onMount(() => {
		loadUserData();
	});
</script>

<svelte:head>
	<title>Settings - Recipe Catalog</title>
</svelte:head>

<div class="min-h-screen bg-neutral-50">
	<div class="container-custom py-8">
		<h1 class="text-4xl font-bold mb-8" style="color: var(--text-900);">Settings</h1>

		{#if loading}
			<!-- Loading state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⏳</div>
				<p class="text-lg" style="color: var(--text-600);">Loading settings...</p>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="text-center py-16">
				<div class="text-4xl mb-4">⚠️</div>
				<p class="text-lg mb-2" style="color: var(--text-900);">Failed to load settings</p>
				<p class="text-sm mb-4" style="color: var(--text-600);">{error}</p>
				<button on:click={loadUserData} class="btn btn-primary">Try Again</button>
			</div>
		{:else if user && preferences && stats}
			<!-- Settings layout -->
			<div class="settings-layout">
				<!-- Sidebar navigation -->
				<aside class="settings-sidebar">
					<button
						class="sidebar-link"
						class:active={activeSection === 'profile'}
						on:click={() => (activeSection = 'profile')}
					>
						👤 Profile
					</button>
					<button
						class="sidebar-link"
						class:active={activeSection === 'preferences'}
						on:click={() => (activeSection = 'preferences')}
					>
						🎨 Preferences
					</button>
					<button
						class="sidebar-link"
						class:active={activeSection === 'security'}
						on:click={() => (activeSection = 'security')}
					>
						🔒 Security
					</button>
					<button
						class="sidebar-link"
						class:active={activeSection === 'stats'}
						on:click={() => (activeSection = 'stats')}
					>
						📊 Statistics
					</button>
					<button
						class="sidebar-link danger"
						class:active={activeSection === 'danger'}
						on:click={() => (activeSection = 'danger')}
					>
						⚠️ Danger Zone
					</button>
				</aside>

				<!-- Main content -->
				<div class="settings-content">
					<!-- Profile Section -->
					{#if activeSection === 'profile'}
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
									<button type="submit" class="btn btn-primary" disabled={profileSaving}>
										{profileSaving ? 'Saving...' : 'Save Changes'}
									</button>
									{#if profileSuccess}
										<span class="success-message">✓ Profile updated successfully!</span>
									{/if}
								</div>
							</form>
						</div>
					{/if}

					<!-- Preferences Section -->
					{#if activeSection === 'preferences'}
						<div class="settings-section">
							<h2 class="section-title">Preferences</h2>
							<p class="section-description">Customize your experience</p>

							<!-- Theme Switcher -->
							<div class="preference-group">
								<ThemeSwitcher
									currentTheme={preferencesForm.theme}
									on:change={handleThemeChange}
								/>
							</div>

							<!-- Other Preferences -->
							<form on:submit|preventDefault={savePreferences} class="settings-form">
								<div class="form-group">
									<label for="default_view" class="form-label">Default View</label>
									<select id="default_view" bind:value={preferencesForm.default_view} class="form-input">
										<option value="grid">Grid</option>
										<option value="list">List</option>
									</select>
								</div>

								<div class="form-group">
									<label for="default_sort" class="form-label">Default Sort</label>
									<select id="default_sort" bind:value={preferencesForm.default_sort} class="form-input">
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
										bind:value={preferencesForm.recipes_per_page}
										class="form-input"
									/>
								</div>

								<div class="form-group">
									<label for="timezone" class="form-label">Timezone</label>
									<input
										id="timezone"
										type="text"
										bind:value={preferencesForm.timezone}
										class="form-input"
										placeholder="UTC"
									/>
								</div>

								<div class="form-group">
									<label class="checkbox-label">
										<input
											type="checkbox"
											bind:checked={preferencesForm.email_notifications}
											class="form-checkbox"
										/>
										<span>Enable email notifications</span>
									</label>
								</div>

								<div class="form-actions">
									<button type="submit" class="btn btn-primary" disabled={preferencesSaving}>
										{preferencesSaving ? 'Saving...' : 'Save Preferences'}
									</button>
									{#if preferencesSuccess}
										<span class="success-message">✓ Preferences saved!</span>
									{/if}
								</div>
							</form>
						</div>
					{/if}

					<!-- Security Section -->
					{#if activeSection === 'security'}
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

								{#if passwordError}
									<div class="error-message">{passwordError}</div>
								{/if}

								<div class="form-actions">
									<button type="submit" class="btn btn-primary" disabled={passwordSaving}>
										{passwordSaving ? 'Changing...' : 'Change Password'}
									</button>
									{#if passwordSuccess}
										<span class="success-message">✓ Password changed successfully!</span>
									{/if}
								</div>
							</form>
						</div>
					{/if}

					<!-- Statistics Section -->
					{#if activeSection === 'stats'}
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
					{/if}

					<!-- Danger Zone Section -->
					{#if activeSection === 'danger'}
						<div class="settings-section danger-section">
							<h2 class="section-title danger-title">Danger Zone</h2>
							<p class="section-description">Irreversible and destructive actions</p>

							<div class="danger-card">
								<div class="danger-info">
									<h3 class="danger-card-title">Delete Account</h3>
									<p class="danger-card-description">
										Permanently delete your account and all associated data. This action cannot be
										undone.
									</p>
								</div>
								<button on:click={handleDeleteAccount} class="btn btn-danger"> Delete Account </button>
							</div>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.settings-layout {
		display: grid;
		grid-template-columns: 250px 1fr;
		gap: 2rem;
		align-items: start;
	}

	.settings-sidebar {
		position: sticky;
		top: 2rem;
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.sidebar-link {
		padding: 0.75rem 1rem;
		text-align: left;
		background: transparent;
		border: none;
		border-radius: var(--radius-md);
		color: var(--text-700);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.sidebar-link:hover {
		background: var(--neutral-100);
		color: var(--text-900);
	}

	.sidebar-link.active {
		background: var(--accent-50);
		color: var(--accent-700);
		font-weight: 600;
	}

	.sidebar-link.danger {
		color: var(--error-600);
	}

	.sidebar-link.danger:hover {
		background: var(--error-50);
		color: var(--error-700);
	}

	.settings-content {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 2rem;
	}

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

	.error-message {
		padding: 0.75rem;
		background: var(--error-50);
		border: 1px solid var(--error-200);
		border-radius: var(--radius-md);
		color: var(--error-700);
		font-size: 0.875rem;
	}

	.preference-group {
		margin-bottom: 2rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid var(--neutral-200);
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
		.settings-layout {
			grid-template-columns: 1fr;
		}

		.settings-sidebar {
			position: static;
			flex-direction: row;
			overflow-x: auto;
		}

		.stats-grid {
			grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		}

		.danger-card {
			flex-direction: column;
			text-align: center;
		}
	}
</style>
