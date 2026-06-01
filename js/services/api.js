import { API_BASE } from '../utils/constants.js';

/**
 * Fetch JSON from an API endpoint.
 * @param {string} path - Path relative to API_BASE (e.g. '/api/jobs')
 * @returns {Promise<any>} Parsed JSON response
 */
export async function fetchJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
  return res.json();
}

/**
 * POST JSON to an API endpoint.
 * @param {string} path - Path relative to API_BASE
 * @param {object} body - Request body
 * @returns {Promise<any>} Parsed JSON response
 */
export async function postJson(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}
