import { useState, useEffect } from 'react';
import { getABStats } from '../api';
import { Spinner } from '../components/UI';

function VariantCard({ label, stats, isWinner }) {
  const variant = label.toLowerCase(); // 'a' or 'b'
  return (
    <div
      className={`variant-card ${variant}`}
      style={isWinner ? { boxShadow: '0 0 0 2px var(--accent3)', borderColor: 'var(--accent3)' } : {}}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div className="variant-label">Variant {label}</div>
        {isWinner && (
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              padding: '3px 10px',
              borderRadius: 99,
              background: 'rgba(0,212,170,0.15)',
              color: 'var(--accent3)',
              border: '1px solid rgba(0,212,170,0.35)',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
            }}
          >
            🏆 Winner
          </span>
        )}
      </div>
      <div className="metric-row">
        <span style={{ color: 'var(--text-muted)' }}>Sends</span>
        <span style={{ fontWeight: 600 }}>{stats.sends}</span>
      </div>
      <div className="metric-row">
        <span style={{ color: 'var(--text-muted)' }}>Opens</span>
        <span style={{ fontWeight: 600 }}>{stats.opens}</span>
      </div>
      <div className="metric-row">
        <span style={{ color: 'var(--text-muted)' }}>Replies</span>
        <span style={{ fontWeight: 600 }}>{stats.replies}</span>
      </div>
      <div className="metric-row">
        <span style={{ color: 'var(--text-muted)' }}>Conversion Rate</span>
        <span style={{ fontWeight: 700, color: isWinner ? 'var(--accent3)' : 'var(--text-primary)' }}>
          {(stats.conversion_rate * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

function ChannelSection({ title, channelData }) {
  const winner = channelData?.winner; // 'A', 'B', 'tie', or null
  const isWinnerA = winner === 'A';
  const isWinnerB = winner === 'B';

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-title" style={{ marginBottom: 16 }}>
        {title}
        {winner && winner !== 'tie' && (
          <span style={{ marginLeft: 10, color: 'var(--text-muted)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
            — Variant {winner} leads
          </span>
        )}
        {winner === 'tie' && (
          <span style={{ marginLeft: 10, color: 'var(--text-muted)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
            — Tied
          </span>
        )}
      </div>
      <div className="ab-grid">
        <VariantCard label="A" stats={channelData.variant_a} isWinner={isWinnerA} />
        <VariantCard label="B" stats={channelData.variant_b} isWinner={isWinnerB} />
      </div>
    </div>
  );
}

export default function ABTesting() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getABStats()
      .then((res) => setData(res))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><Spinner /></div>;

  return (
    <div className="page slide-up">
      <div className="page-header">
        <h1>🧪 A/B Testing</h1>
        <p>Compare variant performance across email and LinkedIn channels</p>
      </div>

      {error && (
        <div
          style={{
            background: 'var(--hot-bg)',
            border: '1px solid rgba(255,87,87,0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            color: 'var(--hot)',
            marginBottom: 24,
            fontSize: 14,
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {data && (
        <>
          {/* Session registry summary */}
          {data.session_registry && (
            <div className="stat-grid" style={{ marginBottom: 28 }}>
              <div className="stat-card">
                <div className="stat-label">Total Tracked Sends</div>
                <div className="stat-value">{data.session_registry.total_tracked ?? 0}</div>
                <div className="stat-sub">Active session registry</div>
              </div>
              {Object.entries(data.session_registry)
                .filter(([k]) => k !== 'total_tracked')
                .slice(0, 3)
                .map(([k, v]) => (
                  <div key={k} className="stat-card">
                    <div className="stat-label">{k.replace(/_/g, ' ')}</div>
                    <div className="stat-value" style={{ fontSize: 22 }}>
                      {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                    </div>
                  </div>
                ))}
            </div>
          )}

          {/* Channel breakdowns */}
          {data.historical_analysis?.email && (
            <ChannelSection title="📧 Email Channel" channelData={data.historical_analysis.email} />
          )}
          {data.historical_analysis?.linkedin && (
            <ChannelSection title="💼 LinkedIn Channel" channelData={data.historical_analysis.linkedin} />
          )}

          {!data.historical_analysis?.email && !data.historical_analysis?.linkedin && (
            <div className="card" style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-muted)' }}>
              No A/B testing data available yet. Start sending outreach to collect results.
            </div>
          )}
        </>
      )}
    </div>
  );
}
