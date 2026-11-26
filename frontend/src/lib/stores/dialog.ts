import { writable } from "svelte/store";

interface DialogOptions {
  title: string;
  message: string;
  onConfirm: () => void;
  /** The confirm button's text. Default: the title's first word ("Delete"). */
  confirmLabel?: string;
  /** Red confirm button, for actions that remove something. Default: true
   *  unless the title starts with a verb that removes nothing (see SAFE). */
  danger?: boolean;
}

interface DialogState extends Required<DialogOptions> {
  open: boolean;
}

// Titles are "Verb Thing" ("Delete Recipe", "Archive List"), so the verb makes
// a better button than "Confirm". These verbs take nothing away.
const SAFE = /^(Transfer|Join|Add|Archive|Duplicate|Save)\b/;

const dialogStore = writable<DialogState>({
  open: false,
  title: "",
  message: "",
  onConfirm: () => {},
  confirmLabel: "Confirm",
  danger: true,
});

export const dialog = {
  subscribe: dialogStore.subscribe,
  show: (options: DialogOptions) => {
    dialogStore.set({
      open: true,
      title: options.title,
      message: options.message,
      onConfirm: options.onConfirm,
      confirmLabel: options.confirmLabel ?? options.title.split(" ")[0],
      danger: options.danger ?? !SAFE.test(options.title),
    });
  },
  close: () => {
    dialogStore.update((state) => ({ ...state, open: false }));
  },
};
