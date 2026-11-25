/** The rule shown to users; mirrors the server's check in backend/app/schemas/user.py. */
export const PASSWORD_HINT =
  "At least 12 characters, with an uppercase letter, a lowercase letter and a number";

/** Returns what is wrong with a new password, or null if it meets the rules. */
export function passwordProblem(password: string): string | null {
  if (password.length < 12)
    return "Password must be at least 12 characters long";
  if (!/[A-Z]/.test(password))
    return "Password must contain at least one uppercase letter";
  if (!/[a-z]/.test(password))
    return "Password must contain at least one lowercase letter";
  if (!/[0-9]/.test(password))
    return "Password must contain at least one number";
  return null;
}
