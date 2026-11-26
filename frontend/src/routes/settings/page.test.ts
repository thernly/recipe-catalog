/**
 * Tests for the settings page: the open section lives in the page address
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";

vi.mock("$app/navigation", () => ({ goto: vi.fn() }));
vi.mock("#lib/api/users.js", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getCurrentUser: vi
    .fn()
    .mockResolvedValue({ id: 1, email: "sam@example.com" }),
  getPreferences: vi.fn().mockResolvedValue({ theme: "garden-fresh" }),
  getUserStats: vi.fn().mockResolvedValue({}),
  deleteAccount: vi.fn(),
}));

import Page from "./+page.svelte";

describe("settings page", () => {
  beforeEach(() => {
    location.hash = "";
  });

  it("opens the section named in the address", async () => {
    location.hash = "#danger";
    const { findByRole } = render(Page);

    expect(await findByRole("heading", { name: "Danger Zone" })).toBeTruthy();
  });

  it("puts the chosen section in the address, and follows Back", async () => {
    const { findByRole } = render(Page);

    await fireEvent.click(await findByRole("button", { name: "Danger Zone" }));
    expect(location.hash).toBe("#danger");
    await findByRole("heading", { name: "Danger Zone" });

    // Back: the address changes underneath the page
    location.hash = "#profile";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    expect(
      (await findByRole("button", { name: "Profile" })).getAttribute(
        "aria-current",
      ),
    ).toBe("true");
  });

  it("falls back to Profile for an unknown section", async () => {
    location.hash = "#nonsense";
    const { findByRole } = render(Page);

    expect(
      (await findByRole("button", { name: "Profile" })).getAttribute(
        "aria-current",
      ),
    ).toBe("true");
  });
});
