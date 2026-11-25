import { describe, it, expect } from "vitest";
import { passwordProblem } from "./password";

describe("passwordProblem", () => {
  it("accepts a password that meets the server's rules", () => {
    expect(passwordProblem("SecurePass123")).toBeNull();
  });

  it.each([
    ["Short1Aa", "12 characters"],
    ["alllowercase123", "uppercase"],
    ["ALLUPPERCASE123", "lowercase"],
    ["NoDigitsInHere", "number"],
  ])("rejects %s", (password, reason) => {
    expect(passwordProblem(password)).toContain(reason);
  });
});
