import { useState, useEffect, useCallback } from 'react';
import { Spinner, StatCard } from '../components/UI';
import { getLearningStats, resetLearning } from '../api';
import { Brain, RotateCcw } from 'lucide-react';

export default function Learning() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [resetting, setResetting] = useState(false);
  const [resetMsg, setResetMsg] = useState(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getLearningStats();
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleReset = async () => {
    setResetting(true);
    setResetMsg(null);
    setError(null);
    try {
      await resetLearning();
      await fetchStats();
      setResetMsg('Weights have been reset to defaults.');
    } catch (e) {
      setError(`Reset failed: ${e.message}`);
    } finally {
      setResetting(false);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>Learning Engine</h1>
        <p>Adaptive scoring weights based on response feedback</p>
      </div>

      {error && (
        <div
          style={{
            background: 'var(--hot-bg)',
            color: 'var(--hot)',
            border: '1px solid rgba(255,87,87,0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            marginBottom: 24,
            fontSize: 14,
          }}
        >
          {error}
        </div>
      )}

      {resetMsg && (
        <div
          style={{
            background: 'rgba(0,212,170,0.1)',
            color: 'var(--accent3)',
            border: '1px solid rgba(0,212,170,0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            marginBottom: 24,
            fontSize: 14,
          }}
        >
          {resetMsg}
        </div>
      )}

      {data && (
        <>
          {/* Summary stats */}
          <div className="stat-grid">
            <StatCard
              label="Total Responses"
              value={data.total_responses ?? 0}
              icon={Brain}
              color="var(--accent)"
            />
            {data.response_counts && (
              <>
                <StatCard
                  label="Replied"
                  value={data.response_counts.replied ?? 0}
                  color="var(--accent3)"
                />
                <StatCard
                  label="Demoed"
                  value={data.response_counts.demoed ?? 0}
                  color="var(--accent2)"
                />
                <StatCard
                  label="Opened"
                  value={data.response_counts.opened ?? 0}
                  color="var(--warm)"
                />
                <StatCard
                  label="Bounced"
                  value={data.response_counts.bounced ?? 0}
                  color="var(--text-muted)"
                />
                <StatCard
                  label="Unsubscribed"
                  value={data.response_counts.unsubscribed ?? 0}
                  color="var(--hot)"
                />
              </>
            )}
          </div>

          {/* Weight bars */}
          {data.weights && (
            <div className="card" style={{ marginBottom: 28 }}>
              <div className="card-title" style={{ marginBottom: 16 }}>
                Scoring Weights
              </div>
              {Object.entries(data.weights).map(([key, value]) => {
                const pct = Math.min(100, Math.max(0, value * 100));
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                return (
                  <div className="weight-bar-row" key={key}>
                    <span className="weight-name">{label}</span>
                    <div className="weight-track">
                      <div className="weight-fill" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="weight-val">{(value * 100).toFixed(1)}%</span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Reset button */}
          <button
            className="btn btn-danger"
            onClick={handleReset}
            disabled={resetting}
          >
            <RotateCcw size={15} />
            {resetting ? 'Resetting…' : 'Reset Weights'}
          </button>
        </>
      )}
    </div>
  );
}
