import { useState, useEffect } from 'react';
import { Search, Network } from 'lucide-react';
import { getAllGraphs } from '../api';
import { Spinner, EmptyState, TierBadge, ScoreBar } from '../components/UI';

export default function Graph() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    getAllGraphs()
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
          ⚠ Failed to load graph data: {error}
        </div>
      </div>
    );
  }

  const committees = data?.committees ?? [];
  const query = search.trim().toLowerCase();
  const filtered = query
    ? committees.filter((c) => c.company.toLowerCase().includes(query))
    : committees;

  function toggleExpanded(company) {
    setExpanded((prev) => (prev === company ? null : company));
  }

  return (
    <div className="page slide-up">
      <div className="page-header">
        <h1>🕸 Buying Committees</h1>
        <p>
          {data?.total_companies ?? 0} companies with identified buying committee members
        </p>
      </div>

      {/* Search */}
      <div className="filters-bar">
        <div className="search-wrap">
          <Search />
          <input
            className="search-input"
            placeholder="Search companies…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <EmptyState icon={Network} message="No companies match your search" />
      ) : (
        <div className="company-grid">
          {filtered.map((committee) => {
            const isExpanded = expanded === committee.company;
            const previewMembers = isExpanded
              ? committee.members
              : committee.members.slice(0, 3);

            return (
              <div
                key={committee.company}
                className="company-card"
                onClick={() => toggleExpanded(committee.company)}
              >
                <div className="company-name">{committee.company}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                  {committee.node_count} node{committee.node_count !== 1 ? 's' : ''}
                </div>

                <div className="members-list">
                  {previewMembers.map((member) => (
                    <div key={member.id} className="member-row">
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1, minWidth: 0 }}>
                        <span style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: 12 }}>
                          {member.name}
                        </span>
                        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                          {member.title}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                        <TierBadge tier={member.tier} />
                        <ScoreBar score={member.score} />
                      </div>
                    </div>
                  ))}

                  {!isExpanded && committee.members.length > 3 && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', paddingTop: 4 }}>
                      +{committee.members.length - 3} more — click to expand
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
