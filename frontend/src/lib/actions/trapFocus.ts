const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Keeps Tab and Shift+Tab inside `node` (use on a modal dialog). */
export function trapFocus(node: HTMLElement) {
  function onKeydown(e: KeyboardEvent) {
    if (e.key !== "Tab") return;
    const items = [...node.querySelectorAll<HTMLElement>(FOCUSABLE)];
    if (items.length === 0) {
      e.preventDefault();
      return;
    }
    const first = items[0];
    const last = items[items.length - 1];
    const active = document.activeElement;
    if (e.shiftKey && (active === first || active === node)) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && active === last) {
      e.preventDefault();
      first.focus();
    }
  }
  node.addEventListener("keydown", onKeydown);
  return { destroy: () => node.removeEventListener("keydown", onKeydown) };
}
