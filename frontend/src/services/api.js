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
  redispatchIncident: (id, payload) => request(`/incidents/${id}/redispatch`, { method: 'POST', body: JSON.stringify(payload) }),
  overrideVerifyIncident: (id, payload) => request(`/incidents/${id}/override-verify`, { method: 'POST', body: JSON.stringify(payload) }),
  cancelIncident: (id, payload) => request(`/incidents/${id}/cancel`, { method: 'POST', body: JSON.stringify(payload) }),
  uploadEvidence: async (incidentId, file, attachToTask = false) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('attach_to_task', String(attachToTask));
    const res = await fetch(`${BASE_URL}/evidence/upload/${incidentId}`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || err.detail || `Upload failed with HTTP ${res.status}`);
    }
    return res.json();
  },
  getPresignedUrl: (s3Key) => request(`/evidence/presigned-url?s3_key=${encodeURIComponent(s3Key)}`),
  getAuditHistory: (id) => request(`/incidents/${id}/audit`),
  chatAgent: (payload) => request('/agent/chat', { method: 'POST', body: JSON.stringify(payload) }),
  getAgentTools: () => request('/agent/tools'),
};

