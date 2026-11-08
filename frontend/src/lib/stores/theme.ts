import { writable } from "svelte/store";
import { browser } from "$app/env";

function savedTheme(): string {
  if (browser) {
    try {
      return localStorage.getItem("recipe-theme") || "garden-fresh";
    } catch {
      /* Storage may be unavailable in restricted browser contexts. */
    }
  }
  return "garden-fresh";
}

export const theme = writable(savedTheme());

export function watchTheme(): () => void {
  const media = window.matchMedia?.("(prefers-color-scheme: dark)");
  let selected = "garden-fresh";
  const apply = () =>
    document.documentElement.setAttribute(
      "data-theme",
      selected === "system"
        ? media?.matches
          ? "dark"
          : "garden-fresh"
        : selected,
    );
  const unsubscribe = theme.subscribe((value) => {
    selected = value;
    try {
      localStorage.setItem("recipe-theme", value);
    } catch {
      /* The selection still applies. */
    }
    apply();
  });
  media?.addEventListener("change", apply);
  return () => {
    unsubscribe();
    media?.removeEventListener("change", apply);
  };
}
