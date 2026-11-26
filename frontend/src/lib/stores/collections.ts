/**
 * Collections store - manages user's recipe collections
 */

import { writable } from "svelte/store";
import type { CollectionWithCount } from "#lib/api/collections.js";
import { getCollections } from "#lib/api/collections.js";

interface CollectionsState {
  collections: CollectionWithCount[];
  loading: boolean;
  loaded: boolean;
  error: string | null;
}

function createCollectionsStore() {
  const { subscribe, set, update } = writable<CollectionsState>({
    collections: [],
    loading: false,
    loaded: false,
    error: null,
  });

  return {
    subscribe,

    /**
     * Load all collections from the API
     */
    async load() {
      // "loading" swaps the sidebar for a spinner, so it is only for the first
      // load. A reload (to refresh the counts) keeps the list on screen.
      update((state) => ({ ...state, loading: !state.loaded, error: null }));

      try {
        const collections = await getCollections();
        set({
          collections,
          loading: false,
          loaded: true,
          error: null,
        });
      } catch (err) {
        const error =
          err instanceof Error ? err.message : "Failed to load collections";
        update((state) => ({ ...state, loading: false, error }));
        console.error("Failed to load collections:", err);
      }
    },

    /**
     * Add a collection to the store
     */
    add(collection: CollectionWithCount) {
      update((state) => ({
        ...state,
        collections: [...state.collections, collection],
      }));
    },

    /**
     * Update a collection in the store
     */
    updateCollection(id: number, updates: Partial<CollectionWithCount>) {
      update((state) => ({
        ...state,
        collections: state.collections.map((c) =>
          c.id === id ? { ...c, ...updates } : c,
        ),
      }));
    },

    /**
     * Remove a collection from the store
     */
    remove(id: number) {
      update((state) => ({
        ...state,
        collections: state.collections.filter((c) => c.id !== id),
      }));
    },

    /**
     * Clear the store
     */
    clear() {
      set({
        collections: [],
        loading: false,
        loaded: false,
        error: null,
      });
    },
  };
}

export const collections = createCollectionsStore();
