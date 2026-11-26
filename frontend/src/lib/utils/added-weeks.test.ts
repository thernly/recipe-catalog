import { beforeEach, describe, expect, it } from "vitest";
import { rememberAddedToList, wasAddedToList } from "./added-weeks.js";

describe("added-weeks", () => {
  beforeEach(() => localStorage.clear());

  it("remembers a meal plan added to a list", () => {
    expect(wasAddedToList(1, 7)).toBe(false);
    rememberAddedToList(1, 7);
    expect(wasAddedToList(1, 7)).toBe(true);
  });

  it("keeps other plans and other lists apart", () => {
    rememberAddedToList(1, 7);
    expect(wasAddedToList(2, 7)).toBe(false);
    expect(wasAddedToList(1, 8)).toBe(false);
    expect(wasAddedToList(17, 7)).toBe(false);
  });

  it("starts fresh when the stored value is damaged", () => {
    localStorage.setItem("meal-plans-added-to-lists", "{not json");
    expect(wasAddedToList(1, 7)).toBe(false);
    rememberAddedToList(1, 7);
    expect(wasAddedToList(1, 7)).toBe(true);
  });
});
