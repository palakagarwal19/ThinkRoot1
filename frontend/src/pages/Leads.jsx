import { useState, useEffect, useCallback } from 'react';
import { Search, ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Link, ExternalLink } from 'lucide-react';
import { getLeads } from '../api';
import { Spinner, TierBadge, ScoreBar, EmptyState } from '../components/UI';
import LeadDrawer from '../components/LeadDrawer';

const TIERS = ['', 'Hot', 'Warm', 'Cold'];
const SORTS = [
  { value: 'score', label: 'Score' },
  { value: 'company', label: 'Company' },
  { value: 'country', label: 'Country' },
];

export default function Leads() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  const [search, setSearch] = useState('');
  const [tier, setTier] = useState('');
  const [sortBy, setSortBy] = useState('score');
  const [order, setOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const LIMIT = 25;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getLeads({ search, tier, sort_by: sortBy, order, page, limit: LIMIT });
      setData(res);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [search, tier, sortBy, order, page]);

  useEffect(() => { setPage(1); }, [search, tier, sortBy, order]);
  useEffect(() => { load(); }, [load]);

  const toggleSort = (col) => {
    if (sortBy === col) setOrder(o => o === 'desc' ? 'asc' : 'desc');
    else { setSortBy(col); setOrder('desc'); }
  };

  const SortIcon = ({ col }) => sortBy === col
    ? (order === 'desc' ? <ChevronDown size={13} /> : <ChevronUp size={13} />)
    : null;

  const leads = data?.leads || [];
  const totalPages = data?.total_pages || 1;

  return (
    <div className="page slide-up">
      <div className="page-header">
        <h1>👥 Lead Intelligence</h1>
        <p>{data?.total || 0} leads · ML-scored and ranked</p>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="search-wrap">
          <Search size={16} />
          <input
            className="search-input"
            placeholder="Search name, company, email…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select className="filter-select" value={tier} onChange={e => setTier(e.target.value)}>
          {TIERS.map(t => <option key={t} value={t}>{t || 'All Tiers'}</option>)}
        </select>
        <select className="filter-select" value={sortBy} onChange={e => setSortBy(e.target.value)}>
          {SORTS.map(s => <option key={s.value} value={s.value}>Sort: {s.label}</option>)}
        </select>
        <button className="btn btn-ghost" onClick={() => setOrder(o => o === 'desc' ? 'asc' : 'desc')}>
          {order === 'desc' ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
          {order === 'desc' ? 'Desc' : 'Asc'}
        </button>
      </div>

      {/* Table */}
      {loading ? <Spinner /> : leads.length === 0 ? (
        <EmptyState icon={Search} message="No leads match your filters" />
      ) : (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th onClick={() => toggleSort('company')}>Name / Company <SortIcon col="company" /></th>
                  <th>Title</th>
                  <th>Industry</th>
                  <th onClick={() => toggleSort('country')}>Country <SortIcon col="country" /></th>
                  <th>Tier</th>
                  <th onClick={() => toggleSort('score')}>Score <SortIcon col="score" /></th>
                  <th>Links</th>
                </tr>
              </thead>
              <tbody>
                {leads.map(lead => (
                  <tr key={lead.id} onClick={() => setSelectedId(lead.id)}>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{lead.name || '—'}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{lead.company || '—'}</div>
                    </td>
                    <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {lead.title || '—'}
                    </td>
                    <td>{lead.industry || '—'}</td>
                    <td>{lead.country || '—'}</td>
                    <td><TierBadge tier={lead.ml_score?.tier} /></td>
                    <td><ScoreBar score={lead.ml_score?.score ?? 0} /></td>
                    <td onClick={e => e.stopPropagation()}>
                      <div style={{ display: 'flex', gap: 6 }}>
                        {lead.linkedin_url && (
                          <a href={lead.linkedin_url} target="_blank" rel="noreferrer"
                            style={{ color: 'var(--text-muted)', transition: 'color 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.color = 'var(--accent)'}
                            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}>
                            <Link size={15} />
                          </a>
                        )}
                        {lead.website && (
                          <a href={`https://${lead.website}`} target="_blank" rel="noreferrer"
                            style={{ color: 'var(--text-muted)', transition: 'color 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.color = 'var(--accent)'}
                            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}>
                            <ExternalLink size={15} />
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button className="page-btn" onClick={() => setPage(1)} disabled={page === 1}>«</button>
            <button className="page-btn" onClick={() => setPage(p => p - 1)} disabled={page === 1}>
              <ChevronLeft size={14} />
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const p = Math.max(1, Math.min(page - 2, totalPages - 4)) + i;
              return p <= totalPages ? (
                <button key={p} className={`page-btn${page === p ? ' active' : ''}`} onClick={() => setPage(p)}>{p}</button>
              ) : null;
            })}
            <button className="page-btn" onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>
              <ChevronRight size={14} />
            </button>
            <button className="page-btn" onClick={() => setPage(totalPages)} disabled={page === totalPages}>»</button>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 8 }}>
              Page {page} of {totalPages} · {data?.total} leads
            </span>
          </div>
        </>
      )}

      {selectedId && <LeadDrawer leadId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}
