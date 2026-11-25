/**
 * Editing a recipe must not drop stored data the form does not show.
 */
import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";
import RecipeForm from "./RecipeForm.svelte";
import type { Recipe } from "#lib/api/recipes.js";

const recipe: Recipe = {
  id: 7,
  user_id: 1,
  name: "Stew",
  recipe_data: {
    name: "Stew",
    recipeIngredient: ["1 onion"],
    recipeInstructions: ["Cook it."],
    totalTime: "PT3H",
    notes: "Better the next day",
    nutrition: { calories: "400 kcal" },
    images: [{ mimeType: "image/png", data: "aGk=" }],
  } as Recipe["recipe_data"],
  source_type: "imported",
  is_modified: false,
  created_at: "2026-11-01T00:00:00Z",
  updated_at: "2026-11-01T00:00:00Z",
  total_time_minutes: 180,
};

async function submitted(edit?: (container: HTMLElement) => Promise<void>) {
  const onSubmit = vi.fn();
  const { container } = render(RecipeForm, {
    props: { recipe },
    events: { submit: onSubmit },
  });
  await edit?.(container);
  await fireEvent.submit(container.querySelector("form")!);
  expect(onSubmit).toHaveBeenCalledOnce();
  return onSubmit.mock.calls[0][0].detail;
}

describe("RecipeForm", () => {
  it("keeps nutrition, images and a total-only time when saving an edit", async () => {
    const data = await submitted();

    expect(data.recipe_data.nutrition).toEqual({ calories: "400 kcal" });
    expect(data.recipe_data.images).toEqual(recipe.recipe_data.images);
    expect(data.recipe_data.totalTime).toBe("PT3H");
    expect(data.total_time_minutes).toBe(180);
  });

  it("still lets a shown field be cleared", async () => {
    const data = await submitted(async (container) => {
      await fireEvent.input(container.querySelector("#recipe-notes")!, {
        target: { value: "" },
      });
    });

    expect(data.recipe_data.notes).toBeUndefined();
  });

  it("recalculates the total once prep or cook time is entered", async () => {
    const data = await submitted(async (container) => {
      await fireEvent.input(container.querySelector("#cook-time-minutes")!, {
        target: { value: "90" },
      });
    });

    expect(data.recipe_data.cookTime).toBe("PT90M");
    expect(data.total_time_minutes).toBe(90);
  });
});
