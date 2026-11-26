import { existsSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("web app manifest", () => {
  const manifest = JSON.parse(
    readFileSync("static/manifest.webmanifest", "utf8"),
  );

  it("names the app and opens it in its own window", () => {
    expect(manifest.name).toBe("Recipe Catalog");
    expect(manifest.display).toBe("standalone");
    expect(manifest.start_url).toBe("/dashboard");
  });

  it("offers the 192px and 512px icons browsers need to install it", () => {
    const sizes = manifest.icons.map((icon: { sizes: string }) => icon.sizes);
    expect(sizes).toContain("192x192");
    expect(sizes).toContain("512x512");
    for (const icon of manifest.icons) {
      expect(existsSync(`static${icon.src}`), icon.src).toBe(true);
    }
  });

  it("is linked from the page shell", () => {
    expect(readFileSync("src/app.html", "utf8")).toContain(
      'rel="manifest" href="%sveltekit.assets%/manifest.webmanifest"',
    );
  });
});
