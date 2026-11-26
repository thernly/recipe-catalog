/**
 * The navbar's menu button, which holds the links on narrow screens.
 */
import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";

vi.mock("$app/navigation", () => ({ goto: vi.fn(), afterNavigate: vi.fn() }));
vi.mock("$app/state", () => ({ page: { url: new URL("http://x/recipes") } }));
vi.mock("#lib/stores/auth.js", async () => {
  const { readable } = await import("svelte/store");
  return { auth: readable({ user: { id: 1, email: "sam@example.com" } }) };
});
vi.mock("#lib/api/users.js", () => ({
  getPreferences: vi.fn().mockResolvedValue({ theme: "garden-fresh" }),
  updatePreferences: vi.fn(),
}));

import Navbar from "./Navbar.svelte";
import { afterNavigate } from "$app/navigation";
import { get } from "svelte/store";
import { getPreferences, updatePreferences } from "#lib/api/users.js";
import { theme } from "#lib/stores/theme.js";

describe("Navbar menu", () => {
  it("opens and closes, and closes after navigating", async () => {
    const { getByRole, container } = render(Navbar);
    const toggle = getByRole("button", { name: "Menu" });
    const links = container.querySelector("#main-menu")!;

    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(links.classList.contains("open")).toBe(false);

    await fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    expect(links.classList.contains("open")).toBe(true);

    // Following a link navigates; the menu must not stay open over the new page
    const onNavigated = vi.mocked(afterNavigate).mock.calls[0][0];
    onNavigated({} as Parameters<typeof onNavigated>[0]);
    await vi.waitFor(() =>
      expect(links.classList.contains("open")).toBe(false),
    );
  });

  it("keeps every destination in the menu", () => {
    const { container } = render(Navbar);
    const hrefs = [...container.querySelectorAll("#main-menu a")].map((a) =>
      a.getAttribute("href"),
    );

    expect(hrefs).toEqual([
      "/dashboard",
      "/recipes",
      "/ai-generate",
      "/meal-plans",
      "/shopping-lists",
      "/import",
      "/export",
      "/settings",
    ]);
  });
});

describe("Navbar theme button", () => {
  it("steps to the theme it names, from any saved theme", async () => {
    vi.mocked(getPreferences).mockResolvedValue({
      theme: "dark",
    } as Awaited<ReturnType<typeof getPreferences>>);
    vi.mocked(updatePreferences).mockResolvedValue(
      {} as Awaited<ReturnType<typeof updatePreferences>>,
    );
    const { findByRole } = render(Navbar);

    // Dark is recognised (it used to be treated as "not Garden Fresh")
    const button = await findByRole("button", {
      name: "Switch to High Contrast theme",
    });
    expect(get(theme)).toBe("dark");

    await fireEvent.click(button);
    expect(updatePreferences).toHaveBeenCalledWith({ theme: "high-contrast" });
    expect(get(theme)).toBe("high-contrast");
    await findByRole("button", { name: "Switch to System theme" });
  });
});
