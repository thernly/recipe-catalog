<script lang="ts">
	import { onDestroy } from 'svelte';
	import { toast } from '#lib/stores/toast.js';
	import { formatCountdown } from '#lib/utils/step-timers.js';

	/** How long to count down, the words from the step, and the step's number */
	export let seconds: number;
	export let label: string;
	export let step: number;

	// ponytail: the timer lives in this page only; a reload or leaving the
	// recipe ends it. Keep the end time in storage if that turns out to matter.
	let endsAt: number | null = null;
	let remaining = 0;
	let done = false;
	let ticker: ReturnType<typeof setInterval> | undefined;
	let audio: AudioContext | undefined;

	function start() {
		// Made on the tap: browsers only play sound that a tap set up
		try {
			audio ??= new AudioContext();
		} catch {
			// no sound here: the timer still counts, buzzes and shows a message
		}
		done = false;
		remaining = seconds;
		endsAt = Date.now() + seconds * 1000;
		// From the clock, not by counting ticks: a background tab ticks slowly
		ticker = setInterval(tick, 500);
	}

	function tick() {
		if (endsAt === null) return;
		remaining = Math.max(0, Math.ceil((endsAt - Date.now()) / 1000));
		if (remaining === 0) finish();
	}

	function stop() {
		clearInterval(ticker);
		endsAt = null;
		done = false;
	}

	function finish() {
		stop();
		done = true;
		beep();
		navigator.vibrate?.([300, 150, 300]);
		toast.info(`Timer done: step ${step} (${label})`);
	}

	function beep() {
		if (!audio) return;
		for (const at of [0, 0.4, 0.8]) {
			const tone = audio.createOscillator();
			tone.frequency.value = 880;
			tone.connect(audio.destination);
			tone.start(audio.currentTime + at);
			tone.stop(audio.currentTime + at + 0.25);
		}
	}

	onDestroy(() => {
		clearInterval(ticker);
		void audio?.close();
	});
</script>

{#if endsAt !== null}
	<span class="timer running" role="timer" aria-label="Step {step} timer">
		⏱ {formatCountdown(remaining)}
		<button type="button" on:click={stop} aria-label="Cancel {label} timer">
			Cancel
		</button>
	</span>
{:else}
	<button type="button" class="timer" class:done on:click={start}>
		⏱ {done ? `Time's up · restart ${label}` : `Start ${label} timer`}
	</button>
{/if}

<style>
	.timer {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.25rem 0.75rem;
		border: 1px solid var(--primary-600);
		border-radius: var(--radius-md);
		background: var(--neutral-white);
		color: var(--primary-600);
		font-size: 0.875rem;
		font-weight: 600;
	}

	.timer.running,
	.timer.done {
		background: var(--primary-600);
		color: var(--neutral-white);
		font-variant-numeric: tabular-nums;
	}

	.timer.running button {
		text-decoration: underline;
		color: inherit;
	}
</style>
