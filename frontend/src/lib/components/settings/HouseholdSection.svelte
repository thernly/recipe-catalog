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
		createInviteLink,
		joinViaInviteLink,
		leaveHousehold,
		type Household,
		type HouseholdMember,
		type HouseholdInvitation,
		type HouseholdInviteLink
	} from '$lib/api/households';
	import { auth } from '$lib/stores/auth';
	import { get } from 'svelte/store';
	import { dialog } from '$lib/stores/dialog';
	import { toast } from '$lib/stores/toast';

	let household: Household | null = null;
	let members: HouseholdMember[] = [];
	let invitations: HouseholdInvitation[] = [];
	let inviteLink: HouseholdInviteLink | null = null;
	let loading = true;
	let error = '';
	let success = '';

	let editingName = false;
	let newName = '';
	let updatingName = false;

	let inviteeEmail = '';
	let sendingInvitation = false;

	let creatingInviteLink = false;
	let inviteLinkExpiryDays = 7;
	let codeCopied = false;
	let linkCopied = false;

	let joiningCode = '';
	let joiningHousehold = false;

	let removingMemberId: number | null = null;
	let revokingInvitationId: number | null = null;

	const currentUser = get(auth).user;
	const isOwner = () => household && currentUser && household.owner_user_id === currentUser.id;

	async function loadHouseholdData() {
		loading = true;
		error = '';
		household = null;
		
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
			// Don't set error if user just isn't in a household yet
			const errorMessage = err instanceof Error ? err.message : '';
			if (!errorMessage.includes('not found') && !errorMessage.includes('No household')) {
				error = errorMessage || 'Failed to load household data';
			}
			// household stays null, which will show the join form
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
		const householdId = household.id;

		dialog.show({
			title: 'Remove Member',
			message: `Remove ${username} from your household?`,
			onConfirm: async () => {
				removingMemberId = userId;
				error = '';

				try {
					await removeMember(householdId, userId);
					success = 'Member removed successfully';
					toast.success('Member removed successfully');
					setTimeout(() => (success = ''), 3000);

					// Reload members
					members = await getHouseholdMembers(householdId);
				} catch (err) {
					console.error('Failed to remove member:', err);
					error = err instanceof Error ? err.message : 'Failed to remove member';
					toast.error('Failed to remove member');
				} finally {
					removingMemberId = null;
				}
			}
		});
	}

	async function handleRevokeInvitation(invitationId: number, email: string) {
		if (!household) return;
		const householdId = household.id;

		dialog.show({
			title: 'Revoke Invitation',
			message: `Revoke invitation for ${email}?`,
			onConfirm: async () => {
				revokingInvitationId = invitationId;
				error = '';
				success = '';

				try {
					await revokeInvitation(householdId, invitationId);
					success = 'Invitation revoked successfully';
					toast.success('Invitation revoked successfully');
					setTimeout(() => (success = ''), 3000);

					// Reload invitations
					invitations = await getHouseholdInvitations(householdId);
				} catch (err) {
					console.error('Failed to revoke invitation:', err);
					error = err instanceof Error ? err.message : 'Failed to revoke invitation';
					toast.error('Failed to revoke invitation');
				} finally {
					revokingInvitationId = null;
				}
			}
		});
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString();
	}

	function isExpired(expiresAt: string): boolean {
		return new Date(expiresAt) < new Date();
	}

	function isInviteLinkExpired(): boolean {
		if (!inviteLink) return false;
		return isExpired(inviteLink.expires_at);
	}

	function isInviteLinkUsed(): boolean {
		return inviteLink?.used_at !== null;
	}

	async function handleCreateInviteLink() {
		if (!household) return;

		creatingInviteLink = true;
		error = '';
		success = '';

		try {
			inviteLink = await createInviteLink(household.id, {
				expires_in_days: inviteLinkExpiryDays
			});
			success = 'Invite link created! Share the code or link with someone to join your household.';
			setTimeout(() => (success = ''), 5000);
		} catch (err) {
			console.error('Failed to create invite link:', err);
			error = err instanceof Error ? err.message : 'Failed to create invite link';
		} finally {
			creatingInviteLink = false;
		}
	}

	async function handleCopyInviteCode() {
		if (!inviteLink) return;

		try {
			await navigator.clipboard.writeText(inviteLink.code);
			codeCopied = true;
			success = 'Invite code copied to clipboard!';
			setTimeout(() => {
				codeCopied = false;
				success = '';
			}, 3000);
		} catch (err) {
			console.error('Failed to copy to clipboard:', err);
			error = 'Failed to copy to clipboard';
		}
	}

	async function handleCopyInviteLink() {
		if (!inviteLink) return;

		const link = `${window.location.origin}/join/${inviteLink.code}`;
		try {
			await navigator.clipboard.writeText(link);
			linkCopied = true;
			success = 'Invite link copied to clipboard!';
			setTimeout(() => {
				linkCopied = false;
				success = '';
			}, 3000);
		} catch (err) {
			console.error('Failed to copy to clipboard:', err);
			error = 'Failed to copy to clipboard';
		}
	}

	async function handleJoinViaCode() {
		if (!joiningCode.trim()) return;

		// Warn if already in a household
		if (household) {
			const confirmMsg = `You are currently in "${household.name}". Joining a new household will automatically remove you from your current household. Continue?`;
			dialog.show({
				title: 'Join New Household',
				message: confirmMsg,
				onConfirm: async () => {
					await joinViaCode();
				}
			});
		} else {
			await joinViaCode();
		}
	}

	async function joinViaCode() {
		joiningHousehold = true;
		error = '';
		success = '';

		try {
			// If already in a household, leave it first
			if (household) {
				await leaveHousehold();
			}

			await joinViaInviteLink(joiningCode.trim());
			success = 'Successfully joined household! Reloading...';
			toast.success('Successfully joined household!');
			joiningCode = '';

			// Reload household data
			setTimeout(() => {
				loadHouseholdData();
			}, 1000);
		} catch (err) {
			console.error('Failed to join household:', err);
			error = err instanceof Error ? err.message : 'Failed to join household';
			toast.error('Failed to join household');
		} finally {
			joiningHousehold = false;
		}
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
				<h3 class="subsection-title">Invite by Email</h3>
				<p class="subsection-description">Send an invitation to a specific email address</p>
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

			<!-- Invite Link -->
			<div class="subsection">
				<h3 class="subsection-title">Invite Link (One-Time Code)</h3>
				<p class="subsection-description">
					Generate a shareable code that anyone can use to join your household (one-time use)
				</p>

				{#if inviteLink && !isInviteLinkUsed() && !isInviteLinkExpired()}
					<div class="invite-link-display">
						<div class="invite-link-info">
							<p class="invite-code-label">Invite Code:</p>
							<div class="invite-code-box">
								<code class="invite-code">{inviteLink.code}</code>
								<button
									type="button"
									class="btn btn-sm"
									class:btn-success={codeCopied}
									class:btn-outline={!codeCopied}
									on:click={handleCopyInviteCode}
								>
									{codeCopied ? '✓ Copied!' : 'Copy Code'}
								</button>
							</div>
							<p class="invite-link-meta">
								Expires {formatDate(inviteLink.expires_at)}
							</p>
							<p class="invite-link-instructions">
								Share this code with someone to join your household. They can enter it on the
								join page.
							</p>
							<button
								type="button"
								class="btn btn-sm"
								class:btn-success={linkCopied}
								class:btn-outline={!linkCopied}
								on:click={handleCopyInviteLink}
							>
								{linkCopied ? '✓ Link Copied!' : 'Copy Full Link'}
							</button>
						</div>
					</div>
				{:else if inviteLink && isInviteLinkUsed()}
					<p class="text-muted">Your previous invite link has been used.</p>
					<button
						type="button"
						class="btn btn-primary"
						on:click={handleCreateInviteLink}
						disabled={creatingInviteLink}
					>
						{creatingInviteLink ? 'Creating...' : 'Create New Invite Link'}
					</button>
				{:else if inviteLink && isInviteLinkExpired()}
					<p class="text-muted">Your previous invite link has expired.</p>
					<button
						type="button"
						class="btn btn-primary"
						on:click={handleCreateInviteLink}
						disabled={creatingInviteLink}
					>
						{creatingInviteLink ? 'Creating...' : 'Create New Invite Link'}
					</button>
				{:else}
					<div class="create-link-form">
						<label class="form-label">
							Link expires in:
							<select bind:value={inviteLinkExpiryDays} class="form-select">
								<option value={1}>1 day</option>
								<option value={7}>7 days (recommended)</option>
								<option value={14}>14 days</option>
								<option value={30}>30 days</option>
							</select>
						</label>
						<button
							type="button"
							class="btn btn-primary"
							on:click={handleCreateInviteLink}
							disabled={creatingInviteLink}
						>
							{creatingInviteLink ? 'Creating...' : 'Generate Invite Link'}
						</button>
					</div>
				{/if}
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

		<!-- Join a Different Household -->
		<div class="subsection">
			<h3 class="subsection-title">Join a Different Household</h3>
			<p class="subsection-description">
				{#if household}
					Enter an invite code to switch to a different household. You will automatically leave your current household.
				{:else}
					Enter an invite code to join an existing household.
				{/if}
			</p>

			<form on:submit|preventDefault={handleJoinViaCode} class="join-form">
				<div class="form-group">
					<label for="join-code" class="form-label">Invite Code</label>
					<input
						id="join-code"
						type="text"
						bind:value={joiningCode}
						class="form-input"
						placeholder="e.g., happy-ocean-river"
						required
					/>
					<p class="form-help">
						Enter the invite code shared with you (three words separated by hyphens)
					</p>
				</div>
				<button type="submit" class="btn btn-primary" disabled={joiningHousehold}>
					{joiningHousehold ? 'Joining...' : household ? 'Switch Household' : 'Join Household'}
				</button>
			</form>
		</div>

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

	.subsection-description {
		font-size: 0.875rem;
		color: var(--text-600);
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

	.create-link-form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.form-label {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-700);
	}

	.form-select {
		padding: 0.5rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		color: var(--text-900);
		background: var(--neutral-white);
		cursor: pointer;
	}

	.form-select:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.invite-link-display {
		padding: 1rem;
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
	}

	.invite-link-info {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.invite-code-label {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-700);
		margin: 0;
	}

	.invite-code-box {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem;
		background: var(--neutral-white);
		border: 2px solid var(--accent-200);
		border-radius: var(--radius-md);
	}

	.invite-code {
		flex: 1;
		font-family: 'Courier New', monospace;
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--accent-700);
		background: transparent;
		padding: 0;
	}

	.invite-link-meta {
		font-size: 0.75rem;
		color: var(--text-500);
		margin: 0;
	}

	.invite-link-instructions {
		font-size: 0.875rem;
		color: var(--text-600);
		margin: 0;
		padding-top: 0.5rem;
		border-top: 1px solid var(--neutral-200);
	}

	.text-muted {
		font-size: 0.875rem;
		color: var(--text-500);
		margin-bottom: 1rem;
	}

	.join-form {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.form-help {
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

	.btn-success {
		background: var(--success-600, #28a745);
		color: white;
		border: none;
	}

	.btn-success:hover:not(:disabled) {
		background: var(--success-700, #218838);
	}

	.btn-danger:disabled,
	.btn-outline:disabled,
	.btn-success:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}
</style>
