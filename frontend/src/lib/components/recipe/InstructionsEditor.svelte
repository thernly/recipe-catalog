<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let instructions: string[] = [''];
	export let error: string = '';

	const dispatch = createEventDispatcher();

	function addInstruction() {
		instructions = [...instructions, ''];
		dispatch('change', instructions);
	}

	function removeInstruction(index: number) {
		instructions = instructions.filter((_, i) => i !== index);
		dispatch('change', instructions);
	}

	function moveInstructionUp(index: number) {
		if (index === 0) return;
		const temp = instructions[index];
		instructions[index] = instructions[index - 1];
		instructions[index - 1] = temp;
		instructions = [...instructions];
		dispatch('change', instructions);
	}

	function moveInstructionDown(index: number) {
		if (index === instructions.length - 1) return;
		const temp = instructions[index];
		instructions[index] = instructions[index + 1];
		instructions[index + 1] = temp;
		instructions = [...instructions];
		dispatch('change', instructions);
	}

	function handleInput() {
		dispatch('change', instructions);
	}
</script>

<section class="form-section">
	<h2 class="section-title required">Instructions</h2>

	{#if error}
		<p class="error-message mb-4">{error}</p>
	{/if}

	<div class="dynamic-list">
		{#each instructions as instruction, index}
			<div class="dynamic-list-item">
				<div class="flex gap-2">
					<span class="item-number">{index + 1}</span>
					<div class="flex flex-col gap-1">
						<button
							type="button"
							on:click={() => moveInstructionUp(index)}
							disabled={index === 0}
							class="btn-reorder"
							title="Move up"
						>
							↑
						</button>
						<button
							type="button"
							on:click={() => moveInstructionDown(index)}
							disabled={index === instructions.length - 1}
							class="btn-reorder"
							title="Move down"
						>
							↓
						</button>
					</div>
				</div>
				<textarea
					bind:value={instructions[index]}
					on:input={handleInput}
					placeholder="Describe this step..."
					rows="2"
					class="form-input flex-1"
				></textarea>
				<button
					type="button"
					on:click={() => removeInstruction(index)}
					class="btn-remove"
					title="Remove"
				>
					×
				</button>
			</div>
		{/each}
	</div>

	<button type="button" on:click={addInstruction} class="btn btn-secondary btn-sm mt-3">
		+ Add Step
	</button>
</section>

<style>
	.form-section {
		background: var(--neutral-white);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-lg);
		padding: 2rem;
		margin-bottom: 2rem;
	}

	.section-title {
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--text-900);
		margin-bottom: 1.5rem;
	}

	.section-title.required::after {
		content: '*';
		color: #ef4444;
		margin-left: 0.25rem;
	}

	.error-message {
		font-size: 0.875rem;
		color: #ef4444;
		margin-top: 0.5rem;
	}

	.mb-4 {
		margin-bottom: 1rem;
	}

	.dynamic-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.dynamic-list-item {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.flex {
		display: flex;
	}

	.flex-col {
		flex-direction: column;
	}

	.gap-1 {
		gap: 0.25rem;
	}

	.gap-2 {
		gap: 0.5rem;
	}

	.item-number {
		flex-shrink: 0;
		width: 2rem;
		height: 2.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-100);
		color: var(--text-600);
		border-radius: var(--radius-md);
		font-size: 0.875rem;
		font-weight: 500;
	}

	.form-input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		font-size: 1rem;
		color: var(--text-900);
		background: var(--neutral-white);
		transition: all var(--transition-fast);
	}

	.form-input:focus {
		outline: none;
		border-color: var(--accent-500);
		box-shadow: 0 0 0 3px var(--accent-100);
	}

	.flex-1 {
		flex: 1;
	}

	.btn-remove {
		flex-shrink: 0;
		width: 2.5rem;
		height: 2.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-50);
		border: 1px solid var(--neutral-200);
		border-radius: var(--radius-md);
		color: var(--text-600);
		font-size: 1.5rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-remove:hover {
		background: #fee2e2;
		border-color: #ef4444;
		color: #ef4444;
	}

	.btn-reorder {
		width: 1.5rem;
		height: 1.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--neutral-100);
		border: 1px solid var(--neutral-200);
		border-radius: 0.25rem;
		color: var(--text-600);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-reorder:hover:not(:disabled) {
		background: var(--accent-50);
		border-color: var(--accent-300);
		color: var(--accent-700);
	}

	.btn-reorder:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}

	.mt-3 {
		margin-top: 0.75rem;
	}

	textarea.form-input {
		resize: vertical;
		min-height: 5rem;
	}
</style>
