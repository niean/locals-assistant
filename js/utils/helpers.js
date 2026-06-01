/**
 * Escape HTML special characters to prevent XSS.
 * @param {string} t - Raw text
 * @returns {string} Escaped HTML string
 */
export function escapeHtml(t) {
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}

/**
 * Convert CM order numbers in HTML to clickable links.
 * @param {string} html - Already-escaped HTML string
 * @returns {string} HTML with CM links
 */
export function linkify(html) {
  return html.replace(
    /CM(\d{6,})/g,
    '<a class="order-link" href="https://op.zuoyebang.cc/static/odin/index.html#/cm/wait/detail/CM$1" target="_blank">CM$1</a>'
  );
}

/**
 * Format large numbers with K/M suffix.
 * @param {number} n
 * @returns {string}
 */
export function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

/**
 * Toggle visibility of a full-response element.
 * @param {string} id - Element ID
 */
export function toggleResponse(id) {
  document.getElementById(id).classList.toggle('open');
}
