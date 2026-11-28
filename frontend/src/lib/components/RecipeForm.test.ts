/**
 * Editing a recipe must not drop stored data the form does not show.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";

vi.mock("$app/navigation", () => ({ beforeNavigate: vi.fn() }));
vi.mock("#lib/api/users.js", () => ({
  getPreferences: vi.fn().mockResolvedValue({
    default_cuisines: ["Thai"],
    custom_cuisines: ["Italian", "Thai"],
    default_categories: ["Dessert"],
    custom_categories: [],
  }),
}));

import RecipeForm from "./RecipeForm.svelte";
import { beforeNavigate } from "$app/navigation";
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

  it("lets the source address of an existing recipe be added and cleared", async () => {
    const added = await submitted(async (container) => {
      await fireEvent.input(container.querySelector("#sourceUrl")!, {
        target: { value: "https://example.com/stew" },
      });
    });
    expect(added.source_url).toBe("https://example.com/stew");

    // The recipe has no address: saving sends null, which clears it
    expect((await submitted()).source_url).toBeNull();
  });

  describe("photos", () => {
    const first = {
      url: "https://example.com/a.jpg",
      data: "QQ==",
      mimeType: "image/jpeg",
    };
    const second = {
      url: "https://example.com/b.jpg",
      data: "Qg==",
      mimeType: "image/jpeg",
    };
    const withPhotos: Recipe = {
      ...recipe,
      image_url: first.url,
      recipe_data: { ...recipe.recipe_data, images: [first, second] },
    };

    async function saved(click: string[]) {
      const onSubmit = vi.fn();
      const { container, getByRole } = render(RecipeForm, {
        props: { recipe: withPhotos },
        events: { submit: onSubmit },
      });
      for (const name of click)
        await fireEvent.click(getByRole("button", { name }));
      await fireEvent.submit(container.querySelector("form")!);
      return onSubmit.mock.calls[0][0].detail;
    }

    it("removes a photo on save, and the image address follows the main photo", async () => {
      const data = await saved(["Remove photo 1"]);

      expect(data.recipe_data.images).toEqual([second]);
      expect(data.image_url).toBe(second.url);
    });

    it("makes another photo the main one", async () => {
      const data = await saved(["Make photo 2 the main photo"]);

      expect(data.recipe_data.images).toEqual([second, first]);
      expect(data.image_url).toBe(second.url);
    });

    it("can remove every photo", async () => {
      const data = await saved(["Remove photo 2", "Remove photo 1"]);

      expect(data.recipe_data.images).toEqual([]);
      expect(data.image_url).toBeUndefined();
    });

    it("asks before leaving after a photo is removed", async () => {
      vi.mocked(beforeNavigate).mockReset();
      const { getByRole } = render(RecipeForm, {
        props: { recipe: withPhotos },
      });
      const guard = vi.mocked(beforeNavigate).mock.calls[0][0];
      const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
      const navigation = { willUnload: false, cancel: vi.fn() };

      await fireEvent.click(getByRole("button", { name: "Remove photo 2" }));
      guard(navigation as unknown as Parameters<typeof guard>[0]);

      expect(confirm).toHaveBeenCalledOnce();
      confirm.mockRestore();
    });

    const pick = (container: HTMLElement, file: File) => {
      const input =
        container.querySelector<HTMLInputElement>('input[type="file"]')!;
      Object.defineProperty(input, "files", {
        value: [file],
        configurable: true,
      });
      return fireEvent.change(input);
    };

    it("adds a photo to a recipe that had none", async () => {
      const onSubmit = vi.fn();
      const { container, getByRole } = render(RecipeForm, {
        props: {
          recipe: {
            ...recipe,
            recipe_data: { ...recipe.recipe_data, images: [] },
          },
        },
        events: { submit: onSubmit },
      });

      await pick(container, new File(["abc"], "a.png", { type: "image/png" }));
      await waitFor(() => getByRole("img", { name: "Photo 1" }));
      await fireEvent.submit(container.querySelector("form")!);

      expect(onSubmit.mock.calls[0][0].detail.recipe_data.images).toEqual([
        { url: "", data: btoa("abc"), mimeType: "image/png" },
      ]);
    });

    it("stops offering to add a photo at five", async () => {
      const photo = (n: number) => ({
        url: "",
        data: `D${n}`,
        mimeType: "image/png",
      });
      const { container, getByText } = render(RecipeForm, {
        props: {
          recipe: {
            ...recipe,
            recipe_data: {
              ...recipe.recipe_data,
              images: [1, 2, 3, 4, 5].map(photo),
            },
          },
        },
      });

      expect(container.querySelector('input[type="file"]')).toBeNull();
      expect(getByText("A recipe can have 5 photos.")).toBeTruthy();
    });

    it("explains a photo that cannot be added", async () => {
      vi.stubGlobal(
        "createImageBitmap",
        vi.fn().mockRejectedValue(new Error()),
      );
      const { container, findByRole } = render(RecipeForm);

      await pick(container, new File(["x"], "a.heic", { type: "image/heic" }));

      expect((await findByRole("alert")).textContent).toContain(
        "not a picture",
      );
      vi.unstubAllGlobals();
    });
  });

  it("suggests the cuisines and categories the recipe list filters on", async () => {
    const { container } = render(RecipeForm, { props: { recipe } });
    const options = (id: string) =>
      [...container.querySelectorAll(`#${id} option`)].map((option) =>
        option.getAttribute("value"),
      );

    await waitFor(() =>
      expect(options("cuisine-options")).toEqual(["Italian", "Thai"]),
    );
    expect(options("category-options")).toEqual(["Dessert"]);
    expect(container.querySelector("#cuisine")?.getAttribute("list")).toBe(
      "cuisine-options",
    );
  });
});

describe("RecipeForm drafts", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.mocked(beforeNavigate).mockReset();
  });

  const nameInput = (container: HTMLElement) =>
    container.querySelector<HTMLInputElement>("#name")!;

  it("saves a new recipe as it is typed and restores it next time", async () => {
    const first = render(RecipeForm);
    await fireEvent.input(nameInput(first.container), {
      target: { value: "Half-written pie" },
    });
    await waitFor(() =>
      expect(localStorage.getItem("recipe-draft")).toContain(
        "Half-written pie",
      ),
    );
    first.unmount();

    const second = render(RecipeForm);
    await waitFor(() =>
      expect(nameInput(second.container).value).toBe("Half-written pie"),
    );
    second.getByText("We restored the recipe you were writing.");
  });

  it("starts over on request and forgets the draft", async () => {
    localStorage.setItem("recipe-draft", JSON.stringify({ name: "Old pie" }));
    const { container, findByRole } = render(RecipeForm);

    await fireEvent.click(await findByRole("button", { name: "Start over" }));

    expect(nameInput(container).value).toBe("");
    await waitFor(() =>
      expect(localStorage.getItem("recipe-draft")).toBeNull(),
    );
  });

  it("does not draft or restore when editing an existing recipe", async () => {
    localStorage.setItem("recipe-draft", JSON.stringify({ name: "Old pie" }));
    const { container } = render(RecipeForm, { props: { recipe } });

    expect(nameInput(container).value).toBe("Stew");
    expect(localStorage.getItem("recipe-draft")).toContain("Old pie");
  });

  it("asks before leaving an edited recipe, but not an untouched one", async () => {
    const { container } = render(RecipeForm, { props: { recipe } });
    const guard = vi.mocked(beforeNavigate).mock.calls[0][0];
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const navigation = { willUnload: false, cancel: vi.fn() };
    type Navigation = Parameters<typeof guard>[0];

    guard(navigation as unknown as Navigation);
    expect(confirm).not.toHaveBeenCalled();

    await fireEvent.input(nameInput(container), { target: { value: "Soup" } });
    guard(navigation as unknown as Navigation);
    expect(confirm).toHaveBeenCalledOnce();
    expect(navigation.cancel).toHaveBeenCalledOnce();
  });
});
