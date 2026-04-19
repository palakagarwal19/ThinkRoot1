import { useState, useEffect } from 'react';
import { Flame, Thermometer, Snowflake, Users } from 'lucide-react';
import { getPipeline } from '../api';
import { Spinner, StatCard } from '../components/UI';

export default function Pipeline() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getPipeline()
      .then((res) => setData(res))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><Spinner /></div>;

  if (error) {
    return (
      <div className="page">
        <div style={{
          background: 'var(--hot-bg)',
          border: '1px solid rgba(255,87,87,0.3)',
          borderRadius: 'var(--radius-md)',
          padding: '14px 18px',
          color: 'var(--hot)',
          fontSize: 14,
        }}>
          {error}
        </div>
      </div>
    );
  }

  const agents = data?.agents || {};
  const lc = data?.lead_classification || {};
  const ds = data?.data_sources || {};

  // Metadata fields to display per agent (everything except 'status')
  const getMetaEntries = (agentData) =>
    Object.entries(agentData).filter(([k]) => k !== 'status');

  // Data source display config
  const dataSources = [
    { key: 'primary', label: 'Apollo CSV' },
    { key: 'clay_api', label: 'Clay API' },
    { key: 'apollo_api', label: 'Apollo API' },
    { key: 'gemini_api', label: 'Gemini API' },
  ];

  return (
    <div className="page slide-up">
      <div className="page-header">
        <h1>⚙️ Pipeline Status</h1>
        <p>Multi-agent pipeline overview — agents, data sources, and lead classification</p>
        {data?.pipeline && (
          <div className="badge-row">
            <span className="chip chip-purple">{data.pipeline}</span>
          </div>
        )}
      </div>

      {/* Lead classification stats */}
      <div className="stat-grid">
        <StatCard label="Hot Leads" value={lc.hot ?? 0} sub="Score ≥ 70" icon={Flame} color="var(--hot)" />
        <StatCard label="Warm Leads" value={lc.warm ?? 0} sub="Score 40–69" icon={Thermometer} color="var(--warm)" />
        <StatCard label="Cold Leads" value={lc.cold ?? 0} sub="Score &lt; 40" icon={Snowflake} color="var(--cold)" />
        <StatCard label="Total Leads" value={lc.total ?? 0} sub="All classified" icon={Users} color="var(--accent)" />
      </div>

      {/* Agent cards */}
      {Object.keys(agents).length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 14, color: 'var(--text-secondary)' }}>
            Agents
          </h2>
          <div className="agent-grid">
            {Object.entries(agents).map(([name, agentData]) => {
              const metaEntries = getMetaEntries(agentData);
              return (
                <div key={name} className="agent-card">
                  <div className="agent-header">
                    <span className="agent-name">{name}</span>
                    <span className="agent-status">{agentData.status || 'active'}</span>
                  </div>
                  {metaEntries.length > 0 && (
                    <div className="agent-meta">
                      {metaEntries.map(([k, v]) => (
                        <div key={k}>
                          <span style={{ color: 'var(--text-muted)' }}>
                            {k.replace(/_/g, ' ')}:
                          </span>{' '}
                          {String(v)}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Data sources */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 16 }}>Data Sources</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
          {dataSources.map(({ key, label }) => {
            const status = ds[key];
            const isConfigured = status && status !== 'not_configured' && status !== 'missing' && status !== 'disabled';
            return (
              <div
                key={key}
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10,
                }}
              >
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                  {label}
                </span>
                <span className={`chip ${isConfigured ? 'chip-green' : 'chip-gray'}`}>
                  {status || 'unknown'}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
