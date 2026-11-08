import { describe, expect, it } from "vitest";
import { safeHttpUrl, safeRedirect } from "./urls.js";

describe("recipe and redirect URLs", () => {
  it.each([
    "javascript:alert(1)",
    "data:text/html,test",
    "//evil.test",
    "bad url",
    "https://",
  ])("does not expose unsafe or malformed source %s", (value) => {
    expect(safeHttpUrl(value)).toBeNull();
  });
  it("extracts valid source hosts", () => {
    expect(safeHttpUrl("https://example.com/recipe")?.hostname).toBe(
      "example.com",
    );
  });
  it.each(["//evil.test", "/\\evil.test", "https://evil.test", null])(
    "rejects external login redirect %s",
    (value) => {
      expect(safeRedirect(value)).toBe("/dashboard");
    },
  );
  it("retains invitation destinations", () => {
    expect(safeRedirect("/households/join?code=soup")).toBe(
      "/households/join?code=soup",
    );
  });
});
