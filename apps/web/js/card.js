/**
 * Card module — dispatcher that delegates to product-specific renderers.
 * Uses CardBase utilities and CardRenderers registry from cards/base.js.
 */
const Card = (() => {
  'use strict';

  const { escapeHtml, formatDateShort, createSkeletonCard, createSkeletonDivider,
          PRODUCT_LABELS, TAG_LABELS, CardRenderers } = CardBase;

  /**
   * Fallback card renderer for unknown products.
   */
  const fallbackRenderer = {
    createCard(event) {
      const article = document.createElement('article');
      article.className = 'event-card';
      article.dataset.product = event.product || '';
      article.dataset.eventId = event.id;
      article.setAttribute('role', 'button');
      article.setAttribute('tabindex', '0');
      const headline = event.title_ko || event.summary_ko || event.title;
      article.setAttribute('aria-label', escapeHtml(headline));

      const productLabel = PRODUCT_LABELS[event.product] || event.product;

      article.innerHTML = `
        <div class="event-card__top">
          <span class="product-badge" data-product="${escapeHtml(event.product)}">${escapeHtml(productLabel)}</span>
        </div>
        <p class="event-card__headline">${escapeHtml(headline)}</p>
        <div class="event-card__bottom">
          <time class="event-card__date" datetime="${escapeHtml(event.event_date)}">${formatDateShort(event.event_date)}</time>
        </div>
      `;
      return article;
    },

    renderModalHeader(headerEl, detail) {
      const productLabel = PRODUCT_LABELS[detail.product] || detail.product;
      const tags = Array.isArray(detail.tags) ? detail.tags : [];
      const tagsHtml = tags.map(t =>
        `<span class="event-tag">${escapeHtml(TAG_LABELS[t] || t)}</span>`
      ).join('');

      headerEl.innerHTML = `
        <div class="modal__title-row">
          <span class="product-badge" data-product="${escapeHtml(detail.product)}">${escapeHtml(productLabel)}</span>
          <span class="modal__title">${escapeHtml(detail.title)}</span>
        </div>
        <div class="modal__meta-row">
          <time datetime="${escapeHtml(detail.event_date)}">${escapeHtml(detail.event_date)}</time>
        </div>
        <div class="modal__tags">${tagsHtml}</div>
      `;
    },

    renderModalBody(bodyEl, detail) {
      bodyEl.innerHTML = '';
      const summaryText = detail.summary_ko || '';
      if (summaryText) {
        const section = CardBase.createModalSection('\uC694\uC57D');
        const p = document.createElement('p');
        p.className = 'modal__text';
        p.textContent = summaryText;
        section.appendChild(p);
        bodyEl.appendChild(section);
      }
      CardBase.renderSourceSection(bodyEl, detail);
    },
  };

  /**
   * Get the renderer for a product, falling back to the default.
   */
  function getRenderer(product) {
    return CardRenderers[product] || fallbackRenderer;
  }

  /**
   * Create a compact event card DOM element.
   * Dispatches to the product-specific renderer.
   */
  function createEventCard(event) {
    const renderer = getRenderer(event.product);
    const article = renderer.createCard(event);

    // Attach click/keyboard handlers
    article.addEventListener('click', () => openModal(event.id));
    article.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openModal(event.id);
      }
    });

    return article;
  }

  /**
   * Open the detail modal for a given event ID.
   */
  async function openModal(eventId) {
    const overlay = document.getElementById('event-modal');
    if (!overlay) return;

    const header = overlay.querySelector('.modal__header');
    const body = overlay.querySelector('.modal__body');

    // Show modal with loading state
    body.innerHTML = `
      <div class="modal__loading">
        <div class="skeleton-line skeleton-line--long"></div>
        <div class="skeleton-line skeleton-line--medium"></div>
        <div class="skeleton-line skeleton-line--short"></div>
      </div>
    `;
    header.innerHTML = '';
    overlay.classList.add('active');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');

    try {
      const detail = await API.getEventDetail(eventId);
      const renderer = getRenderer(detail.product);
      renderer.renderModalHeader(header, detail);
      renderer.renderModalBody(body, detail);
    } catch (err) {
      body.innerHTML = `<p class="modal__error">\uC0C1\uC138 \uC815\uBCF4\uB97C \uBD88\uB7EC\uC624\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.</p>`;
    }
  }

  /**
   * Close the modal.
   */
  function closeModal() {
    const overlay = document.getElementById('event-modal');
    if (!overlay) return;
    overlay.classList.remove('active');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
  }

  return {
    createEventCard,
    openModal,
    closeModal,
    createSkeletonCard,
    createSkeletonDivider,
    PRODUCT_LABELS,
    TAG_LABELS,
  };
})();
