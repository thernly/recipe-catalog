<script lang="ts">
	import { auth } from '#lib/stores/auth.js';
	import { resendVerification } from '#lib/api/users.js';
	import { toast } from '#lib/stores/toast.js';

	let sending = false;
	let sent = false;

	// is_verified is missing on an older cached user object; only a definite
	// "false" shows the notice.
	$: user = $auth.user;
	$: unverified = user?.is_verified === false;

	async function resend() {
		if (!user) return;
		sending = true;
		try {
			await resendVerification(user.email);
			sent = true;
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : 'Could not send the email',
			);
		} finally {
			sending = false;
		}
	}
</script>

{#if unverified && user}
	<div
		class="mb-6 p-4 rounded-md flex flex-wrap items-center justify-between gap-3"
		style="background: var(--accent-50); color: var(--accent-800);"
		role="status"
	>
		{#if sent}
			<span>
				Check {user.email} for the verification link. It can take a few minutes.
			</span>
		{:else}
			<span>
				Please confirm your email address. We sent a link to {user.email}.
			</span>
			<button
				type="button"
				class="btn btn-secondary"
				on:click={resend}
				disabled={sending}
			>
				{sending ? 'Sending...' : 'Send it again'}
			</button>
		{/if}
	</div>
{/if}
