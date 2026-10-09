const BASE_URL = '/api/v1';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const res = await fetch(url, config);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const errorMsg = data?.message || data?.detail || `HTTP Error ${res.status}`;
      throw new Error(errorMsg);
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  getStats: () => request('/stats'),
  getIncidents: (activeOnly = false) => request(`/incidents${activeOnly ? '?active_only=true' : ''}`),
  getIncident: (id) => request(`/incidents/${id}`),
  submitReport: (payload) => request('/incidents', { method: 'POST', body: JSON.stringify(payload) }),
  analyzeIncident: (id) => request(`/incidents/${id}/analyze`, { method: 'POST' }),
  prioritizeIncident: (id) => request(`/incidents/${id}/prioritize`, { method: 'POST' }),
  recommendResponse: (id) => request(`/incidents/${id}/recommend`, { method: 'POST' }),
  triageIncident: (id) => request(`/incidents/${id}/triage`, { method: 'POST' }),
  submitApproval: (id, payload) => request(`/incidents/${id}/approval`, { method: 'POST', body: JSON.stringify(payload) }),
  createTask: (id) => request(`/incidents/${id}/tasks`, { method: 'POST' }),
  resolveIncident: (id, payload) => request(`/incidents/${id}/resolve`, { method: 'POST', body: JSON.stringify(payload) }),
  verifyIncident: (id, payload) => request(`/incidents/${id}/verify`, { method: 'POST', body: JSON.stringify(payload) }),
  getAuditHistory: (id) => request(`/incidents/${id}/audit`),
  chatAgent: (payload) => request('/agent/chat', { method: 'POST', body: JSON.stringify(payload) }),
  getAgentTools: () => request('/agent/tools'),
};
