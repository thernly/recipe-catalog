<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getCurrentHousehold,
		getHouseholdMembers,
		getHouseholdInvitations,
		updateHousehold,
		removeMember,
		createInvitation,
		revokeInvitation,
		type Household,
		type HouseholdMember,
		type HouseholdInvitation
	} from '$lib/api/households';
	import { auth } from '$lib/stores/auth';
	import { get } from 'svelte/store';

	let household: Household | null = null;
	let members: HouseholdMember[] = [];
	let invitations: HouseholdInvitation[] = [];
	let loading = true;
	let error = '';
	let success = '';

	let editingName = false;
	let newName = '';
	let updatingName = false;

	let inviteeEmail = '';
	let sendingInvitation = false;

	let removingMemberId: number | null = null;
	let revokingInvitationId: number | null = null;

	const currentUser = get(auth).user;
	const isOwner = () => household && currentUser && household.owner_user_id === currentUser.id;

	async function loadHouseholdData() {
		loading = true;
		error = '';
		try {
			household = await getCurrentHousehold();
			newName = household.name;

			// Load members and invitations in parallel
			[members, invitations] = await Promise.all([
				getHouseholdMembers(household.id),
				getHouseholdInvitations(household.id)
			]);
		} catch (err) {
			console.error('Failed to load household data:', err);
			error = err instanceof Error ? err.message : 'Failed to load household data';
		} finally {
			loading = false;
		}
	}

	async function handleUpdateName() {
		if (!household || !newName.trim()) return;

		updatingName = true;
		error = '';
		success = '';

		try {
			household = await updateHousehold(household.id, { name: newName.trim() });
			editingName = false;
			success = 'Household name updated successfully';
			setTimeout(() => (success = ''), 3000);
		} catch (err) {
			console.error('Failed to update household name:', err);
			error = err instanceof Error ? err.message : 'Failed to update household name';
		} finally {
			updatingName = false;
		}
	}

	async function handleSendInvitation() {
		if (!household || !inviteeEmail.trim()) return;

		sendingInvitation = true;
		error = '';
		success = '';

		try {
			await createInvitation(household.id, { invitee_email: inviteeEmail.trim() });
			inviteeEmail = '';
			success = 'Invitation sent successfully';
			setTimeout(() => (success = ''), 3000);

			// Reload invitations
			invitations = await getHouseholdInvitations(household.id);
		} catch (err) {
			console.error('Failed to send invitation:', err);
			error = err instanceof Error ? err.message : 'Failed to send invitation';
		} finally {
			sendingInvitation = false;
		}
	}

	async function handleRemoveMember(userId: number, username: string) {
		if (!household) return;

		if (!confirm(`Remove ${username} from your household?`)) {
			return;
		}

		removingMemberId = userId;
		error = '';

		try {
			await removeMember(household.id, userId);
			success = 'Member removed successfully';
			setTimeout(() => (success = ''), 3000);

			// Reload members
			members = await getHouseholdMembers(household.id);
		} catch (err) {
			console.error('Failed to remove member:', err);
			error = err instanceof Error ? err.message : 'Failed to remove member';
		} finally {
			removingMemberId = null;
		}
	}

	async function handleRevokeInvitation(invitationId: number, email: string) {
		if (!household) return;

		if (!confirm(`Revoke invitation for ${email}?`)) {
			return;
		}

		revokingInvitationId = invitationId;
		error = '';

		try {
			await revokeInvitation(household.id, invitationId);
			success = 'Invitation revoked successfully';
			setTimeout(() => (success = ''), 3000);

			// Reload invitations
			invitations = await getHouseholdInvitations(household.id);
		} catch (err) {
			console.error('Failed to revoke invitation:', err);
			error = err instanceof Error ? err.message : 'Failed to revoke invitation';
		} finally {
			revokingInvitationId = null;
		}
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString();
	}

	function isExpired(expiresAt: string): boolean {
		return new Date(expiresAt) < new Date();
	}

	onMount(() => {
		loadHouseholdData();
	});
</script>

