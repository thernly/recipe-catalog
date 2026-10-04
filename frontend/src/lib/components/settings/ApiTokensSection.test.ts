/**
 * Tests for the API tokens settings section
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/svelte/svelte5";
import { get } from "svelte/store";

vi.mock("$lib/api/api-tokens", () => ({
  listApiTokens: vi.fn(),
  createApiToken: vi.fn(),
  revokeApiToken: vi.fn(),
}));

import ApiTokensSection from "./ApiTokensSection.svelte";
import {
  listApiTokens,
  createApiToken,
  revokeApiToken,
} from "$lib/api/api-tokens";
import { dialog } from "$lib/stores/dialog";

const existing = {
  id: 1,
  name: "Old laptop",
  token_prefix: "rcat_oldtok",
  created_at: "2026-09-01T00:00:00Z",
  last_used_at: null,
};

describe("ApiTokensSection", () => {
  beforeEach(() => {
    vi.mocked(listApiTokens).mockReset();
    vi.mocked(createApiToken).mockReset();
    vi.mocked(revokeApiToken).mockReset();
    dialog.close();
  });

  it("lists active tokens without their values", async () => {
    vi.mocked(listApiTokens).mockResolvedValue([existing]);

    const { findByText, getByText } = render(ApiTokensSection);

    expect(await findByText("Old laptop")).toBeTruthy();
    expect(getByText(/rcat_oldtok/)).toBeTruthy();
    expect(getByText(/Never used/)).toBeTruthy();
  });

  it("shows an empty state", async () => {
    vi.mocked(listApiTokens).mockResolvedValue([]);

    const { findByText } = render(ApiTokensSection);

    expect(await findByText("No active tokens")).toBeTruthy();
  });

  it("requires a name before creating", async () => {
    vi.mocked(listApiTokens).mockResolvedValue([]);

    const { getByRole, findByText } = render(ApiTokensSection);
    await fireEvent.click(getByRole("button", { name: "Create token" }));

    expect(await findByText(/Give the token a name/)).toBeTruthy();
    expect(createApiToken).not.toHaveBeenCalled();
  });

  it("creates a token and shows its value once", async () => {
    const created = {
      ...existing,
      id: 2,
      name: "Firefox",
      token_prefix: "rcat_newtok",
      token: "rcat_newtok-full-secret-value",
    };
    vi.mocked(listApiTokens)
      .mockResolvedValueOnce([])
      .mockResolvedValue([{ ...created, token: undefined } as never]);
    vi.mocked(createApiToken).mockResolvedValue(created);

    const {
      getByLabelText,
      getByRole,
      findByLabelText,
      getByText,
      queryByLabelText,
    } = render(ApiTokensSection);

    await fireEvent.input(getByLabelText("Token name"), {
      target: { value: "  Firefox  " },
    });
    await fireEvent.click(getByRole("button", { name: "Create token" }));

    expect(createApiToken).toHaveBeenCalledWith("Firefox");
    const tokenField = (await findByLabelText(
      "New API token",
    )) as HTMLInputElement;
    expect(tokenField.value).toBe("rcat_newtok-full-secret-value");
    expect(getByText(/will not be shown again/)).toBeTruthy();

    // Dismissing hides the value for good
    await fireEvent.click(getByRole("button", { name: "Done" }));
    expect(queryByLabelText("New API token")).toBeNull();
  });

  it("shows the server's error when creation fails", async () => {
    vi.mocked(listApiTokens).mockResolvedValue([]);
    vi.mocked(createApiToken).mockRejectedValue(
      new Error("You can have at most 20 active API tokens."),
    );

    const { getByLabelText, getByRole, findByText } = render(ApiTokensSection);
    await fireEvent.input(getByLabelText("Token name"), {
      target: { value: "One too many" },
    });
    await fireEvent.click(getByRole("button", { name: "Create token" }));

    expect(await findByText(/at most 20 active API tokens/)).toBeTruthy();
  });

  it("revokes a token after confirmation", async () => {
    vi.mocked(listApiTokens)
      .mockResolvedValueOnce([existing])
      .mockResolvedValue([]);
    vi.mocked(revokeApiToken).mockResolvedValue();

    const { findByRole, findByText } = render(ApiTokensSection);
    await fireEvent.click(await findByRole("button", { name: "Revoke" }));

    // Nothing happens until the dialog is confirmed
    const state = get(dialog);
    expect(state.open).toBe(true);
    expect(state.message).toContain("Old laptop");
    expect(revokeApiToken).not.toHaveBeenCalled();

    await state.onConfirm();

    await waitFor(() => expect(revokeApiToken).toHaveBeenCalledWith(1));
    expect(await findByText("No active tokens")).toBeTruthy();
  });
});
