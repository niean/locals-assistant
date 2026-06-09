import { fetchJson } from '../services/api.js';
import { escapeHtml, linkify } from '../utils/helpers.js';
import { openModal } from './modal.js';

/**
 * Load all cron jobs and render.
 */
export async function loadJobs() {
  try {
    const jobs = await fetchJson('/api/jobs');
    renderJobs(jobs);
  } catch (err) {
    document.getElementById('jobs-container').innerHTML = `<div class="empty-state">Failed: ${err.message}</div>`;
  }
}

async function loadRuns(jobId, limit = 50) {
  return fetchJson(`/api/runs/${jobId}?limit=${limit}`);
}

function renderJobs(jobs) {
  const container = document.getElementById('jobs-container');
  container.innerHTML = '';

  const today = new Date().toISOString().split('T')[0];
  let totalToday = 0;
  let deliveredToday = 0;
  let silentToday = 0;

  for (const job of jobs) {
    const section = document.createElement('div');
    section.className = 'job-section';

    const jobName = job.job_name || job.job_id;
    const schedule = job.schedule_display || '';
    const state = job.state || 'unknown';
    const stateClass = state === 'paused' ? 'paused' : 'delivered';
    const stateLabel = state === 'paused' ? 'Paused' : state;
    const lastRunAt = job.last_run_at ? new Date(job.last_run_at).toLocaleString('zh-CN') : '-';
    const nextRunAt = job.next_run_at ? new Date(job.next_run_at).toLocaleString('zh-CN') : '-';

    section.innerHTML = `
      <div class="job-header">
        <h2>${jobName} <span class="job-id">${job.job_id}</span> <span class="status-badge ${stateClass}"><span class="status-dot ${stateClass}"></span>${stateLabel}</span></h2>
        <span style="display:flex;align-items:center;gap:12px;">
          <button class="prompt-btn" onclick="showPrompt('${job.job_id}')">View Prompt</button>
          <span class="schedule">${schedule} | ${job.total_runs} runs</span>
        </span>
      </div>
      <div class="job-meta">
        <span>Last: ${lastRunAt}</span>
        <span>Next: ${nextRunAt}</span>
        <span>Deliver: ${job.deliver || '-'}</span>
      </div>
      <div class="runs-body" id="runs-${job.job_id}"><div class="empty-state">Loading...</div></div>
    `;
    container.appendChild(section);

    loadRuns(job.job_id).then(runs => {
      renderRuns(job.job_id, runs);
      const todayRuns = runs.filter(r => r.timestamp && r.timestamp.startsWith(today));
      totalToday += todayRuns.length;
      deliveredToday += todayRuns.filter(r => r.status === 'delivered').length;
      silentToday += todayRuns.filter(r => r.status === 'silent').length;
      document.getElementById('cron-stats').innerHTML = `
        <div class="stat-card"><div class="label">Runs Today</div><div class="value blue">${totalToday}</div></div>
        <div class="stat-card"><div class="label">Delivered</div><div class="value green">${deliveredToday}</div></div>
        <div class="stat-card"><div class="label">Silent</div><div class="value yellow">${silentToday}</div></div>
      `;
    });
  }
}

function renderRuns(jobId, runs) {
  const body = document.getElementById(`runs-${jobId}`);
  if (!runs.length) { body.innerHTML = '<div class="empty-state">No runs</div>'; return; }

  let html = `<table class="runs-table"><thead><tr><th>Time</th><th>Status</th><th>Response</th></tr></thead><tbody>`;
  for (const run of runs) {
    const status = run.status || 'unknown';
    const statusLabel = status === 'silent' ? 'Silent' : status === 'delivered' ? 'Delivered' : status === 'no_response' ? 'No Response' : 'Unknown';
    let responseHtml = '';
    if (run.response) {
      const clean = run.response.replace('[SILENT]', '').trim();
      if (!clean) {
        responseHtml = '<span class="response-text silent-text">-</span>';
      } else {
        const short = clean.length > 120 ? clean.substring(0, 120) + '...' : clean;
        const id = `resp-${run.filename}`;
        responseHtml = `<span class="response-text${status === 'silent' ? ' silent-text' : ''}">${linkify(escapeHtml(short))}</span>
          ${clean.length > 120 ? `<span class="response-toggle" onclick="toggleResponse('${id}')">Show full</span><div class="response-full" id="${id}">${linkify(escapeHtml(clean))}</div>` : ''}`;
      }
    } else {
      responseHtml = '<span class="response-text silent-text">-</span>';
    }
    html += `<tr><td><span class="timestamp">${run.timestamp || run.filename}</span></td><td><span class="status-badge ${status}"><span class="status-dot ${status}"></span>${statusLabel}</span></td><td>${responseHtml}</td></tr>`;
  }
  html += '</tbody></table>';
  body.innerHTML = html;
}

/**
 * Show cron job prompt in modal.
 * @param {string} jobId
 */
export async function showPrompt(jobId) {
  const body = openModal('Loading...');
  try {
    const data = await fetchJson(`/api/prompt/${jobId}`);
    if (data.error) { body.textContent = data.error; return; }
    document.getElementById('prompt-modal-title').textContent = `Prompt: ${data.job_name}`;
    body.textContent = data.prompt;
  } catch (err) { body.textContent = `Failed: ${err.message}`; }
}
