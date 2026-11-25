/**
 * The "confirm your email" notice and its resend button.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent } from "@testing-library/svelte/svelte5";
import type { Writable } from "svelte/store";

vi.mock("#lib/stores/auth.js", async () => {
  const { writable } = await import("svelte/store");
  return { auth: writable({ user: null }) };
});
vi.mock("#lib/api/users.js", () => ({ resendVerification: vi.fn() }));

import VerifyEmailNotice from "./VerifyEmailNotice.svelte";
import { auth } from "#lib/stores/auth.js";
import { resendVerification } from "#lib/api/users.js";

const signIn = (is_verified: boolean) =>
  (auth as unknown as Writable<unknown>).set({
    user: { id: 1, email: "sam@example.com", display_name: "Sam", is_verified },
  });

describe("VerifyEmailNotice", () => {
  beforeEach(() => {
    vi.mocked(resendVerification).mockReset().mockResolvedValue();
  });

  it("stays hidden for a verified user", () => {
    signIn(true);
    const { queryByRole } = render(VerifyEmailNotice);

    expect(queryByRole("status")).toBeNull();
  });

  it("sends the link again for an unverified user", async () => {
    signIn(false);
    const { getByRole, findByText } = render(VerifyEmailNotice);

    await fireEvent.click(getByRole("button", { name: "Send it again" }));

    expect(resendVerification).toHaveBeenCalledWith("sam@example.com");
    await findByText(/Check sam@example.com/);
  });
});
