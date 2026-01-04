<script lang="ts">
	export let loading = false;
	export let disabled = false;
	export let type: 'button' | 'submit' = 'button';
	export let variant: 'primary' | 'secondary' | 'danger' = 'primary';
</script>

<button
	{type}
	disabled={loading || disabled}
	class={`btn btn-${variant} ${$$props.class || ''}`}
	class:loading
	on:click
>
	{#if loading}
		<span class="spinner"></span>
	{/if}
	<slot />
</button>

<style>
	.btn {
		position: relative;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		font-family: var(--font-ui);
		transition: all var(--transition-base);
	}

	.btn:hover:not(:disabled):not(.loading) {
		transform: translateY(-1px);
	}

	.btn:active:not(:disabled):not(.loading) {
		transform: translateY(0) scale(0.98);
	}

	.btn-primary:hover:not(:disabled):not(.loading) {
		box-shadow: var(--shadow-warm-glow);
	}

	.btn.loading {
		pointer-events: none;
		opacity: 0.7;
	}

	.spinner {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		border: 2px solid currentColor;
		border-right-color: transparent;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
