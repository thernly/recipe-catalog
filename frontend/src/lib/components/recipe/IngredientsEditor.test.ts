import { describe, expect, it } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import IngredientsEditor from "./IngredientsEditor.svelte";

describe("IngredientsEditor", () => {
  it("Enter on the last line adds a line and moves to it, without submitting", async () => {
    const { getByLabelText, getAllByRole } = render(IngredientsEditor, {
      ingredients: ["2 cups flour"],
    });
    const first = getByLabelText("Ingredient 1");

    // fireEvent returns false when the default action (submitting) was prevented
    const allowed = await fireEvent.keyDown(first, { key: "Enter" });

    expect(allowed).toBe(false);
    await waitFor(() => expect(getAllByRole("textbox")).toHaveLength(2));
    await waitFor(() =>
      expect(document.activeElement).toBe(getByLabelText("Ingredient 2")),
    );
  });

  it("Enter on an earlier line moves to the next one without adding a line", async () => {
    const { getByLabelText, getAllByRole } = render(IngredientsEditor, {
      ingredients: ["2 cups flour", "1 egg"],
    });

    await fireEvent.keyDown(getByLabelText("Ingredient 1"), { key: "Enter" });

    await waitFor(() =>
      expect(document.activeElement).toBe(getByLabelText("Ingredient 2")),
    );
    expect(getAllByRole("textbox")).toHaveLength(2);
  });
});
