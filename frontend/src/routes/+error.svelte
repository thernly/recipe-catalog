<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { AlertTriangle, Home, RefreshCw, ArrowLeft, Search } from 'lucide-svelte';

	$: status = $page.status;
	$: message = $page.error?.message || 'Something went wrong';

	function getErrorInfo(status: number) {
		switch (status) {
			case 404:
				return {
					title: 'Page Not Found',
					description: "The page you're looking for doesn't exist or has been moved.",
					icon: Search
				};
			case 403:
				return {
					title: 'Access Denied',
					description: "You don't have permission to access this page.",
					icon: AlertTriangle
				};
			case 500:
				return {
					title: 'Server Error',
					description: 'Something went wrong on our end. Please try again later.',
					icon: AlertTriangle
				};
			default:
				return {
					title: 'Oops!',
					description: message,
					icon: AlertTriangle
				};
		}
	}

	$: errorInfo = getErrorInfo(status);

	function handleRetry() {
		window.location.reload();
	}

	function handleGoBack() {
		window.history.back();
	}
</script>

<svelte:head>
	<title>{errorInfo.title} - Recipe Catalog</title>
</svelte:head>

<div class="error-page">
	<div class="error-container">
		<!-- Decorative background -->
		<div class="error-background">
			<div class="error-code">{status}</div>
		</div>

		<!-- Error icon -->
		<div class="error-icon">
			<svelte:component this={errorInfo.icon} size={48} />
		</div>

		<!-- Error content -->
		<h1 class="error-title">{errorInfo.title}</h1>
		<p class="error-description">{errorInfo.description}</p>

		<!-- Action buttons -->
		<div class="error-actions">
			<button on:click={handleRetry} class="btn btn-primary">
				<RefreshCw size={18} />
				<span>Try Again</span>
			</button>
			<button on:click={handleGoBack} class="btn btn-secondary">
				<ArrowLeft size={18} />
				<span>Go Back</span>
			</button>
			<button on:click={() => goto('/dashboard')} class="btn btn-secondary">
				<Home size={18} />
				<span>Home</span>
			</button>
		</div>

		<!-- Help text -->
		<p class="error-help">
			If the problem persists, try refreshing the page or contact support.
		</p>
	</div>
</div>

<style>
	.error-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		background: var(--neutral-50);
	}

	.error-container {
		text-align: center;
		max-width: 480px;
		position: relative;
	}

	.error-background {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -60%);
		pointer-events: none;
		z-index: 0;
	}

	.error-code {
		font-size: 12rem;
		font-weight: 800;
		color: var(--neutral-100);
		line-height: 1;
		user-select: none;
	}

	.error-icon {
		position: relative;
		z-index: 1;
		width: 5rem;
		height: 5rem;
		margin: 0 auto 1.5rem;
		background: var(--accent-100);
		border-radius: var(--radius-full);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--accent-600);
	}

	.error-title {
		position: relative;
		z-index: 1;
		font-size: 2rem;
		font-weight: 700;
		color: var(--text-900);
		margin: 0 0 0.75rem;
	}

	.error-description {
		position: relative;
		z-index: 1;
		font-size: 1.125rem;
		color: var(--text-600);
		margin: 0 0 2rem;
		line-height: 1.6;
	}

	.error-actions {
		position: relative;
		z-index: 1;
		display: flex;
		gap: 0.75rem;
		justify-content: center;
		flex-wrap: wrap;
		margin-bottom: 2rem;
	}

	.error-actions .btn {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
	}

	.btn-secondary {
		background: var(--neutral-white);
		color: var(--text-700);
		border: 1px solid var(--neutral-300);
	}

	.btn-secondary:hover {
		background: var(--neutral-100);
		border-color: var(--neutral-400);
	}

	.error-help {
		position: relative;
		z-index: 1;
		font-size: 0.875rem;
		color: var(--text-500);
	}

	@media (max-width: 480px) {
		.error-code {
			font-size: 8rem;
		}

		.error-actions {
			flex-direction: column;
		}

		.error-actions .btn {
			width: 100%;
			justify-content: center;
		}
	}
</style>
