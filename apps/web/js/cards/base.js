/**
 * Base card module — shared utilities, constants, and renderer registry.
 * All product-specific renderers register themselves here.
 */
const CardBase = (() => {
  'use strict';

  /** Product label lookup */
  const PRODUCT_LABELS = {
    chatgpt: 'ChatGPT',
    gemini: 'Gemini',
    codex: 'Codex',
    claude_code: 'Claude Code',
  };

  /** Tag label lookup */
  const TAG_LABELS = {
    new: '\uC0C8 \uAE30\uB2A5',
    change: '\uC8FC\uC694 \uBCC0\uACBD',
    pricing: '\uC694\uAE08/\uC811\uADFC',
    fix: '\uAC1C\uC120/\uC218\uC815',
  };

  /**
   * Sanitize text to prevent XSS.
   */
  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /**
   * Format "YYYY-MM-DD" to short "MM-DD".
   */
  function formatDateShort(dateStr) {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length === 3) return parts[1] + '-' + parts[2];
    return dateStr;
  }

  /**
   * Create a modal section with a title.
   */
  function createModalSection(titleText) {
    const section = document.createElement('div');
    section.className = 'modal-section';
    const title = document.createElement('div');
    title.className = 'modal-section__title';
    title.textContent = titleText;
    section.appendChild(title);
    return section;
  }

  /**
   * Create skeleton card placeholder.
   */
  function createSkeletonCard() {
    const div = document.createElement('div');
    div.className = 'skeleton-card';
    div.setAttribute('aria-hidden', 'true');
    div.innerHTML = `
      <div class="skeleton-meta">
        <div class="skeleton-line skeleton-line--badge"></div>
        <div class="skeleton-line skeleton-line--badge"></div>
      </div>
      <div class="skeleton-line skeleton-line--long"></div>
      <div class="skeleton-line skeleton-line--medium"></div>
    `;
    return div;
  }

  /**
   * Create skeleton divider placeholder.
   */
  function createSkeletonDivider() {
    const div = document.createElement('div');
    div.className = 'skeleton-divider';
    div.setAttribute('aria-hidden', 'true');
    div.innerHTML = '<div class="skeleton-divider__text"></div>';
    return div;
  }

  /**
   * Render the common "Source & Meta" section used across products.
   */
  function renderSourceSection(bodyEl, detail) {
    const hasSource = !!detail.source_url;
    const hasDetected = !!detail.detected_at;
    if (!hasSource && !hasDetected) return;

    const section = createModalSection('\uCD9C\uCC98 \uBC0F \uC815\uBCF4');
    const meta = document.createElement('div');
    meta.className = 'source-meta';

    if (hasSource) {
      const row = document.createElement('div');
      row.className = 'source-meta__row';
      row.innerHTML = `<span class="source-meta__label">\uCD9C\uCC98</span>`;
      const link = document.createElement('a');
      link.className = 'source-meta__link';
      link.href = detail.source_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = '\uC6D0\uBB38 \uBCF4\uAE30 \u2192';
      row.appendChild(link);
      meta.appendChild(row);
    }

    if (hasDetected) {
      const row = document.createElement('div');
      row.className = 'source-meta__row';
      const detectedDate = new Date(detail.detected_at);
      const formatted = isNaN(detectedDate.getTime())
        ? escapeHtml(detail.detected_at)
        : detectedDate.toLocaleString('ko-KR');
      row.innerHTML = `<span class="source-meta__label">\uC218\uC9D1\uC77C</span><span class="source-meta__value">${formatted}</span>`;
      meta.appendChild(row);
    }

    section.appendChild(meta);
    bodyEl.appendChild(section);
  }

  /**
   * Registry — product renderers register themselves here.
   * Each renderer: { createCard(event), renderModalHeader(el, detail), renderModalBody(el, detail) }
   */
  const CardRenderers = {};

  return {
    PRODUCT_LABELS,
    TAG_LABELS,
    escapeHtml,
    formatDateShort,
    createModalSection,
    createSkeletonCard,
    createSkeletonDivider,
    renderSourceSection,
    CardRenderers,
  };
})();
