import { describe, expect, it } from "vitest";
import { trapFocus } from "./trapFocus.js";

describe("trapFocus", () => {
  it("wraps Tab from last to first and Shift+Tab from first to last", () => {
    const node = document.createElement("div");
    node.innerHTML = '<button id="a">a</button><button id="b">b</button>';
    document.body.appendChild(node);
    const { destroy } = trapFocus(node);
    const [a, b] = node.querySelectorAll("button");

    b.focus();
    node.dispatchEvent(
      new KeyboardEvent("keydown", { key: "Tab", bubbles: true }),
    );
    expect(document.activeElement).toBe(a);

    node.dispatchEvent(
      new KeyboardEvent("keydown", {
        key: "Tab",
        shiftKey: true,
        bubbles: true,
      }),
    );
    expect(document.activeElement).toBe(b);

    destroy();
    node.remove();
  });
});
