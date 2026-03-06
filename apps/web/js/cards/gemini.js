/**
 * Gemini card/modal renderer.
 */
(() => {
  'use strict';

  const { escapeHtml, formatDateShort, createModalSection, renderSourceSection,
          PRODUCT_LABELS, CardRenderers } = CardBase;

  function createCard(event) {
    const article = document.createElement('article');
    article.className = 'event-card event-card--gemini';
    article.dataset.product = 'gemini';
    article.dataset.eventId = event.id;
    article.setAttribute('role', 'button');
    article.setAttribute('tabindex', '0');

    const headline = event.title_ko || event.title;
    article.setAttribute('aria-label', escapeHtml(headline));

    article.innerHTML = `
      <p class="event-card__headline">${escapeHtml(headline)}</p>
      <div class="event-card__bottom"><span class="event-card__date-compact">${(event.event_date || '').replace(/-/g, '').substring(4)}</span></div>
    `;

    return article;
  }

  function renderModalHeader(headerEl, detail) {
    const koTitle = detail.title_ko || detail.title;

    headerEl.innerHTML = `
      <div class="modal__title-row">
        <span class="product-badge" data-product="gemini">${escapeHtml(PRODUCT_LABELS.gemini)}</span>
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

    // 1) content_ko (Korean summary) — bullet list per line
    const contentKo = pd.content_ko || '';
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

    // 3) Original English content
    const contentEn = pd.content || '';
    if (contentEn) {
      const section = createModalSection('Original Content');
      const block = document.createElement('div');
      block.className = 'content-block content-block--en';
      block.innerHTML = escapeHtml(contentEn).replace(/\n/g, '<br>');
      section.appendChild(block);
      bodyEl.appendChild(section);
    }

    // Source & Meta
    renderSourceSection(bodyEl, detail);
  }

  CardRenderers.gemini = { createCard, renderModalHeader, renderModalBody };
})();
