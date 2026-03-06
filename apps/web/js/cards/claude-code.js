/**
 * Claude Code card/modal renderer.
 * Only card_yn=1 events are shown (filtered server-side).
 */
(() => {
  'use strict';

  const { escapeHtml, formatDateShort, createModalSection, renderSourceSection,
          PRODUCT_LABELS, CardRenderers } = CardBase;

  const CHANGE_TYPE_LABELS = {
    added: '\uCD94\uAC00',
    changed: '\uBCC0\uACBD',
    fixed: '\uC218\uC815',
    removed: '\uC81C\uAC70',
    deprecated: '\uC9C0\uC6D0 \uC911\uB2E8',
    security: '\uBCF4\uC548',
    improved: '\uAC1C\uC120',
    updated: '\uC5C5\uB370\uC774\uD2B8',
    other: '\uAE30\uD0C0',
  };

  function createCard(event) {
    const article = document.createElement('article');
    article.className = 'event-card event-card--claude-code';
    article.dataset.product = 'claude_code';
    article.dataset.eventId = event.id;
    article.setAttribute('role', 'button');
    article.setAttribute('tabindex', '0');

    // title_ko is mapped from title_kor in UNION SQL
    const headline = event.title_ko || event.title;
    article.setAttribute('aria-label', escapeHtml(headline));

    article.innerHTML = `
      <p class="event-card__headline">${escapeHtml(headline)}</p>
      <div class="event-card__bottom"><span class="event-card__date-compact">${(event.event_date || '').replace(/-/g, '').substring(4)}</span></div>
    `;

    return article;
  }

  function renderModalHeader(headerEl, detail) {
    const pd = detail.product_data || {};
    // Korean title as main heading
    const koTitle = pd.title_kor || detail.title_ko || detail.title;

    headerEl.innerHTML = `
      <div class="modal__title-row">
        <span class="product-badge" data-product="claude_code">${escapeHtml(PRODUCT_LABELS.claude_code)}</span>
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

    // 1) content_kor (Korean summary)
    const contentKor = pd.content_kor || '';
    if (contentKor) {
      const section = createModalSection('\uD55C\uAD6D\uC5B4 \uC694\uC57D');
      const block = document.createElement('div');
      block.className = 'content-block';
      block.textContent = contentKor;
      section.appendChild(block);
      bodyEl.appendChild(section);
    }

    // 2) subsystem + change_type (metadata row)
    const subsystem = pd.subsystem || '';
    const changeType = pd.change_type || detail.component || '';
    const changeLabel = CHANGE_TYPE_LABELS[changeType] || changeType;
    if (subsystem || changeType) {
      const section = createModalSection('\uBD84\uB958');
      const row = document.createElement('div');
      row.className = 'cc-meta-row';
      if (changeType) {
        row.innerHTML += `<span class="change-type-chip" data-type="${escapeHtml(changeType)}">${escapeHtml(changeLabel)}</span>`;
      }
      if (subsystem) {
        row.innerHTML += `<span class="subsystem-label">${escapeHtml(subsystem)}</span>`;
      }
      section.appendChild(row);
      bodyEl.appendChild(section);
    }

    // 3) Original English title
    const enTitle = detail.title || '';
    if (enTitle) {
      const section = createModalSection('Original Title');
      const block = document.createElement('div');
      block.className = 'chatgpt-en-title';
      block.textContent = enTitle;
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

  CardRenderers.claude_code = { createCard, renderModalHeader, renderModalBody };
})();
