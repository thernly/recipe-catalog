import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { get } from "svelte/store";
import { toast } from "./toast.js";
import { TOAST_DURATION } from "#lib/constants.js";

const messages = () => get(toast).map((t) => t.message);

describe("toast store", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    for (const t of get(toast)) toast.remove(t.id);
    vi.useRealTimers();
  });

  it("removes a success message by itself", () => {
    toast.success("Saved");
    vi.advanceTimersByTime(TOAST_DURATION);
    expect(messages()).toEqual([]);
  });

  it("keeps an error until it is closed", () => {
    toast.error("Could not save");
    vi.advanceTimersByTime(TOAST_DURATION * 10);
    expect(messages()).toEqual(["Could not save"]);

    toast.remove(get(toast)[0].id);
    expect(messages()).toEqual([]);
  });

  it("does not stack the same error twice", () => {
    toast.error("Could not save");
    toast.error("Could not save");
    expect(messages()).toEqual(["Could not save"]);
  });
});
