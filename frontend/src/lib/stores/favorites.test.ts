/**
 * Favorites store: loads the user's Favorites collection and toggles membership.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { get, type Writable } from "svelte/store";

vi.mock("#lib/stores/auth.js", async () => {
  const { writable } = await import("svelte/store");
  return { auth: writable({ user: null }) };
});
vi.mock("#lib/api/collections.js", () => ({
  getCollections: vi.fn(),
  getCollectionRecipes: vi.fn(),
  addRecipesToCollection: vi.fn(),
  removeRecipesFromCollection: vi.fn(),
}));

import { favorites } from "./favorites";
import { auth } from "#lib/stores/auth.js";
import {
  addRecipesToCollection,
  getCollectionRecipes,
  getCollections,
  removeRecipesFromCollection,
} from "#lib/api/collections.js";

const setUser = (user: { id: number } | null) =>
  (auth as unknown as Writable<unknown>).set({ user });
const loaded = () =>
  vi.waitFor(() => expect(get(favorites).collectionId).toBe(8));

describe("favorites store", () => {
  beforeEach(async () => {
    setUser(null);
    vi.clearAllMocks();
    vi.mocked(getCollections).mockResolvedValue([
      // Another member's Favorites must not be mistaken for mine
      { id: 7, user_id: 2, is_default: true, name: "Favorites" },
      { id: 8, user_id: 1, is_default: true, name: "Favorites" },
    ] as Awaited<ReturnType<typeof getCollections>>);
    vi.mocked(getCollectionRecipes).mockResolvedValue([{ id: 30 }] as Awaited<
      ReturnType<typeof getCollectionRecipes>
    >);
    vi.mocked(addRecipesToCollection).mockResolvedValue();
    vi.mocked(removeRecipesFromCollection).mockResolvedValue();
  });

  it("loads my Favorites on sign-in and forgets them on sign-out", async () => {
    setUser({ id: 1 });
    await loaded();
    expect(getCollectionRecipes).toHaveBeenCalledWith(8);
    expect([...get(favorites).ids]).toEqual([30]);

    setUser(null);
    expect(get(favorites).ids.size).toBe(0);
  });

  it("adds and removes a recipe", async () => {
    setUser({ id: 1 });
    await loaded();

    await favorites.toggle(31);
    expect(addRecipesToCollection).toHaveBeenCalledWith(8, [31]);
    expect(get(favorites).ids.has(31)).toBe(true);

    await favorites.toggle(30);
    expect(removeRecipesFromCollection).toHaveBeenCalledWith(8, [30]);
    expect(get(favorites).ids.has(30)).toBe(false);
  });

  it("puts the star back when the server refuses", async () => {
    setUser({ id: 1 });
    await loaded();
    vi.mocked(addRecipesToCollection).mockRejectedValue(new Error("nope"));
    vi.spyOn(console, "error").mockImplementation(() => {});

    await favorites.toggle(31);

    expect(get(favorites).ids.has(31)).toBe(false);
  });
});
