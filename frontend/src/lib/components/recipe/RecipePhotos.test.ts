import { describe, expect, it } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";

import RecipePhotos from "./RecipePhotos.svelte";

const images = [
  { data: "AAA", mimeType: "image/png" },
  { data: "", url: "https://example.com/two.jpg" },
  { data: "CCC", mimeType: "image/jpeg" },
];

describe("RecipePhotos", () => {
  it("pages through every stored photo, wrapping at both ends", async () => {
    const { getByRole, getByText } = render(RecipePhotos, {
      images,
      name: "Chili",
    });
    const img = () => getByRole("img") as HTMLImageElement;

    expect(img().src).toBe("data:image/png;base64,AAA");
    expect(getByText("1 of 3")).toBeTruthy();

    await fireEvent.click(getByRole("button", { name: "Next photo" }));
    expect(img().src).toBe("https://example.com/two.jpg");
    expect(img().alt).toBe("Chili, photo 2 of 3");

    await fireEvent.click(getByRole("button", { name: "Next photo" }));
    await fireEvent.click(getByRole("button", { name: "Next photo" }));
    expect(getByText("1 of 3")).toBeTruthy();

    await fireEvent.click(getByRole("button", { name: "Previous photo" }));
    expect(img().src).toBe("data:image/jpeg;base64,CCC");
  });

  it("starts at the first photo when the recipe changes", async () => {
    const { getByRole, getByText, rerender } = render(RecipePhotos, {
      images,
      name: "Chili",
    });
    await fireEvent.click(getByRole("button", { name: "Next photo" }));
    await fireEvent.click(getByRole("button", { name: "Next photo" }));

    await rerender({
      images: [{ data: "DDD", mimeType: "image/png" }, ...images],
      name: "Stew",
    });

    expect(getByText("1 of 4")).toBeTruthy();
  });

  it("swipes to the next photo", async () => {
    const { getByRole, getByText } = render(RecipePhotos, {
      images,
      name: "Chili",
    });
    const frame = getByRole("img").parentElement as HTMLElement;

    await fireEvent.touchStart(frame, { touches: [{ clientX: 200 }] });
    await fireEvent.touchEnd(frame, { changedTouches: [{ clientX: 100 }] });

    expect(getByText("2 of 3")).toBeTruthy();
  });

  it("shows one photo with no controls, and falls back to the image address", () => {
    const { getByRole, queryByRole } = render(RecipePhotos, {
      images: [],
      imageUrl: "https://example.com/main.jpg",
      name: "Chili",
    });

    expect((getByRole("img") as HTMLImageElement).src).toBe(
      "https://example.com/main.jpg",
    );
    expect(queryByRole("button")).toBeNull();
  });

  it("shows nothing without a photo", () => {
    const { queryByRole } = render(RecipePhotos, { images: [], name: "Chili" });
    expect(queryByRole("img")).toBeNull();
  });
});
