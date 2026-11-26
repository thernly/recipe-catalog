import { writable } from "svelte/store";
import { TOAST_DURATION } from "#lib/constants.js";

export type ToastType = "success" | "error" | "info" | "warning";

interface ToastItem {
  id: number;
  type: ToastType;
  message: string;
}

function createToastStore() {
  const { subscribe, update } = writable<ToastItem[]>([]);
  let nextId = 0;

  function addToast(type: ToastType, message: string) {
    const id = nextId++;
    // The same message already on screen is not stacked again: errors stay
    // until closed, so a repeating failure would otherwise fill the screen.
    update((toasts) =>
      toasts.some((t) => t.type === type && t.message === message)
        ? toasts
        : [...toasts, { id, type, message }],
    );

    // An error stays until the person closes it: it may need reading twice,
    // or copying down. Everything else goes away by itself.
    if (type === "error") return;
    setTimeout(() => {
      update((toasts) => toasts.filter((t) => t.id !== id));
    }, TOAST_DURATION);
  }

  return {
    subscribe,
    success: (message: string) => addToast("success", message),
    error: (message: string) => addToast("error", message),
    info: (message: string) => addToast("info", message),
    warning: (message: string) => addToast("warning", message),
    remove: (id: number) => {
      update((toasts) => toasts.filter((t) => t.id !== id));
    },
  };
}

export const toast = createToastStore();
export const toasts = toast;
