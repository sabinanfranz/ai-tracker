/**
 * Timeline module — handles multi-rail event rendering, month rows,
 * infinite scroll, and year jump controls.
 */
const Timeline = (() => {
  'use strict';

  // Product rail order (must match rail-header in HTML)
  const PRODUCTS = ['chatgpt', 'gemini', 'codex', 'claude_code'];

  // State
  let currentOffset = 0;
  const PAGE_SIZE = 50;
  let totalEvents = 0;
  let isLoading = false;
  let lastRenderedMonth = null;
  let allYears = new Set();
  let observer = null;

  // DOM references
  const timelineEl = document.getElementById('timeline');
  const loaderEl = document.getElementById('loader');
  const endMessageEl = document.getElementById('end-message');
  const emptyStateEl = document.getElementById('empty-state');
  const errorStateEl = document.getElementById('error-state');
  const errorMessageEl = document.getElementById('error-message');
  const resetFiltersBtn = document.getElementById('reset-filters');
  const retryBtn = document.getElementById('retry-btn');
  const jumpControlsEl = document.getElementById('jump-controls');

  /**
   * Group events by date.
   * @param {Array} events
   * @returns {Map<string, Array>} ordered Map of date -> events
   */
  /**
   * Get week key from a date string "YYYY-MM-DD" → "MM-NW" (e.g. "03-1W").
   */
  function getWeekKey(dateStr) {
    if (!dateStr) return '';
    const day = parseInt(dateStr.substring(8, 10), 10);
    const month = dateStr.substring(5, 7);
    const weekNum = Math.ceil(day / 7);
    return `${month}-${weekNum}W`;
  }

  /**
   * Group events by week.
   */
  function groupByDate(events) {
    const map = new Map();
    events.forEach(evt => {
      const d = evt.event_date || '';
      const weekKey = getWeekKey(d);
      const fullKey = d ? d.substring(0, 7) + '-' + weekKey : '';
      if (!map.has(fullKey)) map.set(fullKey, { weekLabel: weekKey, yearMonth: d.substring(0, 7), events: [] });
      map.get(fullKey).events.push(evt);
    });
    return map;
  }

  /**
   * Show skeleton loading placeholders (multi-rail version).
   */
  function showSkeletons() {
    if (!timelineEl) return;
    timelineEl.innerHTML = '';

    // Create a skeleton month row
    const skelMonth = document.createElement('div');
    skelMonth.className = 'month-row';
    skelMonth.setAttribute('aria-hidden', 'true');
    skelMonth.innerHTML = '<div class="month-row__label" style="opacity:0.4">불러오는 중...</div>';
    timelineEl.appendChild(skelMonth);

    // Create 3 skeleton date rows
    for (let i = 0; i < 3; i++) {
      const row = document.createElement('div');
      row.className = 'date-row';
      row.setAttribute('aria-hidden', 'true');

      // Date cell
      const dateCell = document.createElement('div');
      dateCell.className = 'date-cell';
      dateCell.innerHTML = '<div class="skeleton-line skeleton-line--short" style="width:50px;margin:0 0 0 auto"></div>';
      row.appendChild(dateCell);

      // 4 rail cells with random skeleton cards
      PRODUCTS.forEach((_, idx) => {
        const cell = document.createElement('div');
        cell.className = 'rail-cell';
        // Put skeleton cards in some cells randomly
        if ((i + idx) % 2 === 0) {
          cell.appendChild(Card.createSkeletonCard());
        }
        row.appendChild(cell);
      });

      timelineEl.appendChild(row);
    }
  }

  /**
   * Remove all skeleton elements.
   */
  function removeSkeletons() {
    if (!timelineEl) return;
    timelineEl.querySelectorAll('.skeleton-card, .skeleton-divider, [aria-hidden="true"]').forEach(el => el.remove());
  }

  /**
   * Hide all state displays.
   */
  function hideAllStates() {
    if (loaderEl) loaderEl.style.display = 'none';
    if (endMessageEl) endMessageEl.style.display = 'none';
    if (emptyStateEl) emptyStateEl.style.display = 'none';
    if (errorStateEl) errorStateEl.style.display = 'none';
  }

  /**
   * Show the empty state.
   */
  function showEmpty() {
    hideAllStates();
    if (emptyStateEl) emptyStateEl.style.display = '';
  }

  /**
   * Show the error state.
   * @param {string} message
   */
  function showError(message) {
    hideAllStates();
    if (errorMessageEl) errorMessageEl.textContent = message || '타임라인 데이터를 불러오지 못했습니다.';
    if (errorStateEl) errorStateEl.style.display = '';
  }

  /**
   * Show the end-of-list message.
   */
  function showEnd() {
    if (loaderEl) loaderEl.style.display = 'none';
    if (endMessageEl) endMessageEl.style.display = '';
  }

  /**
   * Load events from API and render them.
   * @param {boolean} append - true to append, false to replace
   */
  async function loadEvents(append = false) {
    if (isLoading) return;
    isLoading = true;

    if (!append) {
      currentOffset = 0;
      lastRenderedMonth = null;
      allYears = new Set();
      hideAllStates();
      showSkeletons();
    } else {
      if (loaderEl) loaderEl.style.display = '';
    }

    try {
      const filterParams = Filters.getQueryParams();
      const params = {
        ...filterParams,
        offset: currentOffset,
        limit: PAGE_SIZE,
      };

      const data = await API.getEvents(params);
      totalEvents = data.total;

      if (!append) {
        removeSkeletons();
        timelineEl.innerHTML = '';
      } else {
        if (loaderEl) loaderEl.style.display = 'none';
      }

      if (data.items.length === 0 && currentOffset === 0) {
        showEmpty();
        isLoading = false;
        return;
      }

      renderEvents(data.items, append);
      currentOffset += data.items.length;

      // Check if we've loaded everything
      if (currentOffset >= totalEvents) {
        showEnd();
        disconnectObserver();
      }

      // Update year jump controls
      setupYearJump();

    } catch (err) {
      if (!append) {
        removeSkeletons();
        timelineEl.innerHTML = '';
      } else {
        if (loaderEl) loaderEl.style.display = 'none';
      }
      showError(err.message);
    } finally {
      isLoading = false;
    }
  }

  /**
   * Render events into multi-rail date-row grid.
   * Events are grouped by date, then each date gets a row with 5 cells.
   * @param {Array} events
   * @param {boolean} append
   */
  function renderEvents(events, append) {
    if (!timelineEl) return;

    const weekGroups = groupByDate(events);

    for (const [key, group] of weekGroups) {
      const yearMonth = group.yearMonth || '';
      const year = yearMonth ? yearMonth.substring(0, 4) : '';

      if (year) allYears.add(year);

      // Insert month row if month changed
      if (yearMonth && yearMonth !== lastRenderedMonth) {
        timelineEl.appendChild(createMonthRow(yearMonth));
        lastRenderedMonth = yearMonth;
      }

      // Create week row
      timelineEl.appendChild(createDateRow(group.weekLabel, group.events));
    }
  }

  /**
   * Create a month row element (replaces old month-divider).
   * @param {string} yearMonth - "YYYY-MM"
   * @returns {HTMLElement}
   */
  function createMonthRow(yearMonth) {
    const [year, month] = yearMonth.split('-');
    const monthNames = [
      '1\uC6D4', '2\uC6D4', '3\uC6D4', '4\uC6D4', '5\uC6D4', '6\uC6D4',
      '7\uC6D4', '8\uC6D4', '9\uC6D4', '10\uC6D4', '11\uC6D4', '12\uC6D4',
    ];
    const monthIdx = parseInt(month, 10) - 1;
    const label = `${year}\uB144 ${monthNames[monthIdx] || month + '\uC6D4'}`;

    const div = document.createElement('div');
    div.className = 'month-row';
    div.id = `month-${yearMonth}`;
    div.dataset.year = year;
    div.innerHTML = `<div class="month-row__label">${label}</div>`;
    return div;
  }

  /**
   * Create a week row with 5 cells: date-cell + 4 rail-cells.
   * @param {string} weekLabel - "MM-NW" (e.g. "03-1W")
   * @param {Array} events - events for this week
   * @returns {HTMLElement}
   */
  function createDateRow(weekLabel, events) {
    const row = document.createElement('div');
    row.className = 'date-row';
    row.dataset.date = weekLabel;

    // Date axis cell (show week label like "03-1W")
    const dateCell = document.createElement('div');
    dateCell.className = 'date-cell';
    dateCell.textContent = weekLabel;
    row.appendChild(dateCell);

    // Group events by product
    const eventsByProduct = {};
    events.forEach(e => {
      const p = e.product || 'unknown';
      if (!eventsByProduct[p]) eventsByProduct[p] = [];
      eventsByProduct[p].push(e);
    });

    // Create 4 rail cells in fixed order
    PRODUCTS.forEach(productId => {
      const cell = document.createElement('div');
      cell.className = 'rail-cell';
      cell.dataset.product = productId;

      const productEvents = eventsByProduct[productId] || [];
      productEvents.forEach(evt => {
        cell.appendChild(Card.createEventCard(evt));
      });

      row.appendChild(cell);
    });

    return row;
  }

  /**
   * Set up IntersectionObserver for infinite scroll.
   */
  function setupInfiniteScroll() {
    if (!loaderEl) return;

    // Create a sentinel element at the bottom
    const sentinel = document.createElement('div');
    sentinel.id = 'scroll-sentinel';
    sentinel.style.height = '1px';
    loaderEl.parentElement.insertBefore(sentinel, loaderEl);

    observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !isLoading && currentOffset < totalEvents) {
          loadEvents(true);
        }
      });
    }, {
      rootMargin: '300px',
    });

    observer.observe(sentinel);
  }

  /**
   * Disconnect the infinite scroll observer.
   */
  function disconnectObserver() {
    if (observer) {
      const sentinel = document.getElementById('scroll-sentinel');
      if (sentinel) observer.unobserve(sentinel);
    }
  }

  /**
   * Reconnect the infinite scroll observer.
   */
  function reconnectObserver() {
    if (observer) {
      const sentinel = document.getElementById('scroll-sentinel');
      if (sentinel) observer.observe(sentinel);
    }
  }

  /**
   * Set up year jump buttons.
   */
  function setupYearJump() {
    if (!jumpControlsEl) return;
    jumpControlsEl.innerHTML = '';

    // "Latest" button
    const latestBtn = document.createElement('button');
    latestBtn.className = 'jump-btn';
    latestBtn.textContent = '최신';
    latestBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    jumpControlsEl.appendChild(latestBtn);

    // Year buttons (sorted descending)
    const years = Array.from(allYears).sort((a, b) => b.localeCompare(a));
    years.forEach(year => {
      const btn = document.createElement('button');
      btn.className = 'jump-btn';
      btn.textContent = year;
      btn.addEventListener('click', () => {
        jumpToYear(year);
      });
      jumpControlsEl.appendChild(btn);
    });

    // Refresh button
    const refreshBtn = document.createElement('button');
    refreshBtn.className = 'jump-btn jump-btn--refresh';
    refreshBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 4 23 10 17 10"></polyline>
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
      </svg>
      새로고침
    `;
    refreshBtn.addEventListener('click', () => {
      refreshTimeline(refreshBtn);
    });
    jumpControlsEl.appendChild(refreshBtn);
  }

  /**
   * Jump to the first month row of a given year.
   * @param {string} year
   */
  function jumpToYear(year) {
    const monthRows = timelineEl.querySelectorAll(`.month-row[data-year="${year}"]`);
    if (monthRows.length > 0) {
      const target = monthRows[0];
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // Flash highlight
      setTimeout(() => {
        target.classList.add('highlight-flash');
        setTimeout(() => target.classList.remove('highlight-flash'), 800);
      }, 500);
    }
  }

  /**
   * Refresh timeline data.
   * @param {HTMLElement} btn
   */
  async function refreshTimeline(btn) {
    if (btn.disabled) return;
    btn.disabled = true;
    btn.classList.add('loading');

    reconnectObserver();
    await loadEvents(false);

    btn.classList.remove('loading');
    btn.disabled = false;
  }

  /**
   * Full reset — clear timeline and reload.
   */
  async function reset() {
    hideAllStates();
    reconnectObserver();
    await loadEvents(false);
  }

  // Bind reset filters button
  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', () => {
      Filters.resetAll();
    });
  }

  // Bind retry button
  if (retryBtn) {
    retryBtn.addEventListener('click', () => {
      reset();
    });
  }

  return {
    loadEvents,
    renderEvents,
    createMonthRow,
    setupInfiniteScroll,
    setupYearJump,
    reset,
    showSkeletons,
  };
})();
