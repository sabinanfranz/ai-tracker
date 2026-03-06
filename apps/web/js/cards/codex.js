/**
 * Codex card/modal renderer.
 */
(() => {
  'use strict';

  const { escapeHtml, formatDateShort, createModalSection, renderSourceSection,
          PRODUCT_LABELS, CardRenderers } = CardBase;

  const ENTRY_TYPE_LABELS = {
    feature: '\uC2E0\uAE30\uB2A5',
    improvement: '\uAC1C\uC120',
    fix: '\uC218\uC815',
    deprecation: '\uC9C0\uC6D0 \uC911\uB2E8',
    general: '\uC77C\uBC18',
  };

  function createCard(event) {
    const article = document.createElement('article');
    article.className = 'event-card event-card--codex';
    article.dataset.product = 'codex';
    article.dataset.eventId = event.id;
    article.setAttribute('role', 'button');
    article.setAttribute('tabindex', '0');

    // title_ko is now COALESCE(title_updated_ko, title) from API
    const headline = event.title_ko || event.title;
    article.setAttribute('aria-label', escapeHtml(headline));

    // Entry type badge
    const entryType = event.component || '';
    const entryLabel = ENTRY_TYPE_LABELS[entryType] || entryType;

    article.innerHTML = `
      <p class="event-card__headline">${escapeHtml(headline)}${entryType ? ` <span class="entry-type-badge">${escapeHtml(entryLabel)}</span>` : ''}</p>
      <div class="event-card__bottom"><span class="event-card__date-compact">${(event.event_date || '').replace(/-/g, '').substring(4)}</span></div>
    `;

    return article;
  }

  function renderModalHeader(headerEl, detail) {
    const pd = detail.product_data || {};

    // entry_type badge in header
    const entryType = pd.entry_type || detail.component || '';
    const entryLabel = ENTRY_TYPE_LABELS[entryType] || entryType;

    // Korean title as main heading
    const koTitle = pd.title_updated_ko || detail.title_ko || detail.title;

    headerEl.innerHTML = `
      <div class="modal__title-row">
        <span class="product-badge" data-product="codex">${escapeHtml(PRODUCT_LABELS.codex)}</span>
        ${entryType ? `<span class="entry-type-badge">${escapeHtml(entryLabel)}</span>` : ''}
        <span class="modal__title">${escapeHtml(koTitle)}</span>
      </div>
      <div class="modal__meta-row">
        <time datetime="${escapeHtml(detail.event_date)}">${escapeHtml(detail.event_date)}</time>
      </div>
    `;
  }

  function renderModalBody(bodyEl, detail) {
    bodyEl.innerHTML = '';
    const pd = detail.product_data || {};

    // 1) content_updated_ko (Korean summary) — bullet list per line
    const contentKo = pd.content_updated_ko || '';
    if (contentKo) {
      const section = createModalSection('\uD55C\uAD6D\uC5B4 \uC694\uC57D');
      const lines = contentKo.split('\n').filter(l => l.trim());
      if (lines.length > 1) {
        const ul = document.createElement('ul');
        ul.className = 'what-changed-list';
        lines.forEach(line => {
          const li = document.createElement('li');
          li.textContent = line.trim();
          ul.appendChild(li);
        });
        section.appendChild(ul);
      } else {
        const p = document.createElement('p');
        p.className = 'modal__text';
        p.textContent = contentKo;
        section.appendChild(p);
      }
      bodyEl.appendChild(section);
    }

    // 2) Original English title
    const enTitle = pd.title || detail.title || '';
    if (enTitle) {
      const section = createModalSection('Original Title');
      const block = document.createElement('div');
      block.className = 'chatgpt-en-title';
      block.textContent = enTitle;
      section.appendChild(block);
      bodyEl.appendChild(section);
    }

    // 3) Body (original English content)
    const bodyContent = pd.body || '';
    if (bodyContent) {
      const section = createModalSection('Original Body');
      const block = document.createElement('div');
      block.className = 'content-block content-block--en';
      block.innerHTML = escapeHtml(bodyContent).replace(/\n/g, '<br>');
      section.appendChild(block);
      bodyEl.appendChild(section);
    }

    // 4) Version
    const version = pd.version || '';
    if (version) {
      const section = createModalSection('Version');
      const block = document.createElement('div');
      block.className = 'version-badge';
      block.textContent = version;
      section.appendChild(block);
      bodyEl.appendChild(section);
    }

    // Source & Meta
    renderSourceSection(bodyEl, detail);
  }

  CardRenderers.codex = { createCard, renderModalHeader, renderModalBody };
})();
