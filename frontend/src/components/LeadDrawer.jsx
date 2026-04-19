import { useState, useEffect } from 'react';
import { X, Mail, Link, Copy, Check, ExternalLink, Zap, Brain } from 'lucide-react';
import { getLead, getLeadOutreach, submitResponse } from '../api';
import { TierBadge, ScoreBar, Spinner } from './UI';

export default function LeadDrawer({ leadId, onClose }) {
  const [data, setData] = useState(null);
  const [outreach, setOutreach] = useState(null);
  const [loadingLead, setLoadingLead] = useState(true);
  const [loadingOutreach, setLoadingOutreach] = useState(false);
  const [outreachTab, setOutreachTab] = useState('email_a');
  const [copied, setCopied] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setLoadingLead(true);
    getLead(leadId)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoadingLead(false));
  }, [leadId]);

  const loadOutreach = async () => {
    setLoadingOutreach(true);
    try {
      const res = await getLeadOutreach(leadId);
      setOutreach(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingOutreach(false);
    }
  };

  const copyText = (txt) => {
    navigator.clipboard.writeText(txt);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const handleResponse = async (type) => {
    setSubmitting(true);
    try {
      await submitResponse({ lead_id: leadId, response_type: type });
      setSubmitted(type);
    } catch (e) { setError(e.message); }
    finally { setSubmitting(false); }
  };

  const TAB_LABELS = {
    email_a: '📧 Email A', email_b: '📧 Email B',
    linkedin_a: '💼 LinkedIn A', linkedin_b: '💼 LinkedIn B',
  };

  const getOutreachContent = () => {
    if (!outreach) return '';
    const map = {
      email_a: outreach.email?.variant_a,
      email_b: outreach.email?.variant_b,
      linkedin_a: outreach.linkedin?.variant_a,
      linkedin_b: outreach.linkedin?.variant_b,
    };
    const v = map[outreachTab];
    if (!v) return 'Not available.';
    if (typeof v === 'string') return v;
    return [v.subject && `Subject: ${v.subject}`, v.body || v.message || JSON.stringify(v)]
      .filter(Boolean).join('\n\n');
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer fade-in" onClick={e => e.stopPropagation()}>
        {loadingLead ? <Spinner /> : !data ? (
          <div className="drawer-body"><p style={{ color: 'var(--hot)' }}>{error || 'Not found'}</p></div>
        ) : (
          <>
            {/* Header */}
            <div className="drawer-header">
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 700 }}>
                  {data.lead?.first_name} {data.lead?.last_name}
                </h2>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 3 }}>
                  {data.lead?.title} · {data.lead?.company}
                </p>
                <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                  {data.ml_score && <TierBadge tier={data.ml_score.tier} />}
                  {data.ml_score && <ScoreBar score={data.ml_score.score} />}
                </div>
              </div>
              <button className="btn btn-ghost" onClick={onClose} style={{ padding: '8px' }}>
                <X size={18} />
              </button>
            </div>

            <div className="drawer-body">
              {/* Contact Info */}
              <div className="drawer-section">
                <div className="drawer-section-title">Contact Information</div>
                <div className="info-grid">
                  <div className="info-item">
                    <div className="label">Email</div>
                    <div className="value">{data.lead?.email || '—'}</div>
                  </div>
                  <div className="info-item">
                    <div className="label">Email Status</div>
                    <div className="value">{data.lead?.email_status || '—'}</div>
                  </div>
                  <div className="info-item">
                    <div className="label">Seniority</div>
                    <div className="value">{data.lead?.seniority || '—'}</div>
                  </div>
                  <div className="info-item">
                    <div className="label">Industry</div>
                    <div className="value">{data.lead?.industry || '—'}</div>
                  </div>
                  <div className="info-item">
                    <div className="label">Country</div>
                    <div className="value">{data.lead?.country || '—'}</div>
                  </div>
                  <div className="info-item">
                    <div className="label">Employees</div>
                    <div className="value">{data.lead?.employees || '—'}</div>
                  </div>
                  <div className="info-item">
                    <div className="label">Annual Revenue</div>
                    <div className="value">{data.lead?.annual_revenue || '—'}</div>
                  </div>
                  <div className="info-item">
                    <div className="label">Latest Funding</div>
                    <div className="value">{data.lead?.latest_funding || '—'}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                  {data.lead?.linkedin_url && (
                    <a href={data.lead.linkedin_url} target="_blank" rel="noreferrer" className="btn btn-ghost" style={{ fontSize: 12 }}>
                      <Link size={14} /> LinkedIn
                    </a>
                  )}
                  {data.lead?.website && (
                    <a href={`https://${data.lead.website}`} target="_blank" rel="noreferrer" className="btn btn-ghost" style={{ fontSize: 12 }}>
                      <ExternalLink size={14} /> Website
                    </a>
                  )}
                </div>
              </div>

              {/* ML Score Breakdown */}
              {data.ml_score?.components && (
                <div className="drawer-section">
                  <div className="drawer-section-title"><Brain size={12} style={{ display: 'inline', marginRight: 5 }} />ML Score Breakdown</div>
                  {Object.entries(data.ml_score.components).map(([k, v]) => (
                    <div key={k} className="weight-bar-row">
                      <div className="weight-name" style={{ textTransform: 'capitalize', fontSize: 12 }}>{k.replace(/_/g, ' ')}</div>
                      <div className="weight-track">
                        <div className="weight-fill" style={{ width: `${Math.min(100, v * 100)}%` }} />
                      </div>
                      <div className="weight-val">{(v * 100).toFixed(0)}</div>
                    </div>
                  ))}
                  <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-muted)' }}>
                    ICP Match: {data.ml_score.icp_match ? '✅' : '❌'} &nbsp;|&nbsp;
                    Modern Stack: {data.ml_score.modern_stack ? '✅' : '❌'} &nbsp;|&nbsp;
                    Recent Funding: {data.ml_score.recent_funding ? '✅' : '❌'}
                  </div>
                </div>
              )}

              {/* Signals */}
              {data.signals && (
                <div className="drawer-section">
                  <div className="drawer-section-title"><Zap size={12} style={{ display: 'inline', marginRight: 5 }} />Signals</div>
                  {data.signals.intent_signals?.length > 0 && (
                    <>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Intent</div>
                      <div className="signal-list" style={{ marginBottom: 12 }}>
                        {data.signals.intent_signals.map((s, i) => <span key={i} className="signal-pill">{s}</span>)}
                      </div>
                    </>
                  )}
                  {data.signals.technologies?.length > 0 && (
                    <>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Technologies</div>
                      <div className="signal-list">
                        {data.signals.technologies.map((s, i) => (
                          <span key={i} className="signal-pill" style={{ background: 'rgba(0,212,170,0.08)', color: 'var(--accent3)', borderColor: 'rgba(0,212,170,0.2)' }}>{s}</span>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Response Signals */}
              <div className="drawer-section">
                <div className="drawer-section-title">Log Response Signal</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {['replied', 'demoed', 'opened', 'bounced', 'unsubscribed'].map(type => (
                    <button
                      key={type}
                      className={`btn ${submitted === type ? 'btn-primary' : 'btn-ghost'}`}
                      style={{ fontSize: 12, padding: '6px 12px', textTransform: 'capitalize' }}
                      onClick={() => handleResponse(type)}
                      disabled={submitting}
                    >
                      {submitted === type ? <Check size={12} /> : null}
                      {type}
                    </button>
                  ))}
                </div>
                {submitted && <div style={{ fontSize: 12, color: 'var(--accent3)', marginTop: 8 }}>✓ Response "{submitted}" recorded — weights updated</div>}
              </div>

              {/* Outreach */}
              <div className="drawer-section">
                <div className="drawer-section-title"><Mail size={12} style={{ display: 'inline', marginRight: 5 }} />AI Outreach</div>
                {!outreach ? (
                  <button className="btn btn-primary" onClick={loadOutreach} disabled={loadingOutreach}>
                    {loadingOutreach ? 'Generating…' : '✨ Generate A/B Outreach'}
                  </button>
                ) : (
                  <>
                    <div className="outreach-tabs">
                      {Object.entries(TAB_LABELS).map(([k, l]) => (
                        <button key={k} className={`tab-btn${outreachTab === k ? ' active' : ''}`} onClick={() => setOutreachTab(k)}>{l}</button>
                      ))}
                    </div>
                    <div className="outreach-box">
                      <button className="copy-btn" onClick={() => copyText(getOutreachContent())}>
                        {copied ? <><Check size={11} /> Copied</> : <><Copy size={11} /> Copy</>}
                      </button>
                      {getOutreachContent()}
                    </div>
                  </>
                )}
              </div>

              {error && <div style={{ color: 'var(--hot)', fontSize: 12, padding: '8px 12px', background: 'var(--hot-bg)', borderRadius: 8 }}>{error}</div>}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
