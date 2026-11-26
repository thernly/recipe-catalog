/**
 * The recipe list's address as it was last seen in this tab (search, filters, sort,
 * page). A recipe page reached without a returnUrl, for example after Edit and Save,
 * uses it so "Back to Recipes" returns to the same list.
 */
const KEY = "recipes-list-url";

export function rememberRecipeListUrl(url: string): void {
  try {
    sessionStorage.setItem(KEY, url);
  } catch {
    // Storage blocked: Back to Recipes opens the plain list
  }
}

export function lastRecipeListUrl(): string {
  try {
    const url = sessionStorage.getItem(KEY);
    if (url?.startsWith("/recipes")) return url;
  } catch {
    // Storage blocked
  }
  return "/recipes";
}
