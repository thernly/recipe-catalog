/**
 * Tests for collections store
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { collections } from './collections';
import type { CollectionWithCount } from '$lib/api/collections';

// Mock the API module
vi.mock('$lib/api/collections', () => ({
	getCollections: vi.fn()
}));

import { getCollections } from '$lib/api/collections';

describe('Collections Store', () => {
	beforeEach(() => {
		// Reset mocks and store before each test
		vi.resetAllMocks();
		collections.clear();
	});

	it('should initialize with empty state', () => {
		const state = get(collections);

		expect(state.collections).toEqual([]);
		expect(state.loading).toBe(false);
		expect(state.loaded).toBe(false);
		expect(state.error).toBeNull();
	});

	it('should load collections successfully', async () => {
		const mockCollections: CollectionWithCount[] = [
			{
				id: 1,
				user_id: 1,
				name: 'Favorites',
				description: 'My favorite recipes',
				is_default: false,
				created_at: '2024-01-01T00:00:00Z',
				updated_at: '2024-01-01T00:00:00Z',
				recipe_count: 5
			},
			{
				id: 2,
				user_id: 1,
				name: 'Desserts',
				description: 'Sweet treats',
				is_default: false,
				created_at: '2024-01-02T00:00:00Z',
				updated_at: '2024-01-02T00:00:00Z',
				recipe_count: 3
			}
		];

		(getCollections as any).mockResolvedValue(mockCollections);

		await collections.load();

		const state = get(collections);
		expect(state.collections).toEqual(mockCollections);
		expect(state.loading).toBe(false);
		expect(state.loaded).toBe(true);
		expect(state.error).toBeNull();
	});

	it('should set loading state while loading', async () => {
		(getCollections as any).mockImplementation(
			() =>
				new Promise((resolve) => {
					setTimeout(() => resolve([]), 100);
				})
		);

		const loadPromise = collections.load();

		// Check loading state immediately
		const loadingState = get(collections);
		expect(loadingState.loading).toBe(true);

		await loadPromise;

		// Check state after loading
		const loadedState = get(collections);
		expect(loadedState.loading).toBe(false);
		expect(loadedState.loaded).toBe(true);
	});

	it('should handle load error', async () => {
		const errorMessage = 'Failed to fetch collections';
		(getCollections as any).mockRejectedValue(new Error(errorMessage));

		await collections.load();

		const state = get(collections);
		expect(state.collections).toEqual([]);
		expect(state.loading).toBe(false);
		expect(state.loaded).toBe(false);
		expect(state.error).toBe(errorMessage);
	});

	it('should handle non-Error exceptions', async () => {
		(getCollections as any).mockRejectedValue('String error');

		await collections.load();

		const state = get(collections);
		expect(state.error).toBe('Failed to load collections');
	});

	it('should add a collection', () => {
		const newCollection: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'New Collection',
			description: 'A new collection',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 0
		};

		collections.add(newCollection);

		const state = get(collections);
		expect(state.collections).toHaveLength(1);
		expect(state.collections[0]).toEqual(newCollection);
	});

	it('should add multiple collections', () => {
		const collection1: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'Collection 1',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 0
		};

		const collection2: CollectionWithCount = {
			id: 2,
			user_id: 1,
			name: 'Collection 2',
			is_default: false,
			created_at: '2024-01-02T00:00:00Z',
			updated_at: '2024-01-02T00:00:00Z',
			recipe_count: 0
		};

		collections.add(collection1);
		collections.add(collection2);

		const state = get(collections);
		expect(state.collections).toHaveLength(2);
		expect(state.collections[0]).toEqual(collection1);
		expect(state.collections[1]).toEqual(collection2);
	});

	it('should update a collection', () => {
		const initialCollection: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'Original Name',
			description: 'Original description',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 5
		};

		collections.add(initialCollection);

		collections.updateCollection(1, {
			name: 'Updated Name',
			description: 'Updated description',
			recipe_count: 10
		});

		const state = get(collections);
		expect(state.collections[0].name).toBe('Updated Name');
		expect(state.collections[0].description).toBe('Updated description');
		expect(state.collections[0].recipe_count).toBe(10);
	});

	it('should update only specified fields', () => {
		const initialCollection: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'Original Name',
			description: 'Original description',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 5
		};

		collections.add(initialCollection);

		collections.updateCollection(1, { name: 'New Name' });

		const state = get(collections);
		expect(state.collections[0].name).toBe('New Name');
		expect(state.collections[0].description).toBe('Original description');
		expect(state.collections[0].recipe_count).toBe(5);
	});

	it('should not update non-existent collection', () => {
		const collection: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'Collection',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 0
		};

		collections.add(collection);

		collections.updateCollection(999, { name: 'Updated' });

		const state = get(collections);
		expect(state.collections[0].name).toBe('Collection');
	});

	it('should remove a collection', () => {
		const collection1: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'Collection 1',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 0
		};

		const collection2: CollectionWithCount = {
			id: 2,
			user_id: 1,
			name: 'Collection 2',
			is_default: false,
			created_at: '2024-01-02T00:00:00Z',
			updated_at: '2024-01-02T00:00:00Z',
			recipe_count: 0
		};

		collections.add(collection1);
		collections.add(collection2);

		collections.remove(1);

		const state = get(collections);
		expect(state.collections).toHaveLength(1);
		expect(state.collections[0].id).toBe(2);
	});

	it('should do nothing when removing non-existent collection', () => {
		const collection: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'Collection',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 0
		};

		collections.add(collection);

		collections.remove(999);

		const state = get(collections);
		expect(state.collections).toHaveLength(1);
	});

	it('should clear the store', () => {
		const collection: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'Collection',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 5
		};

		collections.add(collection);

		collections.clear();

		const state = get(collections);
		expect(state.collections).toEqual([]);
		expect(state.loading).toBe(false);
		expect(state.loaded).toBe(false);
		expect(state.error).toBeNull();
	});

	it('should maintain state across multiple operations', () => {
		// Add collections
		collections.add({
			id: 1,
			user_id: 1,
			name: 'Collection 1',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 0
		});

		collections.add({
			id: 2,
			user_id: 1,
			name: 'Collection 2',
			is_default: false,
			created_at: '2024-01-02T00:00:00Z',
			updated_at: '2024-01-02T00:00:00Z',
			recipe_count: 0
		});

		// Update one
		collections.updateCollection(1, { name: 'Updated Collection 1' });

		// Remove one
		collections.remove(2);

		// Add another
		collections.add({
			id: 3,
			user_id: 1,
			name: 'Collection 3',
			is_default: false,
			created_at: '2024-01-03T00:00:00Z',
			updated_at: '2024-01-03T00:00:00Z',
			recipe_count: 0
		});

		const state = get(collections);
		expect(state.collections).toHaveLength(2);
		expect(state.collections[0].name).toBe('Updated Collection 1');
		expect(state.collections[1].name).toBe('Collection 3');
	});

	it('should handle concurrent operations', () => {
		const collection1: CollectionWithCount = {
			id: 1,
			user_id: 1,
			name: 'Collection 1',
			is_default: false,
			created_at: '2024-01-01T00:00:00Z',
			updated_at: '2024-01-01T00:00:00Z',
			recipe_count: 0
		};

		const collection2: CollectionWithCount = {
			id: 2,
			user_id: 1,
			name: 'Collection 2',
			is_default: false,
			created_at: '2024-01-02T00:00:00Z',
			updated_at: '2024-01-02T00:00:00Z',
			recipe_count: 0
		};

		// Add and update in quick succession
		collections.add(collection1);
		collections.updateCollection(1, { name: 'Updated' });
		collections.add(collection2);

		const state = get(collections);
		expect(state.collections).toHaveLength(2);
		expect(state.collections[0].name).toBe('Updated');
		expect(state.collections[1].name).toBe('Collection 2');
	});
});
