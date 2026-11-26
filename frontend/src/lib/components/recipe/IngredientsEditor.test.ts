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

  const values = (boxes: HTMLElement[]) =>
    boxes.map((box) => (box as HTMLInputElement).value);

  it("turns a pasted list into one ingredient per line", async () => {
    const { getByLabelText, getAllByRole } = render(IngredientsEditor, {
      ingredients: ["2 cups flour", "", "salt"],
    });
    const paste = (text: string) => ({
      clipboardData: { getData: () => text },
    });

    // Into an empty box: it is filled, and blank lines are dropped
    await fireEvent.paste(
      getByLabelText("Ingredient 2"),
      paste("1 egg\r\n\n  1 cup milk  \n"),
    );
    await waitFor(() =>
      expect(values(getAllByRole("textbox"))).toEqual([
        "2 cups flour",
        "1 egg",
        "1 cup milk",
        "salt",
      ]),
    );

    // Into a filled box: the lines go in after it
    await fireEvent.paste(
      getByLabelText("Ingredient 1"),
      paste("butter\nsugar"),
    );
    await waitFor(() =>
      expect(values(getAllByRole("textbox")).slice(0, 3)).toEqual([
        "2 cups flour",
        "butter",
        "sugar",
      ]),
    );
  });

  it("leaves a one-line paste to the browser", async () => {
    const { getByLabelText } = render(IngredientsEditor, {
      ingredients: [""],
    });

    const allowed = await fireEvent.paste(getByLabelText("Ingredient 1"), {
      clipboardData: { getData: () => "1 egg" },
    });

    expect(allowed).toBe(true);
  });

  it("moves an ingredient up and down", async () => {
    const { getByRole, getAllByRole } = render(IngredientsEditor, {
      ingredients: ["flour", "egg", "milk"],
    });

    await fireEvent.click(
      getByRole("button", { name: "Move ingredient 3 up" }),
    );
    await waitFor(() =>
      expect(values(getAllByRole("textbox"))).toEqual(["flour", "milk", "egg"]),
    );
    await fireEvent.click(
      getByRole("button", { name: "Move ingredient 1 down" }),
    );
    await waitFor(() =>
      expect(values(getAllByRole("textbox"))).toEqual(["milk", "flour", "egg"]),
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
