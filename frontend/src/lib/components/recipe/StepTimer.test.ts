import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";
import { get } from "svelte/store";

import StepTimer from "./StepTimer.svelte";
import { toasts } from "#lib/stores/toast.js";

const props = { seconds: 90, label: "90 seconds", step: 3 };

describe("StepTimer", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("counts down from the step's time and says when it is up", async () => {
    const { getByRole, findByRole } = render(StepTimer, props);

    await fireEvent.click(
      getByRole("button", { name: /Start 90 seconds timer/ }),
    );
    expect(getByRole("timer").textContent).toContain("1:30");

    await vi.advanceTimersByTimeAsync(30_000);
    expect(getByRole("timer").textContent).toContain("1:00");

    await vi.advanceTimersByTimeAsync(60_000);
    expect(await findByRole("button", { name: /Time's up/ })).toBeTruthy();
    expect(get(toasts).map((t) => t.message)).toContain(
      "Timer done: step 3 (90 seconds)",
    );
  });

  it("can be cancelled", async () => {
    const { getByRole, queryByRole } = render(StepTimer, props);

    await fireEvent.click(getByRole("button", { name: /Start/ }));
    await fireEvent.click(
      getByRole("button", { name: "Cancel 90 seconds timer" }),
    );
    await vi.advanceTimersByTimeAsync(120_000);

    expect(queryByRole("timer")).toBeNull();
    expect(
      getByRole("button", { name: /Start 90 seconds timer/ }),
    ).toBeTruthy();
  });
});
