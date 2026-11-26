/** A time mentioned in a recipe step, e.g. "simmer for 20 minutes". */
export interface StepDuration {
  /** The words as written: "20 minutes", "1 hour 30 minutes", "20-25 minutes" */
  label: string;
  seconds: number;
}

const UNIT_SECONDS: Record<string, number> = { h: 3600, m: 60, s: 1 };
const UNIT = "hours?|hrs?|minutes?|mins?|seconds?|secs?";
// amount, optional range end ("20-25", "20 to 25"), unit, optional smaller
// part ("1 hour 30 minutes", "1 hour and 15 minutes")
const DURATION = new RegExp(
  String.raw`(\d+\s+\d\/\d|\d\/\d|\d+(?:\.\d+)?)(?:\s*(?:-|–|to)\s*\d+(?:\.\d+)?)?\s*(${UNIT})\b` +
    String.raw`(?:,?\s*(?:and\s+)?(\d+)\s*(${UNIT})\b)?`,
  "gi",
);

function toNumber(text: string): number {
  // "1 1/2" -> 1.5, "1/2" -> 0.5, "20" -> 20
  return text
    .trim()
    .split(/\s+/)
    .reduce((sum, part) => {
      const [top, bottom] = part.split("/");
      return sum + (bottom ? Number(top) / Number(bottom) : Number(top));
    }, 0);
}

/**
 * Every time mentioned in a step, in order. A range ("20-25 minutes") counts
 * as its lower end, so the timer says when to start checking.
 */
export function findDurations(step: string): StepDuration[] {
  const text = step
    .replace(/½/g, " 1/2")
    .replace(/¼/g, " 1/4")
    .replace(/¾/g, " 3/4");
  return [...text.matchAll(DURATION)]
    .map((match) => {
      const [whole, amount, unit, extraAmount, extraUnit] = match;
      let seconds = toNumber(amount) * UNIT_SECONDS[unit[0].toLowerCase()];
      if (extraAmount)
        seconds +=
          Number(extraAmount) * UNIT_SECONDS[extraUnit[0].toLowerCase()];
      return {
        label: whole.trim().replace(/\s+/g, " "),
        seconds: Math.round(seconds),
      };
    })
    .filter((duration) => duration.seconds > 0);
}

/** 75 -> "1:15", 3725 -> "1:02:05" */
export function formatCountdown(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return hours
    ? `${hours}:${String(minutes).padStart(2, "0")}:${seconds}`
    : `${minutes}:${seconds}`;
}
