import { REFRESH_INTERVAL } from './utils/constants.js';
import { toggleResponse } from './utils/helpers.js';
import { initNavigation, switchTab } from './components/navigation.js';
import { loadStatus } from './components/overview.js';
import { loadJobs, showPrompt } from './components/jobs.js';
import { loadSessions, showSessionMessages, startRename, submitRename, cancelRename } from './components/sessions.js';
import { loadSkills, loadMcp, loadPlugins, showSkillContent } from './components/tools.js';
import { closePromptModal } from './components/modal.js';

/**
 * Load all data for all tabs.
 */
async function loadAll() {
  await Promise.all([loadStatus(), loadJobs(), loadSessions(), loadSkills(), loadMcp(), loadPlugins()]);
  document.getElementById('last-update').textContent = `Last updated: ${new Date().toLocaleString('zh-CN')}`;
}

// Initialize navigation
initNavigation();

// Initial data load
loadAll();

// Auto refresh
setInterval(loadAll, REFRESH_INTERVAL);

// Expose functions to inline onclick handlers
Object.assign(window, {
  loadAll,
  switchTab,
  showPrompt,
  closePromptModal,
  showSessionMessages,
  startRename,
  submitRename,
  cancelRename,
  showSkillContent,
  toggleResponse,
});
