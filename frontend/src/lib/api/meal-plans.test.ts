/**
 * Week-start dates are sent to the server as the local calendar date.
 */
import { describe, it, expect, afterEach } from "vitest";
import { formatDateISO, getWeekStart } from "./meal-plans";

const originalTZ = process.env.TZ;

describe("meal plan week dates", () => {
  afterEach(() => {
    process.env.TZ = originalTZ;
  });

  it("keeps Monday as Monday east of UTC", () => {
    process.env.TZ = "Australia/Sydney";
    // Wednesday 25 Nov 2026, 08:00 in Sydney is still Tuesday in UTC.
    const weekStart = getWeekStart(new Date(2026, 10, 25, 8, 0));
    expect(formatDateISO(weekStart)).toBe("2026-11-23");
  });

  it("keeps Monday as Monday west of UTC", () => {
    process.env.TZ = "America/Los_Angeles";
    // That week's Monday at 21:00 in Los Angeles is already Tuesday in UTC.
    const weekStart = getWeekStart(new Date(2026, 10, 29, 21, 0));
    expect(formatDateISO(weekStart)).toBe("2026-11-23");
  });
});
