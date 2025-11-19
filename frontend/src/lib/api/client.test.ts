/**
 * Tests for API client
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { buildQueryString, apiRequest } from './client';

describe('buildQueryString', () => {
	it('should build query string from simple params', () => {
		const params = {
			name: 'test',
			page: 1,
			active: true
		};

		const result = buildQueryString(params);

		expect(result).toBe('?name=test&page=1&active=true');
	});

	it('should handle empty params', () => {
		const result = buildQueryString({});

		expect(result).toBe('');
	});

	it('should skip undefined values', () => {
		const params = {
			name: 'test',
			optional: undefined,
			page: 1
		};

		const result = buildQueryString(params);

		expect(result).toBe('?name=test&page=1');
	});

	it('should skip null values', () => {
		const params = {
			name: 'test',
			empty: null,
			page: 1
		};

		const result = buildQueryString(params);

		expect(result).toBe('?name=test&page=1');
	});

	it('should skip empty string values', () => {
		const params = {
			name: 'test',
			empty: '',
			page: 1
		};

		const result = buildQueryString(params);

		expect(result).toBe('?name=test&page=1');
	});

	it('should handle array values', () => {
		const params = {
			tags: ['vegetarian', 'quick'],
			page: 1
		};

		const result = buildQueryString(params);

		expect(result).toContain('tags=vegetarian');
		expect(result).toContain('tags=quick');
		expect(result).toContain('page=1');
	});

	it('should handle mixed types', () => {
		const params = {
			string: 'test',
			number: 42,
			boolean: true,
			array: ['a', 'b']
		};

		const result = buildQueryString(params);

		expect(result).toContain('string=test');
		expect(result).toContain('number=42');
		expect(result).toContain('boolean=true');
		expect(result).toContain('array=a');
		expect(result).toContain('array=b');
	});

	it('should encode special characters', () => {
		const params = {
			search: 'chocolate cake',
			filter: 'dairy-free'
		};

		const result = buildQueryString(params);

		expect(result).toContain('chocolate+cake');
		expect(result).toContain('dairy-free');
	});

	it('should handle zero as valid value', () => {
		const params = {
			page: 0,
			limit: 0
		};

		const result = buildQueryString(params);

		expect(result).toBe('?page=0&limit=0');
	});

	it('should handle false as valid value', () => {
		const params = {
			active: false,
			verified: false
		};

		const result = buildQueryString(params);

		expect(result).toBe('?active=false&verified=false');
	});

	it('should handle empty arrays', () => {
		const params = {
			tags: [],
			name: 'test'
		};

		const result = buildQueryString(params);

		expect(result).toBe('?name=test');
	});

	it('should convert non-string values to strings', () => {
		const params = {
			date: new Date('2024-01-01'),
			obj: { key: 'value' }
		};

		const result = buildQueryString(params);

		// Should convert to string representation
		expect(result).toContain('date=');
		expect(result).toContain('obj=');
	});
});

describe('apiRequest', () => {
	beforeEach(() => {
		// Mock fetch globally
		global.fetch = vi.fn();
		vi.resetAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('should make GET request with default options', async () => {
		const mockData = { id: 1, name: 'Test' };

		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => mockData
		});

		const result = await apiRequest('/api/test');

		expect(global.fetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/test'),
			expect.objectContaining({
				credentials: 'include'
			})
		);
		expect(result).toEqual(mockData);
	});

	it('should make POST request with JSON body', async () => {
		const postData = { name: 'New Item' };
		const mockResponse = { id: 1, ...postData };

		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => mockResponse
		});

		// Mock CSRF token fetch
		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			json: async () => ({ csrf_token: 'test-token' })
		});

		const result = await apiRequest('/api/test', {
			method: 'POST',
			body: JSON.stringify(postData)
		});

		expect(result).toEqual(mockResponse);
	});

	it('should handle 204 No Content response', async () => {
		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			status: 204
		});

		const result = await apiRequest('/api/test', {
			method: 'DELETE'
		});

		expect(result).toEqual({});
	});

	it('should throw error on HTTP error response', async () => {
		(global.fetch as any).mockResolvedValueOnce({
			ok: false,
			status: 400,
			json: async () => ({ detail: 'Bad request' })
		});

		await expect(apiRequest('/api/test')).rejects.toThrow('Bad request');
	});

	it('should include Content-Type header for JSON', async () => {
		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({})
		});

		await apiRequest('/api/test', {
			method: 'POST',
			body: JSON.stringify({ test: 'data' })
		});

		const fetchCall = (global.fetch as any).mock.calls.find(
			(call: any) => call[0].includes('/api/test')
		);

		expect(fetchCall[1].headers['Content-Type']).toBe('application/json');
	});

	it('should not set Content-Type for FormData', async () => {
		const formData = new FormData();
		formData.append('file', new Blob(['test']), 'test.txt');

		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({})
		});

		await apiRequest('/api/test', {
			method: 'POST',
			body: formData
		});

		const fetchCall = (global.fetch as any).mock.calls.find(
			(call: any) => call[0].includes('/api/test')
		);

		expect(fetchCall[1].headers['Content-Type']).toBeUndefined();
	});

	it('should handle network errors', async () => {
		(global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

		await expect(apiRequest('/api/test')).rejects.toThrow('Network error');
	});

	it('should handle response without error detail', async () => {
		(global.fetch as any).mockResolvedValueOnce({
			ok: false,
			status: 500,
			json: async () => ({})
		});

		await expect(apiRequest('/api/test')).rejects.toThrow('HTTP error! status: 500');
	});

	it('should handle response that cannot be parsed as JSON', async () => {
		(global.fetch as any).mockResolvedValueOnce({
			ok: false,
			status: 500,
			json: async () => {
				throw new Error('Invalid JSON');
			}
		});

		await expect(apiRequest('/api/test')).rejects.toThrow('HTTP error! status: 500');
	});

	it('should send credentials with request', async () => {
		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({})
		});

		await apiRequest('/api/test');

		expect(global.fetch).toHaveBeenCalledWith(
			expect.any(String),
			expect.objectContaining({
				credentials: 'include'
			})
		);
	});

	it('should handle custom headers', async () => {
		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({})
		});

		await apiRequest('/api/test', {
			headers: {
				'X-Custom-Header': 'custom-value'
			}
		});

		const fetchCall = (global.fetch as any).mock.calls.find(
			(call: any) => call[0].includes('/api/test')
		);

		expect(fetchCall[1].headers['X-Custom-Header']).toBe('custom-value');
	});

	it('should merge custom headers with default headers', async () => {
		(global.fetch as any).mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({})
		});

		await apiRequest('/api/test', {
			method: 'POST',
			body: JSON.stringify({}),
			headers: {
				'X-Custom': 'value'
			}
		});

		const fetchCall = (global.fetch as any).mock.calls.find(
			(call: any) => call[0].includes('/api/test')
		);

		expect(fetchCall[1].headers['Content-Type']).toBe('application/json');
		expect(fetchCall[1].headers['X-Custom']).toBe('value');
	});
});