<div class="settings-section">
	<h2 class="section-title">Household</h2>
	<p class="section-description">Manage your household members and share recipes with your family</p>

	{#if loading}
		<p class="text-sm" style="color: var(--text-500);">Loading...</p>
	{:else if household}
		<!-- Household Name -->
		<div class="subsection">
			<h3 class="subsection-title">Household Name</h3>
			{#if editingName && isOwner()}
				<form on:submit|preventDefault={handleUpdateName} class="edit-name-form">
					<input
						type="text"
						bind:value={newName}
						class="form-input"
						placeholder="Household name"
						required
					/>
					<div class="button-group">
						<button type="submit" class="btn btn-primary btn-sm" disabled={updatingName}>
							{updatingName ? 'Saving...' : 'Save'}
						</button>
						<button
							type="button"
							class="btn btn-outline btn-sm"
							on:click={() => {
								editingName = false;
								newName = household?.name || '';
							}}
						>
							Cancel
						</button>
					</div>
				</form>
			{:else}
				<div class="name-display">
					<p class="household-name">{household.name}</p>
					{#if isOwner()}
						<button class="btn btn-outline btn-sm" on:click={() => (editingName = true)}>
							Edit
						</button>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Members -->
		<div class="subsection">
			<h3 class="subsection-title">
				Members ({members.length}/{household.max_members})
			</h3>
			<div class="member-list">
				{#each members as member}
					<div class="member-item">
						<div class="member-info">
							<h4 class="member-name">
								{member.user_display_name || 'Unknown'}
								{#if member.role === 'owner'}
									<span class="badge badge-primary">Owner</span>
								{/if}
								{#if member.user_id === currentUser?.id}
									<span class="badge badge-secondary">You</span>
								{/if}
							</h4>
							<p class="member-email">{member.user_email || ''}</p>
							<p class="member-meta">Joined {formatDate(member.joined_at)}</p>
						</div>
						{#if isOwner() && member.role !== 'owner' && member.user_id !== currentUser?.id}
							<button
								type="button"
								class="btn btn-danger btn-sm"
								on:click={() =>
									handleRemoveMember(member.user_id, member.user_display_name || 'user')}
								disabled={removingMemberId === member.user_id}
							>
								{removingMemberId === member.user_id ? 'Removing...' : 'Remove'}
							</button>
						{/if}
					</div>
				{/each}
			</div>
		</div>

		<!-- Invite Member -->
		{#if isOwner() && members.length < household.max_members}
			<div class="subsection">
				<h3 class="subsection-title">Invite Member</h3>
				<form on:submit|preventDefault={handleSendInvitation} class="invite-form">
					<input
						type="email"
						bind:value={inviteeEmail}
						class="form-input"
						placeholder="Email address"
						required
					/>
					<button type="submit" class="btn btn-primary" disabled={sendingInvitation}>
						{sendingInvitation ? 'Sending...' : 'Send Invitation'}
					</button>
				</form>
			</div>
		{/if}

		<!-- Pending Invitations -->
		{#if isOwner() && invitations.length > 0}
			<div class="subsection">
				<h3 class="subsection-title">Pending Invitations</h3>
				<div class="invitation-list">
					{#each invitations as invitation}
						{@const expired = isExpired(invitation.expires_at)}
						<div class="invitation-item" class:expired>
							<div class="invitation-info">
								<p class="invitation-email">{invitation.invitee_email}</p>
								<p class="invitation-meta">
									Sent {formatDate(invitation.created_at)}
									{#if expired}
										<span class="text-error">· Expired</span>
									{:else}
										· Expires {formatDate(invitation.expires_at)}
									{/if}
								</p>
							</div>
							<button
								type="button"
								class="btn btn-outline btn-sm"
								on:click={() => handleRevokeInvitation(invitation.id, invitation.invitee_email)}
								disabled={revokingInvitationId === invitation.id}
							>
								{revokingInvitationId === invitation.id ? 'Revoking...' : 'Revoke'}
							</button>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if error}
			<div class="error-message">{error}</div>
		{/if}

		{#if success}
			<div class="success-message">✓ {success}</div>
		{/if}
	{/if}
</div>

<style>
	.settings-section {
		max-width: 700px;
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

	.subsection {
		margin-bottom: 2rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid var(--neutral-200);
	}

	.subsection:last-child {
		border-bottom: none;
	}

	.subsection-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 1rem 0;
	}

	.name-display {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.household-name {
		font-size: 1.125rem;
		font-weight: 500;
		color: var(--text-900);
		margin: 0;
	}

	.edit-name-form {
		display: flex;
		gap: 0.75rem;
		align-items: start;
		flex-wrap: wrap;
	}

	.button-group {
		display: flex;
		gap: 0.5rem;
	}

	.form-input {
		flex: 1;
		min-width: 250px;
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

	.member-list,
	.invitation-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.member-item,
	.invitation-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
	}

	.invitation-item.expired {
		opacity: 0.6;
		background: var(--neutral-50);
	}

	.member-info,
	.invitation-info {
		flex: 1;
	}

	.member-name {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-900);
		margin: 0 0 0.25rem 0;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.member-email,
	.invitation-email {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0 0 0.25rem 0;
	}

	.member-meta,
	.invitation-meta {
		font-size: 0.75rem;
		color: var(--text-500);
		margin: 0;
	}

	.badge {
		display: inline-block;
		padding: 0.125rem 0.5rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
	}

	.badge-primary {
		background: var(--accent-100);
		color: var(--accent-700);
	}

	.badge-secondary {
		background: var(--neutral-200);
		color: var(--text-700);
	}

	.invite-form {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.error-message {
		padding: 0.75rem;
		background: var(--error-50);
		border: 1px solid var(--error-200);
		border-radius: var(--radius-md);
		color: var(--error-700);
		font-size: 0.875rem;
		margin-top: 1rem;
	}

	.success-message {
		padding: 0.75rem;
		background: var(--success-50, #d4edda);
		border: 1px solid var(--success-200, #c3e6cb);
		border-radius: var(--radius-md);
		color: var(--success-700, #155724);
		font-size: 0.875rem;
		margin-top: 1rem;
	}

	.text-error {
		color: var(--error-600);
		font-weight: 500;
	}

	.btn-outline {
		background: white;
		border: 1px solid var(--neutral-300);
		color: var(--text-900);
	}

	.btn-outline:hover:not(:disabled) {
		background: var(--neutral-50);
		border-color: var(--neutral-400);
	}

	.btn-danger {
		background: var(--error-600, #dc3545);
		color: white;
		border: none;
	}

	.btn-danger:hover:not(:disabled) {
		background: var(--error-700, #c82333);
	}

	.btn-danger:disabled,
	.btn-outline:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}
</style>
