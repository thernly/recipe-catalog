import { afterEach, describe, expect, it, vi } from "vitest";
import { MAX_PHOTO_BYTES, shrinkPhoto } from "./shrink-photo.js";

describe("shrinkPhoto", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("keeps a small JPEG as it is", async () => {
    const file = new File(["abc"], "a.jpg", { type: "image/jpeg" });

    expect(await shrinkPhoto(file)).toEqual({
      url: "",
      data: btoa("abc"),
      mimeType: "image/jpeg",
    });
  });

  it("lowers the quality, then the size, until the photo fits", async () => {
    const close = vi.fn();
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn().mockResolvedValue({ width: 4000, height: 3000, close }),
    );
    const tried: Array<[number, number]> = [];
    const canvas = {
      width: 0,
      height: 0,
      getContext: () => ({ drawImage: vi.fn() }),
      toBlob(done: (blob: Blob) => void, _type: string, quality: number) {
        tried.push([this.width, quality]);
        // Fits only once it is 1200px wide at the lowest quality
        const fits = this.width <= 1200 && quality < 0.5;
        done(new Blob([fits ? "x" : "x".repeat(MAX_PHOTO_BYTES + 1)]));
      },
    };
    vi.spyOn(document, "createElement").mockReturnValue(
      canvas as unknown as HTMLElement,
    );
    const big = new File(["x".repeat(MAX_PHOTO_BYTES + 1)], "big.jpg", {
      type: "image/jpeg",
    });

    const photo = await shrinkPhoto(big);

    expect(photo).toEqual({ url: "", data: btoa("x"), mimeType: "image/jpeg" });
    expect(tried[0]).toEqual([1600, 0.85]);
    expect(tried.at(-1)?.[0]).toBe(1200);
    expect(close).toHaveBeenCalled();
  });

  it("explains a file the browser cannot open", async () => {
    vi.stubGlobal("createImageBitmap", vi.fn().mockRejectedValue(new Error()));
    const file = new File(["x"], "a.heic", { type: "image/heic" });

    await expect(shrinkPhoto(file)).rejects.toThrow("not a picture");
  });
});
