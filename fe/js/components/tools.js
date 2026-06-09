import { fetchJson } from '../services/api.js';
import { escapeHtml } from '../utils/helpers.js';
import { openModal } from './modal.js';

/**
 * Load skills data and render both custom and other sections.
 */
export async function loadSkills() {
  try {
    const data = await fetchJson('/api/skills');
    renderSkills(data);
  } catch (err) {
    document.getElementById('skills-custom').innerHTML = `<div class="empty-state">Failed: ${err.message}</div>`;
  }
}

function renderSkills(data) {
  document.getElementById('skills-custom').innerHTML = renderSkillTable(data.custom);
  document.getElementById('skills-other').innerHTML = renderSkillTable(data.other);
}

function renderSkillTable(skills) {
  if (!skills || !skills.length) return '<div class="empty-state">No skills</div>';
  let html = `<table class="sessions-table" style="table-layout:fixed;"><colgroup><col style="width:300px"><col style="width:180px"><col><col style="width:80px"></colgroup><thead><tr><th>Name</th><th>Category</th><th>Description</th><th>Actions</th></tr></thead><tbody>`;
  for (const s of skills) {
    const desc = s.description.length > 80 ? s.description.substring(0, 80) + '...' : s.description;
    html += `<tr>
      <td><strong>${escapeHtml(s.name)}</strong></td>
      <td><span class="source-badge">${s.category}</span></td>
      <td style="color:#656d76;font-size:12px;">${escapeHtml(desc)}</td>
      <td><button class="icon-btn" onclick="showSkillContent('${s.rel_path}', '${escapeHtml(s.name)}')" title="View skill"><svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M1.679 7.932c.412-.621 1.242-1.75 2.366-2.717C5.175 4.242 6.527 3.5 8 3.5c1.473 0 2.825.742 3.955 1.715 1.124.967 1.954 2.096 2.366 2.717a.12.12 0 0 1 0 .136c-.412.621-1.242 1.75-2.366 2.717C10.825 11.758 9.473 12.5 8 12.5c-1.473 0-2.825-.742-3.955-1.715C2.921 9.818 2.091 8.69 1.679 8.068a.12.12 0 0 1 0-.136zM8 2c-1.981 0-3.67.992-4.933 2.078C1.86 5.137.907 6.41.458 7.088a1.62 1.62 0 0 0 0 1.824c.449.678 1.402 1.951 2.609 3.01C4.33 13.008 6.019 14 8 14c1.981 0 3.67-.992 4.933-2.078 1.207-1.059 2.16-2.332 2.609-3.01a1.62 1.62 0 0 0 0-1.824c-.449-.678-1.402-1.951-2.609-3.01C11.67 2.992 9.981 2 8 2zm0 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-3.5 2a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/></svg></button></td>
    </tr>`;
  }
  html += '</tbody></table>';
  return html;
}

/**
 * Load MCP servers and render.
 */
export async function loadMcp() {
  try {
    const data = await fetchJson('/api/mcp');
    if (!data.length) {
      document.getElementById('mcp-list').innerHTML = '<div class="empty-state">No MCP servers configured</div>';
      return;
    }
    let html = `<table class="sessions-table"><thead><tr><th>Name</th><th>URL</th><th>Timeout</th></tr></thead><tbody>`;
    for (const s of data) {
      html += `<tr><td><strong>${escapeHtml(s.name)}</strong></td><td><span class="timestamp">${escapeHtml(s.url)}</span></td><td>${s.timeout}s</td></tr>`;
    }
    html += '</tbody></table>';
    document.getElementById('mcp-list').innerHTML = html;
  } catch (err) {
    document.getElementById('mcp-list').innerHTML = `<div class="empty-state">Failed: ${err.message}</div>`;
  }
}

/**
 * Load plugins and render.
 */
export async function loadPlugins() {
  try {
    const data = await fetchJson('/api/plugins');
    if (!data.length) {
      document.getElementById('plugins-list').innerHTML = '<div class="empty-state">No plugins installed</div>';
      return;
    }
    let html = `<table class="sessions-table"><thead><tr><th>Name</th><th>Version</th><th>Description</th><th>Tools</th><th>Status</th></tr></thead><tbody>`;
    for (const p of data) {
      const status = p.enabled
        ? '<span class="status-badge delivered"><span class="status-dot delivered"></span>Enabled</span>'
        : '<span class="status-badge silent"><span class="status-dot silent"></span>Disabled</span>';
      const tools = p.tools.length ? p.tools.join(', ') : '-';
      html += `<tr>
        <td><strong>${escapeHtml(p.name)}</strong></td>
        <td><span class="job-id">${escapeHtml(p.version)}</span></td>
        <td style="color:#656d76;font-size:12px;">${escapeHtml(p.description)}</td>
        <td><span class="timestamp">${escapeHtml(tools)}</span></td>
        <td>${status}</td>
      </tr>`;
    }
    html += '</tbody></table>';
    document.getElementById('plugins-list').innerHTML = html;
  } catch (err) {
    document.getElementById('plugins-list').innerHTML = `<div class="empty-state">Failed: ${err.message}</div>`;
  }
}

/**
 * Show skill content in modal.
 */
export async function showSkillContent(relPath, name) {
  const body = openModal(`Skill: ${name}`);
  try {
    const data = await fetchJson(`/api/skills/${relPath}/content`);
    if (data.error) { body.textContent = data.error; return; }
    body.textContent = data.content;
  } catch (err) { body.textContent = `Failed: ${err.message}`; }
}
