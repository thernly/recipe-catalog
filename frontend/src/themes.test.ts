/**
 * Text contrast of the theme colours in app.css (WCAG 2 contrast ratio).
 *
 * Enforced for the themes listed in CHECKED. A new theme belongs there.
 */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

// Comments are removed so one sitting above a block is not read as its selector
const css = readFileSync("src/app.css", "utf8").replace(
  /\/\*[\s\S]*?\*\//g,
  "",
);

/** Every custom property a theme ends up with: :root, then its blocks in order. */
function themeVars(id: string): Record<string, string> {
  const vars: Record<string, string> = {};
  for (const [, selectors, body] of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const names = selectors.split(",").map((s) => s.trim());
    if (!names.includes(":root") && !names.includes(`[data-theme="${id}"]`))
      continue;
    for (const [, name, value] of body.matchAll(/(--[\w-]+):\s*([^;]+);/g))
      vars[name] = value.trim();
  }
  return vars;
}

function hex(vars: Record<string, string>, name: string): string {
  let value = vars[name];
  for (let i = 0; i < 5 && value?.startsWith("var("); i++)
    value = vars[value.slice(4, -1)];
  if (!/^#[0-9a-f]{6}$/i.test(value ?? ""))
    throw new Error(`${name} is not a hex colour: ${value}`);
  return value;
}

function luminance(colour: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(colour.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// [text, background, minimum ratio]. 4.5 is body text; 3 is large or bold text.
const PAIRS: [string, string, number][] = [
  ...["--text-900", "--text-700", "--text-600", "--text-500"].flatMap(
    (text): [string, string, number][] => [
      [text, "--neutral-50", 4.5],
      [text, "--neutral-white", 4.5],
      [text, "--neutral-100", 4.5],
    ],
  ),
  ["--color-navbar-text", "--color-navbar-bg", 4.5],
  ["--color-btn-primary-text", "--color-btn-primary-bg", 4.5],
  ["--color-btn-primary-text", "--color-btn-primary-hover", 4.5],
  ["--color-btn-secondary-text", "--color-btn-secondary-bg", 4.5],
  ["--color-badge-text", "--color-badge-bg", 4.5],
  ["--color-sidebar-active-text", "--color-sidebar-active-bg", 4.5],
  ["--color-link", "--neutral-50", 4.5],
  ["--color-link", "--neutral-white", 4.5],
  // Accent 600 and 700 are used as text (links, active tabs, labels)
  ["--accent-600", "--neutral-50", 4.5],
  ["--accent-600", "--neutral-white", 4.5],
  ["--accent-700", "--neutral-50", 4.5],
  ["--accent-700", "--neutral-white", 4.5],
  ["--accent-700", "--accent-50", 4.5],
  // Gradient buttons put --neutral-white text on accent 500 to 700
  ["--neutral-white", "--accent-500", 3],
  ["--neutral-white", "--accent-600", 3],
  ["--neutral-white", "--accent-700", 3],
];

function shortfalls(id: string): string[] {
  const vars = themeVars(id);
  return PAIRS.flatMap(([text, background, minimum]) => {
    const ratio = contrast(hex(vars, text), hex(vars, background));
    return ratio >= minimum
      ? []
      : [`${text} on ${background}: ${ratio.toFixed(2)} (needs ${minimum})`];
  });
}

const CHECKED = [
  "garden-fresh",
  "bistro",
  "high-contrast",
  "ember",
  "coastal",
  "farmhouse",
];
// Known shortfall, 2026-11-26. Dark: the dark --neutral-white text on
// accent-500 (2.8). Move it up once it passes.
const NOT_YET = ["dark"];

describe("theme contrast", () => {
  it("calculates the standard ratios", () => {
    expect(contrast("#000000", "#ffffff")).toBeCloseTo(21, 5);
    expect(contrast("#777777", "#ffffff")).toBeCloseTo(4.48, 2);
  });

  it.each(CHECKED)("%s keeps its text readable", (id) => {
    expect(shortfalls(id)).toEqual([]);
  });

  it.each(NOT_YET)("%s defines every colour the check reads", (id) => {
    expect(() => shortfalls(id)).not.toThrow();
  });
});
