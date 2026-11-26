import { describe, it, expect, beforeEach } from "vitest";
import {
  loadProgress,
  saveProgress,
  PROGRESS_MAX_AGE_MS,
} from "./cooking-progress.js";

const NOTHING = { ingredients: [], steps: [], scale: 1, cookMode: false };

describe("cooking progress", () => {
  beforeEach(() => localStorage.clear());

  it("gives back what was saved for that recipe", () => {
    const progress = {
      ingredients: [0, 2],
      steps: [1],
      scale: 2,
      cookMode: true,
    };
    saveProgress(7, progress);

    expect(loadProgress(7)).toEqual(progress);
    expect(loadProgress(8)).toEqual(NOTHING);
  });

  it("forgets progress from an earlier day's cooking", () => {
    const now = Date.now();
    saveProgress(7, { ...NOTHING, steps: [0] }, now);

    expect(loadProgress(7, now + PROGRESS_MAX_AGE_MS - 1).steps).toEqual([0]);
    expect(loadProgress(7, now + PROGRESS_MAX_AGE_MS + 1)).toEqual(NOTHING);
  });

  it("stores nothing when there is nothing to remember", () => {
    saveProgress(7, { ...NOTHING, steps: [0] });
    saveProgress(7, NOTHING);

    expect(localStorage.length).toBe(0);
  });

  it.each(["not json", "null", '{"savedAt": "x"}', '{"ingredients": "all"}'])(
    "ignores a damaged entry: %s",
    (stored) => {
      localStorage.setItem("recipe-progress-7", stored);

      expect(loadProgress(7)).toEqual(NOTHING);
    },
  );

  it("drops values of the wrong kind from an otherwise good entry", () => {
    localStorage.setItem(
      "recipe-progress-7",
      JSON.stringify({
        savedAt: Date.now(),
        ingredients: [1, "2", null],
        steps: [0],
        scale: "big",
        cookMode: "yes",
      }),
    );

    expect(loadProgress(7)).toEqual({
      ingredients: [1],
      steps: [0],
      scale: 1,
      cookMode: false,
    });
  });
});
