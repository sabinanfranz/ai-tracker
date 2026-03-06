/**
 * Filters module — manages product and tag filter state,
 * renders the filter bar, and syncs with URL query params + localStorage.
 */
const Filters = (() => {
  'use strict';

  // localStorage key
  const STORAGE_KEY = 'ai_tracker_filters';

  // Internal state
  const state = {
    products: [],       // selected product IDs (empty = all)
    tags: [],           // selected tag IDs (empty = all)
    year: null,
  };

  // Metadata loaded from API
  let productsData = [];
  let tagsData = [];

  // Debounce timer
  let debounceTimer = null;
  const DEBOUNCE_MS = 250;

  // Change callback
  let onChangeCallback = null;

  // DOM references
  const productFiltersEl = document.getElementById('product-filters');
  const tagFiltersEl = document.getElementById('tag-filters');
  const filterStatusEl = document.getElementById('filter-status');
  const mobileCountEl = document.getElementById('mobile-filter-count');

  /**
   * Initialize the filter bar with product and tag metadata.
   * @param {Array} products - from GET /api/products
   * @param {Array} tags - from GET /api/tags
   */
  function init(products, tags) {
    productsData = products || [];
    tagsData = tags || [];
    // Start with all products active
    if (state.products.length === 0) {
      state.products = productsData.map(p => p.id);
    }
    renderProductToggles();
    renderTagChips();
    updateStatus();
  }

  /**
   * Render product toggle buttons.
   */
  function renderProductToggles() {
    if (!productFiltersEl) return;
    productFiltersEl.innerHTML = '';

    productsData.forEach(product => {
      const btn = document.createElement('button');
      btn.className = 'product-toggle';
      btn.dataset.productId = product.id;
      btn.style.setProperty('--toggle-color', product.color);

      const isActive = state.products.includes(product.id);
      if (isActive) btn.classList.add('active');

      btn.innerHTML = `
        <span class="product-toggle__dot"></span>
        <span>${escapeText(product.label)}</span>
        <span class="product-toggle__count">(${product.event_count})</span>
      `;

      btn.addEventListener('click', () => {
        toggleProduct(product.id);
      });

      productFiltersEl.appendChild(btn);
    });
  }

  /**
   * Render tag chip buttons.
   */
  function renderTagChips() {
    if (!tagFiltersEl) return;
    tagFiltersEl.innerHTML = '';

    tagsData.forEach(tag => {
      const btn = document.createElement('button');
      btn.className = 'tag-chip';
      btn.dataset.tagId = tag.id;

      const isActive = state.tags.includes(tag.id);
      if (isActive) btn.classList.add('active');

      btn.innerHTML = `
        <span>${escapeText(tag.label)}</span>
        <span class="tag-chip__count">(${tag.count})</span>
      `;

      btn.addEventListener('click', () => {
        toggleTag(tag.id);
      });

      tagFiltersEl.appendChild(btn);
    });
  }

  /**
   * Toggle a product filter.
   * @param {string} productId
   */
  function toggleProduct(productId) {
    const idx = state.products.indexOf(productId);
    if (idx >= 0) {
      // Don't allow turning off the last product
      if (state.products.length <= 1) return;
      state.products.splice(idx, 1);
    } else {
      state.products.push(productId);
    }

    updateProductUI();
    debouncedChange();
  }

  /**
   * Toggle a tag filter.
   * @param {string} tagId
   */
  function toggleTag(tagId) {
    const idx = state.tags.indexOf(tagId);
    if (idx >= 0) {
      state.tags.splice(idx, 1);
    } else {
      state.tags.push(tagId);
    }

    updateTagUI();
    debouncedChange();
  }

  /**
   * Update product toggle button visuals.
   */
  function updateProductUI() {
    if (!productFiltersEl) return;
    const buttons = productFiltersEl.querySelectorAll('.product-toggle');
    buttons.forEach(btn => {
      const id = btn.dataset.productId;
      const isActive = state.products.includes(id);
      btn.classList.toggle('active', isActive);
    });
  }

  /**
   * Update tag chip button visuals.
   */
  function updateTagUI() {
    if (!tagFiltersEl) return;
    const chips = tagFiltersEl.querySelectorAll('.tag-chip');
    chips.forEach(chip => {
      const id = chip.dataset.tagId;
      chip.classList.toggle('active', state.tags.includes(id));
    });
  }

  /**
   * Update the filter status text.
   */
  function updateStatus() {
    if (!filterStatusEl) return;

    const prodCount = state.products.length || productsData.length;
    const tagCount = state.tags.length;
    const parts = [];

    if (state.products.length < productsData.length) {
      parts.push(`${state.products.length}개 제품`);
    }
    if (tagCount > 0) {
      parts.push(`${tagCount}개 태그`);
    }
    if (state.year) {
      parts.push(`${state.year}년`);
    }

    filterStatusEl.textContent = parts.length > 0
      ? `필터 적용: ${parts.join(' + ')}`
      : '';

    // Update mobile count badge
    const totalActiveFilters = (state.products.length < productsData.length ? productsData.length - state.products.length : 0) + state.tags.length;
    if (mobileCountEl) {
      if (totalActiveFilters > 0) {
        mobileCountEl.textContent = totalActiveFilters;
        mobileCountEl.style.display = '';
      } else {
        mobileCountEl.style.display = 'none';
      }
    }
  }

  /**
   * Save current filter state to localStorage.
   */
  function saveToStorage() {
    try {
      const data = {
        products: state.products,
        tags: state.tags,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
      // localStorage may be unavailable (e.g. private browsing)
      console.warn('[Filters] Failed to save to localStorage:', e);
    }
  }

  /**
   * Restore filter state from localStorage.
   * Only called if URL has no filter params.
   */
  function restoreFromStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;

      const data = JSON.parse(raw);

      if (Array.isArray(data.products)) {
        state.products = data.products;
      }
      if (Array.isArray(data.tags)) {
        state.tags = data.tags;
      }

      updateProductUI();
      updateTagUI();
      updateStatus();
    } catch (e) {
      console.warn('[Filters] Failed to restore from localStorage:', e);
    }
  }

  /**
   * Clear saved filters from localStorage.
   */
  function clearStorage() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      // ignore
    }
  }

  /**
   * Debounced filter change handler.
   */
  function debouncedChange() {
    updateStatus();
    updateURL();
    saveToStorage();

    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (onChangeCallback) onChangeCallback();
    }, DEBOUNCE_MS);
  }

  /**
   * Get current filter state as query params for API call.
   * @returns {object}
   */
  function getQueryParams() {
    const params = {};
    // Only filter if not all products are active
    if (state.products.length > 0 && state.products.length < productsData.length) {
      params.product = state.products;
    }
    if (state.tags.length > 0) {
      params.tag = state.tags;
    }
    if (state.year) {
      params.year = state.year;
    }
    return params;
  }

  /**
   * Sync current filter state to URL query params (without page reload).
   */
  function updateURL() {
    const url = new URL(window.location);
    url.searchParams.delete('products');
    url.searchParams.delete('tags');
    url.searchParams.delete('year');

    if (state.products.length > 0) {
      url.searchParams.set('products', state.products.join(','));
    }
    if (state.tags.length > 0) {
      url.searchParams.set('tags', state.tags.join(','));
    }
    if (state.year) {
      url.searchParams.set('year', state.year);
    }

    window.history.replaceState(null, '', url.toString());
  }

  /**
   * Restore filter state from URL query params.
   * If URL has no filter params, falls back to localStorage.
   */
  function restoreFromURL() {
    const params = new URLSearchParams(window.location.search);

    // Check if URL has any filter-related params
    const hasURLFilters = params.has('products') || params.has('tags')
      || params.has('year');

    if (hasURLFilters) {
      // URL takes priority
      const products = params.get('products');
      if (products) {
        state.products = products.split(',').filter(Boolean);
      }

      const tags = params.get('tags');
      if (tags) {
        state.tags = tags.split(',').filter(Boolean);
      }

      const year = params.get('year');
      if (year) {
        state.year = parseInt(year, 10) || null;
      }

      updateProductUI();
      updateTagUI();
      updateStatus();
    } else {
      // No URL params — try localStorage
      restoreFromStorage();
    }
  }

  /**
   * Reset all filters to defaults.
   */
  function resetAll() {
    state.products = productsData.map(p => p.id);
    state.tags = [];
    state.year = null;

    updateProductUI();
    updateTagUI();
    updateStatus();
    updateURL();
    clearStorage();

    if (onChangeCallback) onChangeCallback();
  }

  /**
   * Register a callback for filter changes.
   * @param {Function} callback
   */
  function onFilterChange(callback) {
    onChangeCallback = callback;
  }

  /**
   * Set year filter programmatically (used by jump controls).
   * @param {number|null} year
   */
  function setYear(year) {
    state.year = year;
    updateStatus();
    updateURL();
  }

  /**
   * Get current state (read-only copy).
   */
  function getState() {
    return { ...state, products: [...state.products], tags: [...state.tags] };
  }

  /**
   * Simple text escaping.
   */
  function escapeText(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  return {
    state,
    init,
    getQueryParams,
    onFilterChange,
    updateURL,
    restoreFromURL,
    resetAll,
    setYear,
    getState,
  };
})();
