const VALID_TABS = ['overview', 'cron', 'sessions', 'mcp', 'skills', 'plugins'];

/**
 * Switch to a named tab, updating content visibility and URL hash.
 * @param {string} name - Tab name
 * @param {boolean} updateHash - Whether to update location.hash
 */
export function switchTab(name, updateHash = true) {
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const tabEl = document.querySelector(`#tab-${name}`);
  if (tabEl) tabEl.classList.add('active');
  if (updateHash) location.hash = name === 'overview' ? '' : name;
}

/**
 * Get the current tab name from the URL hash.
 * @returns {string} Tab name
 */
export function getTabFromHash() {
  const hash = location.hash.replace('#', '');
  return VALID_TABS.includes(hash) ? hash : 'overview';
}

/**
 * Initialize navigation: restore tab from hash + listen for hash changes.
 */
export function initNavigation() {
  window.addEventListener('hashchange', () => switchTab(getTabFromHash(), false));
  switchTab(getTabFromHash(), false);
}
