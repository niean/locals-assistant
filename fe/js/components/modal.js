/**
 * Open the shared modal and return the body element for content injection.
 * @param {string} title - Modal title text
 * @returns {HTMLElement} The modal body element
 */
export function openModal(title) {
  const modal = document.getElementById('prompt-modal');
  const body = document.getElementById('prompt-modal-body');
  const modalTitle = document.getElementById('prompt-modal-title');
  body.textContent = 'Loading...';
  body.style.fontFamily = '';
  modalTitle.textContent = title;
  modal.classList.add('open');
  return body;
}

/**
 * Close the shared modal.
 * @param {Event} [e] - Click event (for overlay click detection)
 */
export function closePromptModal(e) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('prompt-modal').classList.remove('open');
}
