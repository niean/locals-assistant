import { fetchJson, postJson } from '../services/api.js';
import { escapeHtml, formatNumber } from '../utils/helpers.js';
import { openModal } from './modal.js';

/**
 * Load sessions data and render.
 */
export async function loadSessions() {
  try {
    const data = await fetchJson('/api/sessions?days=7');
    renderSessions(data);
  } catch (err) {
    document.getElementById('sessions-list').innerHTML = `<div class="empty-state">Failed: ${err.message}</div>`;
  }
}

function renderSessions(data) {
  document.getElementById('sessions-stats').innerHTML = `
    <div class="stat-card"><div class="label">Sessions (7d)</div><div class="value blue">${data.total_sessions}</div><div class="sub">${data.active_sessions} active</div></div>
    <div class="stat-card"><div class="label">Messages</div><div class="value">${formatNumber(data.total_messages)}</div></div>
    <div class="stat-card"><div class="label">Tool Calls</div><div class="value">${formatNumber(data.total_tool_calls)}</div></div>
    <div class="stat-card"><div class="label">Input Tokens</div><div class="value">${formatNumber(data.input_tokens)}</div></div>
    <div class="stat-card"><div class="label">Output Tokens</div><div class="value">${formatNumber(data.output_tokens)}</div></div>
  `;

  if (!data.recent_sessions || !data.recent_sessions.length) {
    document.getElementById('sessions-list').innerHTML = '<div class="empty-state">No active sessions</div>';
  } else {
    document.getElementById('sessions-list').innerHTML = renderSessionTable(data.recent_sessions, true);
  }

  if (!data.inactive_sessions || !data.inactive_sessions.length) {
    document.getElementById('sessions-inactive').innerHTML = '<div class="empty-state">No inactive sessions</div>';
  } else {
    document.getElementById('sessions-inactive').innerHTML = renderSessionTable(data.inactive_sessions, false);
  }
}

