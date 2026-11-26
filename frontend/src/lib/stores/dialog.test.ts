import { describe, expect, it } from "vitest";
import { get } from "svelte/store";
import { dialog } from "./dialog.js";

const shown = (options: {
  title: string;
  confirmLabel?: string;
  danger?: boolean;
}) => {
  dialog.show({ message: "", onConfirm: () => {}, ...options });
  const { confirmLabel, danger } = get(dialog);
  return [confirmLabel, danger];
};

describe("dialog store", () => {
  it("names the confirm button after the action, red when it removes something", () => {
    expect(shown({ title: "Delete Recipe" })).toEqual(["Delete", true]);
    expect(shown({ title: "Remove Member" })).toEqual(["Remove", true]);
    expect(shown({ title: "Discard this recipe?" })).toEqual(["Discard", true]);
  });

  it("is not red for actions that take nothing away", () => {
    expect(shown({ title: "Transfer Ownership" })).toEqual(["Transfer", false]);
    expect(shown({ title: "Archive List" })).toEqual(["Archive", false]);
    expect(shown({ title: "Add This Week Again?" })).toEqual(["Add", false]);
  });

  it("lets a caller choose both", () => {
    expect(
      shown({ title: "Sign Out Session", confirmLabel: "Sign out" }),
    ).toEqual(["Sign out", true]);
    expect(shown({ title: "Delete Draft", danger: false })).toEqual([
      "Delete",
      false,
    ]);
  });
});
