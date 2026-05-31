/**
 * Tests for RecipeCard component
 */
import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";
import RecipeCard from "./RecipeCard.svelte";
import type { RecipeSummary } from "$lib/api/recipes";

describe("RecipeCard", () => {
  const mockRecipe: RecipeSummary = {
    id: 1,
    name: "Test Recipe",
    description: "A delicious test recipe",
    image_url: "https://example.com/image.jpg",
    cuisine: "Italian",
    category: "Dinner",
    total_time_minutes: 45,
    source_type: "manual",
    created_at: "2024-01-01T00:00:00Z",
  };

  it("should render recipe name", () => {
    const { getByText } = render(RecipeCard, {
      props: { recipe: mockRecipe },
    });

    expect(getByText("Test Recipe")).toBeTruthy();
  });

  it("should render recipe description", () => {
    const { getByText } = render(RecipeCard, {
      props: { recipe: mockRecipe },
    });

    expect(getByText("A delicious test recipe")).toBeTruthy();
  });

  it("should render recipe without description", () => {
    const recipeWithoutDesc = { ...mockRecipe, description: undefined };

    const { queryByText, getByText } = render(RecipeCard, {
      props: { recipe: recipeWithoutDesc },
    });

    expect(getByText("Test Recipe")).toBeTruthy();
    expect(queryByText("A delicious test recipe")).toBeNull();
  });

  it("should render cuisine badge", () => {
    const { getByText } = render(RecipeCard, {
      props: { recipe: mockRecipe },
    });

    expect(getByText("Italian")).toBeTruthy();
  });

  it("should render category badge", () => {
    const { getByText } = render(RecipeCard, {
      props: { recipe: mockRecipe },
    });

    expect(getByText("Dinner")).toBeTruthy();
  });

  it("should render without cuisine badge when not provided", () => {
    const recipeNoCuisine = { ...mockRecipe, cuisine: undefined };

    const { queryByText } = render(RecipeCard, {
      props: { recipe: recipeNoCuisine },
    });

    expect(queryByText("Italian")).toBeNull();
  });

  it("should render without category badge when not provided", () => {
    const recipeNoCategory = { ...mockRecipe, category: undefined };

    const { queryByText } = render(RecipeCard, {
      props: { recipe: recipeNoCategory },
    });

    expect(queryByText("Dinner")).toBeNull();
  });

  it("should format time correctly for minutes only", () => {
    const recipe30Min = { ...mockRecipe, total_time_minutes: 30 };

    const { getByText } = render(RecipeCard, {
      props: { recipe: recipe30Min },
    });

    expect(getByText(/30min/)).toBeTruthy();
  });

  it("should format time correctly for hours only", () => {
    const recipe2Hours = { ...mockRecipe, total_time_minutes: 120 };

    const { getByText } = render(RecipeCard, {
      props: { recipe: recipe2Hours },
    });

    expect(getByText(/2h$/)).toBeTruthy();
  });

  it("should format time correctly for hours and minutes", () => {
    const recipe90Min = { ...mockRecipe, total_time_minutes: 90 };

    const { getByText } = render(RecipeCard, {
      props: { recipe: recipe90Min },
    });

    expect(getByText(/1h 30min/)).toBeTruthy();
  });

  it("should not display time when not provided", () => {
    const recipeNoTime = { ...mockRecipe, total_time_minutes: undefined };

    const { queryByText } = render(RecipeCard, {
      props: { recipe: recipeNoTime },
    });

    expect(queryByText(/min/)).toBeNull();
    expect(queryByText(/h/)).toBeNull();
  });

  it("should show manual source type badge", () => {
    const { getByText } = render(RecipeCard, {
      props: { recipe: mockRecipe },
    });

    expect(getByText(/Manual/)).toBeTruthy();
  });

  it("should show imported source type badge", () => {
    const importedRecipe: RecipeSummary = {
      ...mockRecipe,
      source_type: "imported" as const,
    };

    const { getByText } = render(RecipeCard, {
      props: { recipe: importedRecipe },
    });

    expect(getByText(/Imported/)).toBeTruthy();
  });

  it("should render image from URL", () => {
    const { container } = render(RecipeCard, {
      props: { recipe: mockRecipe },
    });

    const img = container.querySelector("img");
    expect(img).toBeTruthy();
    expect(img?.src).toContain("example.com/image.jpg");
    expect(img?.alt).toBe("Test Recipe");
  });

  it("should render base64 image when provided", () => {
    const recipeWithBase64 = {
      ...mockRecipe,
      recipe_data: {
        images: [
          {
            data: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            mimeType: "image/png",
            url: "",
          },
        ],
      },
    };

    const { container } = render(RecipeCard, {
      props: { recipe: recipeWithBase64 },
    });

    const img = container.querySelector("img");
    expect(img).toBeTruthy();
    expect(img?.src).toContain("data:image/png;base64");
  });

  it("should render placeholder when no image provided", () => {
    const recipeNoImage = { ...mockRecipe, image_url: undefined };

    const { getByText } = render(RecipeCard, {
      props: { recipe: recipeNoImage },
    });

    // Placeholder renders first letter of recipe name
    expect(getByText(mockRecipe.name.charAt(0).toUpperCase())).toBeTruthy();
  });

  it("should dispatch view event when card is clicked", async () => {
    const viewHandler = vi.fn();
    const { container } = render(RecipeCard, {
      props: { recipe: mockRecipe, onview: viewHandler },
    });

    const button = container.querySelector("button");
    await fireEvent.click(button!);

    expect(viewHandler).toHaveBeenCalled();
    expect(viewHandler.mock.calls[0][0]).toEqual(mockRecipe);
  });

  it("should dispatch edit event when edit button clicked", async () => {
    const editHandler = vi.fn();
    const { getByRole } = render(RecipeCard, {
      props: { recipe: mockRecipe, onedit: editHandler },
    });

    const editButton = getByRole("button", { name: "Edit recipe" });
    await fireEvent.click(editButton);

    expect(editHandler).toHaveBeenCalled();
    expect(editHandler.mock.calls[0][0]).toEqual(mockRecipe);
  });

  it("should dispatch delete event when delete button clicked", async () => {
    const deleteHandler = vi.fn();
    const { getByRole } = render(RecipeCard, {
      props: { recipe: mockRecipe, ondelete: deleteHandler },
    });

    const deleteButton = getByRole("button", { name: "Delete recipe" });
    await fireEvent.click(deleteButton);

    expect(deleteHandler).toHaveBeenCalled();
    expect(deleteHandler.mock.calls[0][0]).toEqual(mockRecipe);
  });

  it("should dispatch favorite event when favorite button clicked", async () => {
    const favoriteHandler = vi.fn();
    const { getByRole } = render(RecipeCard, {
      props: { recipe: mockRecipe, onfavorite: favoriteHandler },
    });

    const favoriteButton = getByRole("button", { name: "Add to favorites" });
    await fireEvent.click(favoriteButton);

    expect(favoriteHandler).toHaveBeenCalled();
    expect(favoriteHandler.mock.calls[0][0]).toEqual(mockRecipe);
  });

  it("should show action buttons by default", () => {
    const { getByRole } = render(RecipeCard, {
      props: { recipe: mockRecipe },
    });

    expect(getByRole("button", { name: "Edit recipe" })).toBeTruthy();
    expect(getByRole("button", { name: "Delete recipe" })).toBeTruthy();
    expect(getByRole("button", { name: "Add to favorites" })).toBeTruthy();
  });

  it("should hide action buttons when showActions is false", () => {
    const { queryByRole } = render(RecipeCard, {
      props: { recipe: mockRecipe, showActions: false },
    });

    expect(queryByRole("button", { name: "Edit recipe" })).toBeNull();
    expect(queryByRole("button", { name: "Delete recipe" })).toBeNull();
    expect(queryByRole("button", { name: "Add to favorites" })).toBeNull();
  });

  it("should prevent card click when action button is clicked", async () => {
    const viewHandler = vi.fn();
    const editHandler = vi.fn();
    const { getByRole } = render(RecipeCard, {
      props: { recipe: mockRecipe, onview: viewHandler, onedit: editHandler },
    });

    const editButton = getByRole("button", { name: "Edit recipe" });
    await fireEvent.click(editButton);

    // Edit should be called, but not view
    expect(editHandler).toHaveBeenCalled();
    expect(viewHandler).not.toHaveBeenCalled();
  });

  it("should render minimal recipe with only name", () => {
    const minimalRecipe: RecipeSummary = {
      id: 1,
      name: "Minimal Recipe",
      source_type: "manual",
      created_at: "2024-01-01T00:00:00Z",
    };

    const { getByText, queryByText } = render(RecipeCard, {
      props: { recipe: minimalRecipe },
    });

    expect(getByText("Minimal Recipe")).toBeTruthy();
    expect(queryByText(/min/)).toBeNull();
  });

  it("should handle very long recipe names gracefully", () => {
    const longNameRecipe = {
      ...mockRecipe,
      name: "This is a very long recipe name that should be truncated properly when displayed on the card to prevent layout issues",
    };

    const { getByText } = render(RecipeCard, {
      props: { recipe: longNameRecipe },
    });

    expect(getByText(/This is a very long recipe name/)).toBeTruthy();
  });

  it("should handle very long descriptions gracefully", () => {
    const longDescRecipe = {
      ...mockRecipe,
      description:
        "This is a very long description that should be truncated properly when displayed on the card to prevent layout issues and maintain a clean appearance",
    };

    const { getByText } = render(RecipeCard, {
      props: { recipe: longDescRecipe },
    });

    expect(getByText(/This is a very long description/)).toBeTruthy();
  });

  it("should format 1 minute correctly", () => {
    const recipe1Min = { ...mockRecipe, total_time_minutes: 1 };

    const { getByText } = render(RecipeCard, {
      props: { recipe: recipe1Min },
    });

    expect(getByText(/1min/)).toBeTruthy();
  });

  it("should format 1 hour correctly", () => {
    const recipe1Hour = { ...mockRecipe, total_time_minutes: 60 };

    const { getByText } = render(RecipeCard, {
      props: { recipe: recipe1Hour },
    });

    expect(getByText(/1h$/)).toBeTruthy();
  });

  it("should format 1 hour 1 minute correctly", () => {
    const recipe61Min = { ...mockRecipe, total_time_minutes: 61 };

    const { getByText } = render(RecipeCard, {
      props: { recipe: recipe61Min },
    });

    expect(getByText(/1h 1min/)).toBeTruthy();
  });
});
