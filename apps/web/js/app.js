/**
 * App module — main entry point and orchestrator.
 * Initializes filters, loads data, and wires up interactions.
 */
(function () {
  'use strict';

  // Mobile sidebar toggle elements
  const mobileToggle = document.getElementById('mobile-filter-toggle');
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('filter-overlay');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (mobileToggle) {
    mobileToggle.addEventListener('click', openSidebar);
  }
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // Close filter panel or modal on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      // Modal takes priority
      const modal = document.getElementById('event-modal');
      if (modal && modal.classList.contains('active')) {
        Card.closeModal();
        return;
      }
      closeSidebar();
    }
  });

  // Modal: overlay click to close
  const eventModal = document.getElementById('event-modal');
  if (eventModal) {
    eventModal.addEventListener('click', (e) => {
      // Only close when clicking the overlay itself, not the modal content
      if (e.target === eventModal) {
        Card.closeModal();
      }
    });

    // Modal: close button
    const modalClose = eventModal.querySelector('.modal__close');
    if (modalClose) {
      modalClose.addEventListener('click', () => Card.closeModal());
    }
  }

  /**
   * Main initialization.
   */
  document.addEventListener('DOMContentLoaded', async () => {
    // 1. Show skeleton loading immediately
    Timeline.showSkeletons();

    try {
      // 2. Load products + tags metadata in parallel
      const [productsRes, tagsRes] = await Promise.all([
        API.getProducts(),
        API.getTags(),
      ]);

      const products = Array.isArray(productsRes) ? productsRes : (productsRes.products || []);
      const tags = Array.isArray(tagsRes) ? tagsRes : (tagsRes.tags || []);

      // 3. Initialize filters with metadata
      Filters.init(products, tags);

      // 4. Restore filter state from URL
      Filters.restoreFromURL();

      // 5. Register filter change handler
      Filters.onFilterChange(() => {
        Timeline.reset();
      });

      // 6. Load initial events
      await Timeline.loadEvents(false);

      // 7. Setup infinite scroll
      Timeline.setupInfiniteScroll();

    } catch (err) {
      console.error('[App] Initialization failed:', err);

      // If metadata load fails, still try to show timeline with defaults
      try {
        Filters.init([], []);
        await Timeline.loadEvents(false);
        Timeline.setupInfiniteScroll();
      } catch (innerErr) {
        // Timeline.loadEvents will handle showing error state
        console.error('[App] Fallback also failed:', innerErr);
      }
    }
  });
})();
