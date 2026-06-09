import { fetchJson } from '../services/api.js';
import { formatNumber } from '../utils/helpers.js';

/**
 * Load overview status data and render.
 */
export async function loadStatus() {
  try {
    const [data, skills, plugins, mcp] = await Promise.all([
      fetchJson('/api/status'),
      fetchJson('/api/skills'),
      fetchJson('/api/plugins'),
      fetchJson('/api/mcp'),
    ]);
    data._tools = { skills, plugins, mcp };
    renderOverview(data);
  } catch (err) {
    document.getElementById('overview-stats').innerHTML = `<div class="empty-state">Failed: ${err.message}</div>`;
  }
}

function renderOverview(data) {
  const gw = data.gateway;
  const td = data.today;
  const s7 = data.sessions_7d;

  document.getElementById('overview-stats').innerHTML = `
    <div class="stat-card">
      <div class="label">Gateway</div>
      <div class="value ${gw.running ? 'green' : 'red'}">${gw.running ? 'Running' : 'Down'}</div>
      <div class="sub">${gw.running ? 'PID ' + gw.pid + ' / ' + gw.uptime : ''}</div>
    </div>
    <div class="stat-card">
      <div class="label">Today Sessions</div>
      <div class="value blue">${td.sessions}</div>
      <div class="sub">${td.messages} msgs / ${td.tool_calls} tools</div>
    </div>
    <div class="stat-card">
      <div class="label">Today Tokens</div>
      <div class="value">${formatNumber(td.tokens)}</div>
    </div>
    <div class="stat-card">
      <div class="label">7d Sessions</div>
      <div class="value blue">${s7.total_sessions}</div>
      <div class="sub">${s7.active_sessions} active</div>
    </div>
    <div class="stat-card">
      <div class="label">7d Messages</div>
      <div class="value">${formatNumber(s7.total_messages)}</div>
    </div>
    <div class="stat-card">
      <div class="label">7d Tokens</div>
      <div class="value">${formatNumber(s7.input_tokens + s7.output_tokens)}</div>
      <div class="sub">in ${formatNumber(s7.input_tokens)} / out ${formatNumber(s7.output_tokens)}</div>
    </div>
  `;

  const platformsHtml = data.platforms.map(p =>
    `<div class="row"><span class="key">${p.name}</span><span class="val"><span class="indicator green"></span> configured</span></div>`
  ).join('');

  const jobsHtml = data.cron_jobs.map(j => {
    const stateClass = j.state === 'paused' ? 'yellow' : 'green';
    return `<div class="row"><span class="key">${j.job_name}</span><span class="val"><span class="indicator ${stateClass}"></span> ${j.state} (${j.total_runs} runs)</span></div>`;
  }).join('');

  const sourceHtml = s7.by_source.map(s =>
    `<div class="row"><span class="key">${s.source}</span><span class="val">${s.sessions} sessions / ${s.messages} msgs</span></div>`
  ).join('');

  const tools = data._tools || { skills: { custom: [], other: [] }, plugins: [], mcp: [] };
  const customSkillCount = tools.skills.custom ? tools.skills.custom.length : 0;
  const otherSkillCount = tools.skills.other ? tools.skills.other.length : 0;
  const pluginCount = tools.plugins ? tools.plugins.length : 0;
  const enabledPlugins = tools.plugins ? tools.plugins.filter(p => p.enabled).length : 0;
  const mcpCount = tools.mcp ? tools.mcp.length : 0;

  const toolsHtml = `
    <div class="row"><span class="key">Custom Skills</span><span class="val">${customSkillCount}</span></div>
    <div class="row"><span class="key">Other Skills</span><span class="val">${otherSkillCount}</span></div>
    <div class="row"><span class="key">Plugins</span><span class="val">${enabledPlugins} enabled / ${pluginCount} total</span></div>
    <div class="row"><span class="key">MCP Servers</span><span class="val">${mcpCount}</span></div>
  `;

  document.getElementById('status-grid').innerHTML = `
    <div class="status-panel">
      <div class="panel-header"><span class="indicator ${gw.running ? 'green' : 'red'}"></span> System</div>
      <div class="panel-body">
        <div class="row"><span class="key">Model</span><span class="val">${data.model.model}</span></div>
        <div class="row"><span class="key">Provider</span><span class="val">${data.model.provider}</span></div>
        <div class="row"><span class="key">Gateway PID</span><span class="val">${gw.pid || '-'}</span></div>
        <div class="row"><span class="key">Uptime</span><span class="val">${gw.uptime || '-'}</span></div>
      </div>
    </div>
    <div class="status-panel">
      <div class="panel-header">Platforms</div>
      <div class="panel-body">${platformsHtml || '<div class="row"><span class="key">None configured</span></div>'}</div>
    </div>
    <div class="status-panel">
      <div class="panel-header">Cron Jobs</div>
      <div class="panel-body">${jobsHtml || '<div class="row"><span class="key">None</span></div>'}</div>
    </div>
    <div class="status-panel">
      <div class="panel-header">Tools</div>
      <div class="panel-body">${toolsHtml}</div>
    </div>
    <div class="status-panel">
      <div class="panel-header">Traffic by Source (7d)</div>
      <div class="panel-body">${sourceHtml}</div>
    </div>
  `;
}
