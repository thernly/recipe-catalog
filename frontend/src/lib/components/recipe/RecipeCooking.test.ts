import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";

vi.mock("#lib/api/recipes.js", () => ({ updateCooking: vi.fn() }));

import RecipeCooking from "./RecipeCooking.svelte";
import { updateCooking } from "#lib/api/recipes.js";

const today = new Date().toLocaleDateString("en-CA");

describe("RecipeCooking", () => {
  beforeEach(() => vi.mocked(updateCooking).mockReset());

  it("rates the recipe, and clears the rating when it is tapped again", async () => {
    vi.mocked(updateCooking).mockResolvedValue({
      rating: 4,
      last_cooked_on: null,
    });
    const { getByRole } = render(RecipeCooking, { recipeId: 7 });
    const four = getByRole("button", { name: "Rate 4 out of 5" });

    await fireEvent.click(four);
    expect(updateCooking).toHaveBeenCalledWith(7, { rating: 4 });
    await waitFor(() => expect(four.getAttribute("aria-pressed")).toBe("true"));

    await fireEvent.click(four);
    expect(updateCooking).toHaveBeenLastCalledWith(7, { rating: null });
  });

  it("marks the recipe cooked today and shows the date", async () => {
    vi.mocked(updateCooking).mockResolvedValue({
      rating: null,
      last_cooked_on: today,
    });
    const { getByRole, getByText, findByText, queryByRole } = render(
      RecipeCooking,
      { recipeId: 7 },
    );
    expect(getByText("Not cooked yet")).toBeTruthy();

    await fireEvent.click(getByRole("button", { name: "Cooked today" }));

    expect(updateCooking).toHaveBeenCalledWith(7, { last_cooked_on: today });
    expect(await findByText(/^Last cooked /)).toBeTruthy();
    expect(queryByRole("button", { name: "Cooked today" })).toBeNull();
  });

  it("shows an earlier date and can clear it", async () => {
    vi.mocked(updateCooking).mockResolvedValue({
      rating: 3,
      last_cooked_on: null,
    });
    const { getByRole, getByText, findByText } = render(RecipeCooking, {
      recipeId: 7,
      rating: 3,
      lastCookedOn: "2026-11-01",
    });
    expect(getByText(/Last cooked .*2026/)).toBeTruthy();

    await fireEvent.click(getByRole("button", { name: "Clear" }));

    expect(updateCooking).toHaveBeenCalledWith(7, { last_cooked_on: null });
    expect(await findByText("Not cooked yet")).toBeTruthy();
  });
});