function renderSessionTable(sessions, showDisconnect) {
  let html = `<table class="sessions-table" style="table-layout:fixed;"><colgroup><col style="width:300px;"><col><col style="width:100px;"><col style="width:100px;"><col style="width:80px;"><col style="width:80px;"><col style="width:80px;"><col style="width:120px;"></colgroup><thead><tr><th>ID</th><th>Title</th><th>Source</th><th>Started</th><th style="text-align:right;">Msgs</th><th style="text-align:right;">Tools</th><th style="text-align:right;">Tokens</th><th>Actions</th></tr></thead><tbody>`;
  for (const s of sessions) {
    const time = new Date(s.started_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    const totalTokens = (s.input_tokens || 0) + (s.output_tokens || 0);
    const tokenK = totalTokens > 0 ? (totalTokens / 1000).toFixed(1) + 'K' : '-';
    const tokenDisplay = totalTokens > 0 ? `<span title="in: ${formatNumber(s.input_tokens)} / out: ${formatNumber(s.output_tokens)}">${tokenK}</span>` : '-';
    const viewBtn = `<button class="icon-btn" onclick="showSessionMessages('${s.id}', '${escapeHtml(s.title)}')" title="View messages"><svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M1.679 7.932c.412-.621 1.242-1.75 2.366-2.717C5.175 4.242 6.527 3.5 8 3.5c1.473 0 2.825.742 3.955 1.715 1.124.967 1.954 2.096 2.366 2.717a.12.12 0 0 1 0 .136c-.412.621-1.242 1.75-2.366 2.717C10.825 11.758 9.473 12.5 8 12.5c-1.473 0-2.825-.742-3.955-1.715C2.921 9.818 2.091 8.69 1.679 8.068a.12.12 0 0 1 0-.136zM8 2c-1.981 0-3.67.992-4.933 2.078C1.86 5.137.907 6.41.458 7.088a1.62 1.62 0 0 0 0 1.824c.449.678 1.402 1.951 2.609 3.01C4.33 13.008 6.019 14 8 14c1.981 0 3.67-.992 4.933-2.078 1.207-1.059 2.16-2.332 2.609-3.01a1.62 1.62 0 0 0 0-1.824c-.449-.678-1.402-1.951-2.609-3.01C11.67 2.992 9.981 2 8 2zm0 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-3.5 2a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/></svg></button>`;
    const disconnectBtn = showDisconnect ? `<button class="icon-btn icon-btn--danger" onclick="disconnectSession('${s.id}', this)" title="Disconnect session"><svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06z"/></svg></button>` : '';
    html += `<tr>
      <td class="id-cell" title="${s.id}"><span class="job-id">${s.id}</span></td>
      <td class="title-cell" title="${escapeHtml(s.title)}">
        <span id="title-text-${s.id}" ondblclick="startRename('${s.id}')" style="cursor:pointer;">${escapeHtml(s.title)}</span>
        <span id="title-edit-${s.id}" style="display:none;">
          <input type="text" value="${escapeHtml(s.title)}" style="font-size:13px;padding:2px 6px;border:1px solid #0969da;border-radius:4px;width:200px;" onkeydown="if(event.key==='Enter')submitRename('${s.id}',this.value);if(event.key==='Escape')cancelRename('${s.id}');">
          <button class="prompt-btn" onclick="submitRename('${s.id}',this.previousElementSibling.value)" style="margin-left:4px;">Save</button>
        </span>
      </td>
      <td><span class="source-badge ${s.source}">${s.source}</span></td>
      <td><span class="timestamp">${time}</span></td>
      <td style="text-align:right;">${s.messages}</td>
      <td style="text-align:right;">${s.tool_calls}</td>
      <td style="text-align:right;">${tokenDisplay}</td>
      <td>${viewBtn}${disconnectBtn}</td>
    </tr>`;
  }
  html += '</tbody></table>';
  return html;
}

/**
 * Show session messages in modal.
 */
export async function showSessionMessages(sessionId, title) {
  const body = openModal(`Session: ${title}`);
  try {
    const data = await fetchJson(`/api/sessions/${sessionId}/messages`);
    if (data.error) { body.textContent = data.error; return; }
    if (!data.messages.length) { body.textContent = 'No messages'; return; }
    let html = '<div style="display:flex;flex-direction:column;gap:12px;">';
    for (const m of data.messages) {
      const roleClass = m.role === 'user' ? 'color:#0969da;' : m.role === 'assistant' ? 'color:#1a7f37;' : 'color:#9a6700;';
      const roleLabel = m.role === 'tool' ? `tool(${m.tool_name || '?'})` : m.role;
      const content = escapeHtml(m.content || '(empty)');
      html += `<div style="border-bottom:1px solid #eaeef2;padding-bottom:8px;">
        <div style="font-size:11px;margin-bottom:4px;"><span style="${roleClass}font-weight:600;">${roleLabel}</span> <span style="color:#8c959f;">${m.time}</span></div>
        <div style="white-space:pre-wrap;word-break:break-word;font-size:12px;line-height:1.5;">${content}</div>
      </div>`;
    }
    html += '</div>';
    body.innerHTML = html;
    body.style.fontFamily = 'inherit';
  } catch (err) { body.textContent = `Failed: ${err.message}`; }
}

export function startRename(sessionId) {
  document.getElementById(`title-text-${sessionId}`).style.display = 'none';
  const editEl = document.getElementById(`title-edit-${sessionId}`);
  editEl.style.display = 'inline';
  editEl.querySelector('input').focus();
}

export function cancelRename(sessionId) {
  document.getElementById(`title-text-${sessionId}`).style.display = '';
  document.getElementById(`title-edit-${sessionId}`).style.display = 'none';
}

export async function submitRename(sessionId, newTitle) {
  try {
    const data = await postJson(`/api/sessions/${sessionId}/rename`, { title: newTitle });
    if (data.ok) { loadSessions(); }
    else { alert(data.error || 'Rename failed'); cancelRename(sessionId); }
  } catch (err) { alert(`Error: ${err.message}`); cancelRename(sessionId); }
}

export async function disconnectSession(sessionId, btn) {
  if (!confirm('Disconnect this session?')) return;
  btn.disabled = true;
  btn.textContent = '...';
  try {
    const data = await postJson(`/api/sessions/${sessionId}/disconnect`, {});
    if (data.ok) { btn.textContent = 'Done'; btn.style.color = '#1a7f37'; loadSessions(); }
    else { btn.textContent = data.error || 'Failed'; btn.style.color = '#cf222e'; }
  } catch (err) { btn.textContent = 'Error'; btn.style.color = '#cf222e'; }
}
