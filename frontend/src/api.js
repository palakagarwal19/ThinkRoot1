const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// Health
export const getHealth = () => req('/');

// Leads
export const getLeads = (params = {}) => {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== '' && q.append(k, v));
  return req(`/api/leads?${q}`);
};
export const getLeadsStats = () => req('/api/leads/stats');
export const getLead = (id) => req(`/api/leads/${id}`);
export const getLeadSignals = (id) => req(`/api/leads/${id}/signals`);
export const getLeadScore = (id) => req(`/api/leads/${id}/score`);
export const getLeadOutreach = (id) => req(`/api/leads/${id}/outreach`);

// Graph
export const getAllGraphs = (minSize = 1) => req(`/api/graph?min_committee_size=${minSize}`);
export const getCompanyGraph = (company) => req(`/api/graph/${encodeURIComponent(company)}`);

// A/B Testing
export const getABStats = () => req('/api/ab-testing');
export const registerABSend = (data) => req('/api/ab-testing/register', { method: 'POST', body: JSON.stringify(data) });
export const recordABResponse = (data) => req('/api/ab-testing/response', { method: 'POST', body: JSON.stringify(data) });

// Learning
export const submitResponse = (data) => req('/api/learn/response', { method: 'POST', body: JSON.stringify(data) });
export const getLearningStats = () => req('/api/learn/stats');
export const resetLearning = () => req('/api/learn/reset', { method: 'POST' });

// Pipeline
export const getPipeline = () => req('/api/pipeline');
