/**
 * Recipe note endpoints.
 *
 * Household members leave dated notes on a recipe. Any member may add one; only
 * the author may edit it; the author or the recipe's owner may delete it.
 */

import { apiRequest } from "./client";

export interface RecipeNote {
  id: number;
  recipe_id: number;
  text: string;
  author_name: string;
  /** True when the current user wrote the note */
  is_author: boolean;
  created_at: string;
  updated_at: string | null;
}

/**
 * List a recipe's notes, newest first
 */
export async function listNotes(recipeId: number): Promise<RecipeNote[]> {
  return apiRequest<RecipeNote[]>(`/recipes/${recipeId}/notes`);
}

/**
 * Add a note to a recipe
 */
export async function addNote(
  recipeId: number,
  text: string,
): Promise<RecipeNote> {
  return apiRequest<RecipeNote>(`/recipes/${recipeId}/notes`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

/**
 * Edit one of your own notes
 */
export async function updateNote(
  recipeId: number,
  noteId: number,
  text: string,
): Promise<RecipeNote> {
  return apiRequest<RecipeNote>(`/recipes/${recipeId}/notes/${noteId}`, {
    method: "PATCH",
    body: JSON.stringify({ text }),
  });
}

/**
 * Delete a note (yours, or any note on a recipe you own)
 */
export async function deleteNote(
  recipeId: number,
  noteId: number,
): Promise<void> {
  return apiRequest<void>(`/recipes/${recipeId}/notes/${noteId}`, {
    method: "DELETE",
  });
}
