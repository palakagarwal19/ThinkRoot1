import { useState, useEffect } from 'react';
import { Users, Flame, Thermometer, Snowflake, TrendingUp, Mail, MessageSquare, BarChart2 } from 'lucide-react';
import { getLeadsStats, getPipeline } from '../api';
import { Spinner, StatCard } from '../components/UI';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = ['#ff5757', '#ffad33', '#4ea3ff', '#6378ff', '#9b6bff', '#00d4aa', '#ff7eb3'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', fontSize: 13 }}>
      <p style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || 'var(--accent)' }}>{p.name}: <strong>{p.value}</strong></p>
      ))}
    </div>
  );
};

export default function Overview() {
  const [stats, setStats] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getLeadsStats(), getPipeline()])
      .then(([s, p]) => { setStats(s); setPipeline(p); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><Spinner /></div>;

  const tierData = stats ? [
    { name: 'Hot', value: stats.tier_counts?.Hot || 0, color: '#ff5757' },
    { name: 'Warm', value: stats.tier_counts?.Warm || 0, color: '#ffad33' },
    { name: 'Cold', value: stats.tier_counts?.Cold || 0, color: '#4ea3ff' },
  ] : [];

  const industryData = stats
    ? Object.entries(stats.top_industries || {}).slice(0, 8).map(([k, v]) => ({ name: k.length > 20 ? k.slice(0, 18) + '…' : k, count: v }))
    : [];

  const countryData = stats
    ? Object.entries(stats.top_countries || {}).slice(0, 7).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const eng = stats?.engagement || {};

  return (
    <div className="page slide-up">
      <div className="page-header">
        <h1>🧠 NeuroLead Dashboard</h1>
        <p>Multi-agent AI lead intelligence for P95.ai — real-time overview</p>
      </div>

      {/* KPI row */}
      <div className="stat-grid">
        <StatCard label="Total Leads" value={stats?.total_leads || 0} sub="Apollo CSV Pipeline" icon={Users} color="var(--accent)" />
        <StatCard label="Hot Leads" value={stats?.tier_counts?.Hot || 0} sub="Score ≥ 70" icon={Flame} color="var(--hot)" />
        <StatCard label="Warm Leads" value={stats?.tier_counts?.Warm || 0} sub="Score 40–69" icon={Thermometer} color="var(--warm)" />
        <StatCard label="Cold Leads" value={stats?.tier_counts?.Cold || 0} sub="Score &lt; 40" icon={Snowflake} color="var(--cold)" />
        <StatCard label="Avg ML Score" value={stats?.average_ml_score || 0} sub="Across all leads" icon={TrendingUp} color="var(--accent2)" />
        <StatCard label="Emails Sent" value={eng.emails_sent || 0} sub={`Open rate: ${eng.open_rate_pct || 0}%`} icon={Mail} color="#00d4aa" />
        <StatCard label="Replies" value={eng.replied || 0} sub={`Reply rate: ${eng.reply_rate_pct || 0}%`} icon={MessageSquare} color="#ffad33" />
        <StatCard label="Demos" value={eng.demoed || 0} sub="Booked" icon={BarChart2} color="var(--accent)" />
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Tier donut */}
        <div className="chart-card">
          <div className="chart-title">Lead Tier Distribution</div>
          <div className="chart-sub">Hot / Warm / Cold breakdown</div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={tierData} cx="50%" cy="50%" innerRadius={55} outerRadius={88} dataKey="value" paddingAngle={3}>
                {tierData.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Industry bar */}
        <div className="chart-card">
          <div className="chart-title">Top Industries</div>
          <div className="chart-sub">Lead count by industry</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={industryData} layout="vertical" margin={{ left: 10 }}>
              <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} width={130} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="var(--accent)" radius={[0, 4, 4, 0]}>
                {industryData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Country pie */}
        <div className="chart-card">
          <div className="chart-title">Top Countries</div>
          <div className="chart-sub">Geographic distribution</div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={countryData} cx="50%" cy="50%" outerRadius={88} dataKey="value" paddingAngle={2}>
                {countryData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Engagement bar */}
        <div className="chart-card">
          <div className="chart-title">Engagement Funnel</div>
          <div className="chart-sub">Email pipeline performance</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={[
              { stage: 'Sent', count: eng.emails_sent || 0 },
              { stage: 'Opened', count: eng.emails_opened || 0 },
              { stage: 'Replied', count: eng.replied || 0 },
              { stage: 'Demoed', count: eng.demoed || 0 },
            ]} margin={{ left: -20 }}>
              <XAxis dataKey="stage" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {['#6378ff', '#9b6bff', '#00d4aa', '#ffad33'].map((c, i) => <Cell key={i} fill={c} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Agent weights */}
      {stats?.effective_weights && (
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🎯 Effective Scoring Weights (Learning-Adjusted)</div>
          {Object.entries(stats.effective_weights).map(([k, v]) => (
            <div key={k} className="weight-bar-row">
              <div className="weight-name" style={{ textTransform: 'capitalize', fontSize: 13 }}>{k.replace(/_/g, ' ')}</div>
              <div className="weight-track">
                <div className="weight-fill" style={{ width: `${Math.min(100, v * 100 * 4)}%` }} />
              </div>
              <div className="weight-val">{(v * 100).toFixed(1)}%</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
