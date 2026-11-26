import { describe, expect, it } from "vitest";
import { findDurations, formatCountdown } from "./step-timers.js";

describe("findDurations", () => {
  it.each([
    ["Simmer for 20 minutes.", [["20 minutes", 1200]]],
    ["Bake 20-25 minutes until golden.", [["20-25 minutes", 1200]]],
    ["Cook 3 to 4 mins per side", [["3 to 4 mins", 180]]],
    ["Roast for 1 hour 30 minutes", [["1 hour 30 minutes", 5400]]],
    ["Braise 1 hour and 15 minutes", [["1 hour and 15 minutes", 4500]]],
    ["Rest 1 1/2 hours", [["1 1/2 hours", 5400]]],
    ["Rise for 1½ hours", [["1 1/2 hours", 5400]]],
    ["Stir for 30 seconds", [["30 seconds", 30]]],
    [
      "Boil 10 minutes, then rest 5 minutes",
      [
        ["10 minutes", 600],
        ["5 minutes", 300],
      ],
    ],
    ["Heat the oven to 350 degrees and add 2 eggs", []],
  ])("%s", (step, expected) => {
    expect(findDurations(step).map((d) => [d.label, d.seconds])).toEqual(
      expected,
    );
  });
});

describe("formatCountdown", () => {
  it("shows minutes and seconds, and hours when there are any", () => {
    expect(formatCountdown(75)).toBe("1:15");
    expect(formatCountdown(5)).toBe("0:05");
    expect(formatCountdown(3725)).toBe("1:02:05");
  });
});
