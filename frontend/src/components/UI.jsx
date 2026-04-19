export function Spinner() {
  return (
    <div className="spinner-wrap">
      <div className="spinner" />
      <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading…</div>
    </div>
  );
}

export function TierBadge({ tier }) {
  const cls = tier?.toLowerCase();
  return <span className={`tier-badge tier-${cls}`}>{tier}</span>;
}

export function ScoreBar({ score }) {
  const pct = Math.min(100, Math.max(0, score));
  return (
    <div className="score-bar-wrap">
      <div className="score-bar">
        <div className="score-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="score-num">{score}</span>
    </div>
  );
}

export function EmptyState({ icon: Icon, message = 'No data found' }) {
  return (
    <div className="empty-state">
      {Icon && <Icon />}
      <p>{message}</p>
    </div>
  );
}

export function StatCard({ label, value, sub, icon: Icon, color }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={color ? { color } : {}}>{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
      {Icon && (
        <div className="stat-icon" style={{ background: color ? `${color}22` : 'rgba(99,120,255,0.12)' }}>
          <Icon size={18} color={color || 'var(--accent)'} />
        </div>
      )}
    </div>
  );
}
