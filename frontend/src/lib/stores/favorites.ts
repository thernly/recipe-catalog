/**
 * Favorites: membership of the signed-in user's default "Favorites" collection.
 * Loaded once per user; the star on recipe cards and the recipe page reads it.
 */
import { get, writable } from "svelte/store";
import {
  addRecipesToCollection,
  getCollectionRecipes,
  getCollections,
  removeRecipesFromCollection,
} from "#lib/api/collections.js";
import { auth } from "#lib/stores/auth.js";
import { toast } from "#lib/stores/toast.js";

interface FavoritesState {
  collectionId: number | null;
  ids: Set<number>;
}

const empty = (): FavoritesState => ({ collectionId: null, ids: new Set() });

function createFavoritesStore() {
  const { subscribe, set, update } = writable<FavoritesState>(empty());
  let loadedFor: number | null = null;

  async function load(userId: number) {
    try {
      const collections = await getCollections();
      const favorites = collections.find(
        (c) => c.is_default && c.user_id === userId,
      );
      if (!favorites || loadedFor !== userId) return;
      const recipes = await getCollectionRecipes(favorites.id);
      if (loadedFor !== userId) return;
      set({
        collectionId: favorites.id,
        ids: new Set(recipes.map((r) => r.id)),
      });
    } catch (err) {
      // Stars stay empty; toggling reports the problem
      console.error("Failed to load favorites:", err);
    }
  }

  // Follow the signed-in user: load on sign-in, forget on sign-out
  auth.subscribe(({ user }) => {
    const userId = user?.id ?? null;
    if (userId === loadedFor) return;
    loadedFor = userId;
    set(empty());
    if (userId !== null) void load(userId);
  });

  function mark(recipeId: number, favorite: boolean) {
    update((state) => {
      const ids = new Set(state.ids);
      if (favorite) ids.add(recipeId);
      else ids.delete(recipeId);
      return { ...state, ids };
    });
  }

  return {
    subscribe,

    /** Add or remove a recipe; the star changes at once and reverts on failure. */
    async toggle(recipeId: number): Promise<void> {
      const { collectionId, ids } = get({ subscribe });
      if (collectionId === null) {
        toast.error("Favorites are not available right now");
        return;
      }
      const favorite = !ids.has(recipeId);
      mark(recipeId, favorite);
      try {
        if (favorite) await addRecipesToCollection(collectionId, [recipeId]);
        else await removeRecipesFromCollection(collectionId, [recipeId]);
      } catch (err) {
        mark(recipeId, !favorite);
        toast.error("Could not update favorites");
        console.error("Failed to update favorites:", err);
      }
    },

    /** Reload after collection membership was changed elsewhere. */
    async refresh(): Promise<void> {
      if (loadedFor !== null) await load(loadedFor);
    },
  };
}

export const favorites = createFavoritesStore();
