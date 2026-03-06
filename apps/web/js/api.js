/**
 * API module — wraps all fetch calls to the backend.
 */
const API = (() => {
  'use strict';

  const BASE = '';  // relative path (same-origin, served via FastAPI static mount)

  /**
   * Generic fetch wrapper with error handling.
   * @param {string} endpoint - API path (e.g. '/api/events')
   * @param {object} options  - fetch options
   * @returns {Promise<any>}
   */
  async function request(endpoint, options = {}) {
    const url = `${BASE}${endpoint}`;
    try {
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      if (!res.ok) {
        const errorBody = await res.text().catch(() => '');
        throw new Error(`HTTP ${res.status}: ${errorBody || res.statusText}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`[API] ${options.method || 'GET'} ${url} failed:`, err);
      throw err;
    }
  }

  /**
   * Build query string from an object (skip null/undefined/empty values).
   * @param {object} params
   * @returns {string}
   */
  function toQuery(params) {
    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value === null || value === undefined || value === '') continue;
      if (Array.isArray(value)) {
        if (value.length > 0) qs.set(key, value.join(','));
      } else {
        qs.set(key, String(value));
      }
    }
    const str = qs.toString();
    return str ? `?${str}` : '';
  }

  return {
    /**
     * GET /api/events — list events with optional filters.
     * @param {object} params - { product, tag, severity_min, year, offset, limit }
     * @returns {Promise<{total:number, offset:number, limit:number, items:Array}>}
     */
    async getEvents(params = {}) {
      const query = toQuery(params);
      return request(`/api/events${query}`);
    },

    /**
     * GET /api/events/{id} — single event detail.
     * @param {string} id
     * @returns {Promise<object>}
     */
    async getEventDetail(id) {
      return request(`/api/events/${encodeURIComponent(id)}`);
    },

    /**
     * GET /api/products — product metadata for filter UI.
     * @returns {Promise<{products:Array}>}
     */
    async getProducts() {
      return request('/api/products');
    },

    /**
     * GET /api/tags — tag metadata for filter UI.
     * @returns {Promise<{tags:Array}>}
     */
    async getTags() {
      return request('/api/tags');
    },
  };
})();
