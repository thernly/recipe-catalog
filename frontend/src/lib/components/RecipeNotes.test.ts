/**
 * Tests for the recipe "Household Notes" section
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import { get } from "svelte/store";

vi.mock("#lib/api/recipe-notes.js", () => ({
  listNotes: vi.fn(),
  addNote: vi.fn(),
  updateNote: vi.fn(),
  deleteNote: vi.fn(),
}));

import RecipeNotes from "./RecipeNotes.svelte";
import {
  listNotes,
  addNote,
  updateNote,
  deleteNote,
  type RecipeNote,
} from "#lib/api/recipe-notes.js";
import { dialog } from "#lib/stores/dialog.js";

const mine: RecipeNote = {
  id: 1,
  recipe_id: 7,
  text: "Halved the sugar",
  author_name: "Sam",
  is_author: true,
  created_at: "2026-11-14T18:02:00Z",
  updated_at: null,
};

const theirs: RecipeNote = {
  ...mine,
  id: 2,
  text: "Needs more salt",
  author_name: "Milo",
  is_author: false,
};

describe("RecipeNotes", () => {
  beforeEach(() => {
    vi.mocked(listNotes).mockReset();
    vi.mocked(addNote).mockReset();
    vi.mocked(updateNote).mockReset();
    vi.mocked(deleteNote).mockReset();
    dialog.close();
  });

  it("lists notes with their author", async () => {
    vi.mocked(listNotes).mockResolvedValue([theirs, mine]);

    const { findByText, getByText } = render(RecipeNotes, {
      props: { recipeId: 7 },
    });

    expect(await findByText("Needs more salt")).toBeTruthy();
    expect(getByText("Milo")).toBeTruthy();
    expect(getByText("Sam")).toBeTruthy();
    expect(listNotes).toHaveBeenCalledWith(7);
  });

  it("shows existing notes above the add-note box", async () => {
    vi.mocked(listNotes).mockResolvedValue([mine]);

    const { findByText, getByLabelText, getByRole } = render(RecipeNotes, {
      props: { recipeId: 7 },
    });

    expect(getByRole("heading", { name: "Household Notes" })).toBeTruthy();
    const note = await findByText("Halved the sugar");
    const input = getByLabelText("Add a note");
    expect(
      note.compareDocumentPosition(input) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("shows an empty state", async () => {
    vi.mocked(listNotes).mockResolvedValue([]);

    const { findByText } = render(RecipeNotes, { props: { recipeId: 7 } });

    expect(await findByText("No notes yet.")).toBeTruthy();
  });

  it("shows a load error", async () => {
    vi.mocked(listNotes).mockRejectedValue(new Error("boom"));

    const { findByRole } = render(RecipeNotes, { props: { recipeId: 7 } });

    expect((await findByRole("alert")).textContent).toContain(
      "Failed to load notes",
    );
  });

  it("adds a trimmed note to the top of the list", async () => {
    vi.mocked(listNotes).mockResolvedValue([theirs]);
    vi.mocked(addNote).mockResolvedValue({ ...mine, id: 3, text: "Great" });

    const { getByLabelText, getByRole, findByText } = render(RecipeNotes, {
      props: { recipeId: 7 },
    });
    await findByText("Needs more salt");

    const input = getByLabelText("Add a note") as HTMLTextAreaElement;
    await fireEvent.input(input, { target: { value: "  Great  " } });
    await fireEvent.click(getByRole("button", { name: "Add note" }));

    expect(addNote).toHaveBeenCalledWith(7, "Great");
    expect(await findByText("Great")).toBeTruthy();
    expect(input.value).toBe("");
  });

  it("offers editing only on your own notes", async () => {
    vi.mocked(listNotes).mockResolvedValue([theirs, mine]);
    vi.mocked(updateNote).mockResolvedValue({
      ...mine,
      text: "Used a third of the sugar",
      updated_at: "2026-11-15T09:00:00Z",
    });

    const { findAllByRole, getByLabelText, getByRole, findByText } = render(
      RecipeNotes,
      { props: { recipeId: 7 } },
    );

    const editButtons = await findAllByRole("button", { name: "Edit" });
    expect(editButtons).toHaveLength(1);

    await fireEvent.click(editButtons[0]);
    await fireEvent.input(getByLabelText("Edit note"), {
      target: { value: "Used a third of the sugar" },
    });
    await fireEvent.click(getByRole("button", { name: "Save" }));

    expect(updateNote).toHaveBeenCalledWith(7, 1, "Used a third of the sugar");
    expect(await findByText("Used a third of the sugar")).toBeTruthy();
    expect(await findByText("(edited)")).toBeTruthy();
  });

  it("lets a member delete only their own notes", async () => {
    vi.mocked(listNotes).mockResolvedValue([theirs, mine]);

    const { findAllByRole } = render(RecipeNotes, {
      props: { recipeId: 7, isRecipeOwner: false },
    });

    expect(await findAllByRole("button", { name: "Delete" })).toHaveLength(1);
  });

  it("lets the recipe owner delete anyone's note after confirming", async () => {
    vi.mocked(listNotes).mockResolvedValue([theirs]);
    vi.mocked(deleteNote).mockResolvedValue();

    const { findByRole, findByText } = render(RecipeNotes, {
      props: { recipeId: 7, isRecipeOwner: true },
    });
    await fireEvent.click(await findByRole("button", { name: "Delete" }));

    // Nothing happens until the dialog is confirmed
    const state = get(dialog);
    expect(state.open).toBe(true);
    expect(state.message).toContain("Milo's note");
    expect(deleteNote).not.toHaveBeenCalled();

    await state.onConfirm();

    await waitFor(() => expect(deleteNote).toHaveBeenCalledWith(7, 2));
    expect(await findByText("No notes yet.")).toBeTruthy();
  });
});
