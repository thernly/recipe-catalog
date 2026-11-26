/**
 * Tests for the export page: choosing whose recipes go into an export
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";

vi.mock("#lib/api/client.js", () => ({ apiRequest: vi.fn() }));
vi.mock("#lib/api/users.js", () => ({ getUserStats: vi.fn() }));
vi.mock("#lib/utils/download.js", () => ({ downloadBlob: vi.fn() }));

import Page from "./+page.svelte";
import { apiRequest } from "#lib/api/client.js";
import { getUserStats } from "#lib/api/users.js";

describe("export page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getUserStats).mockResolvedValue({
      total_recipes: 1,
      total_collections: 0,
    } as Awaited<ReturnType<typeof getUserStats>>);
    vi.mocked(apiRequest).mockResolvedValue(new Blob());
  });

  it("exports only your own recipes unless the household is chosen", async () => {
    const { findByRole, getByLabelText } = render(Page);

    await fireEvent.click(await findByRole("button", { name: /Plain Text/ }));
    await waitFor(() =>
      expect(apiRequest).toHaveBeenLastCalledWith(
        "/export/recipes?format=text&scope=mine",
        { responseType: "blob" },
      ),
    );

    await fireEvent.change(getByLabelText("Recipes to include"), {
      target: { value: "household" },
    });
    await fireEvent.click(
      await findByRole("button", { name: /Download Complete Backup/ }),
    );
    await waitFor(() =>
      expect(apiRequest).toHaveBeenLastCalledWith(
        "/export/all?scope=household",
        { responseType: "blob" },
      ),
    );
  });

  it("does not send a scope for collections, which are always your own", async () => {
    const { findAllByRole } = render(Page);

    const jsonButtons = await findAllByRole("button", { name: /JSON/ });
    await fireEvent.click(jsonButtons[1]);

    await waitFor(() =>
      expect(apiRequest).toHaveBeenLastCalledWith(
        "/export/collections?format=json",
        { responseType: "blob" },
      ),
    );
  });
});
