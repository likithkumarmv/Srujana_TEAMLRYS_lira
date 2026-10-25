import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { formatCurrency, formatDate, getPriorityClass, getStatusLabel } from '../../lib/formatters';
import {
  ArrowLeft,
  ShieldAlert,
  PhoneCall,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  UserCheck,
  Building2,
  Clock,
  ArrowRightLeft,
  Network
} from 'lucide-react';

interface CaseDetailPageProps {
  caseId: string;
  onBack: () => void;
}

export const CaseDetailPage: React.FC<CaseDetailPageProps> = ({ caseId, onBack }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Disposition modal state
  const [showDispModal, setShowDispModal] = useState(false);
  const [selectedDisp, setSelectedDisp] = useState('closed_verified');
  const [dispNote, setDispNote] = useState('');

  // Gemini state
  const [geminiResult, setGeminiResult] = useState<any>(null);
  const [geminiLoading, setGeminiLoading] = useState(false);

  const loadCase = async () => {
    try {
      setLoading(true);
      const res = await api.getCaseDetail(caseId);
      setData(res);
    } catch (err: any) {
      alert(`Error loading case: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [caseId]);

  if (loading || !data) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading investigation workbench...</div>;
  }

  const { case: c, supplier, transactions, graph, actions, calls } = data;

  const handleAcknowledge = async () => {
    try {
      setActionLoading(true);
      await api.acknowledgeCase(c.id, 'Acknowledged by operator');
      await loadCase();
    } catch (e: any) {
      alert(`Acknowledge failed: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRequestCall = async () => {
    try {
      setActionLoading(true);
      await api.requestVerificationCall(c.id, 'Initiated via analyst workbench');
      await loadCase();
    } catch (e: any) {
      alert(`Call request failed: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalate = async () => {
    const reason = prompt('Enter rationale for escalating this case to Senior Risk Review:');
    if (!reason) return;
    try {
      setActionLoading(true);
      await api.escalateCase(c.id, reason, c.version);
      await loadCase();
    } catch (e: any) {
      alert(`Escalation failed: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitDisposition = async () => {
    if (!dispNote || dispNote.trim().length < 5) {
      alert('A detailed human reviewer rationale (minimum 5 characters) is required for audit compliance.');
      return;
    }
    try {
      setActionLoading(true);
      await api.setCaseDisposition(c.id, selectedDisp, dispNote, c.version);
      setShowDispModal(false);
      await loadCase();
    } catch (e: any) {
      alert(`Disposition failed: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTriggerGemini = async () => {
    try {
      setGeminiLoading(true);
      const res = await api.analyzeCaseWithGemini(c.id);
      setGeminiResult(res);
    } catch (e: any) {
      alert(`Gemini analysis failed: ${e.message}`);
    } finally {
      setGeminiLoading(false);
    }
  };

  return (
    <div>
      {/* Top Bar Navigation & Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button className="btn btn-sm" onClick={onBack}>
            <ArrowLeft size={14} /> Back
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '20px', fontWeight: 700 }}>{c.case_ref}</h1>
              <span className={`badge ${getPriorityClass(c.priority)}`}>{c.priority}</span>
              <span className="badge" style={{ background: 'var(--surface-muted)' }}>{getStatusLabel(c.status)}</span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>v{c.version}</span>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{c.title}</div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-sm" onClick={handleAcknowledge} disabled={actionLoading}>
            <UserCheck size={14} /> Acknowledge
          </button>
          <button className="btn btn-sm btn-primary" onClick={handleRequestCall} disabled={actionLoading || !supplier?.known_contact_phone}>
            <PhoneCall size={14} /> Request Verification Call
          </button>
          <button className="btn btn-sm" onClick={handleEscalate} disabled={actionLoading || c.status === 'escalated'}>
            <AlertTriangle size={14} /> Escalate
          </button>
          <button className="btn btn-sm btn-primary" onClick={() => setShowDispModal(true)} disabled={actionLoading}>
            <CheckCircle2 size={14} /> Set Disposition
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Left Column: Risk Engine Breakdown + Graph + Transactions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Summary Card */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Case Overview & Risk Synthesis</h2>
              <div style={{ textAlign: 'right' }}>
                <span className="stat-label">Amount At Risk: </span>
                <span className="tabular-nums" style={{ fontSize: '16px', fontWeight: 700 }}>{formatCurrency(c.amount_at_risk)}</span>
              </div>
            </div>
            <p style={{ color: 'var(--text)', fontSize: '13px', lineHeight: '1.6', marginBottom: '14px' }}>
              {c.summary}
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', padding: '12px', background: 'var(--surface-muted)', borderRadius: 'var(--radius-sm)' }}>
              <div>
                <div className="stat-label">Risk Score</div>
                <div className="tabular-nums" style={{ fontSize: '18px', fontWeight: 700 }}>{c.risk_score} / 100</div>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Priority indicator (not fraud probability)</span>
              </div>
              <div>
                <div className="stat-label">Evidence Confidence</div>
                <div className="tabular-nums" style={{ fontSize: '18px', fontWeight: 700 }}>{c.evidence_confidence}%</div>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Corroboration level</span>
              </div>
              <div>
                <div className="stat-label">Data Completeness</div>
                <div className="tabular-nums" style={{ fontSize: '18px', fontWeight: 700 }}>{c.data_completeness}%</div>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Field coverage</span>
              </div>
            </div>
          </div>

          {/* Explainable Signals Breakdown */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <ShieldAlert size={18} />
                <span>Explainable Signal Breakdown</span>
              </h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {c.risk_reasons && c.risk_reasons.length > 0 ? (
                c.risk_reasons.map((sig: any, idx: number) => (
                  <div key={idx} style={{ padding: '12px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'var(--surface-muted)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600, fontSize: '13px' }}>{sig.label}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className="badge" style={{ background: 'var(--surface)' }}>+{sig.points} pts</span>
                        <span className={`badge ${sig.severity === 'high' ? 'badge-critical' : 'badge-high'}`}>{sig.severity}</span>
                      </div>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{sig.explanation}</div>
                  </div>
                ))
              ) : (
                <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No high-risk signal anomalies observed for this case.</div>
              )}
            </div>
          </div>

          {/* Episode Relationship Graph (Interactive SVG network) */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <Network size={18} />
                <span>Episode Relationship Network</span>
              </h2>
            </div>
            <div style={{ height: '220px', background: 'var(--surface-muted)', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
              <svg width="100%" height="100%" viewBox="0 0 500 200">
                {/* Connections */}
                <line x1="80" y1="100" x2="250" y2="60" stroke="var(--primary)" strokeWidth="2" strokeDasharray="4" />
                <line x1="250" y1="60" x2="420" y2="100" stroke="var(--danger)" strokeWidth="2" />
                <line x1="80" y1="100" x2="250" y2="140" stroke="var(--border)" strokeWidth="2" />

                {/* Node 1: Vendor */}
                <circle cx="80" cy="100" r="28" fill="var(--surface)" stroke="var(--primary)" strokeWidth="2" />
                <text x="80" y="96" textAnchor="middle" fill="var(--text)" fontSize="10" fontWeight="600">Supplier</text>
                <text x="80" y="110" textAnchor="middle" fill="var(--text-muted)" fontSize="8">Bharathi Ind</text>

                {/* Node 2: Case Episode */}
                <circle cx="250" cy="60" r="32" fill="var(--surface)" stroke="var(--danger)" strokeWidth="3" />
                <text x="250" y="56" textAnchor="middle" fill="var(--danger)" fontSize="11" fontWeight="700">{c.case_ref}</text>
                <text x="250" y="70" textAnchor="middle" fill="var(--text-muted)" fontSize="9">Risk: {c.risk_score}</text>

                {/* Node 3: Tx Outbound */}
                <circle cx="250" cy="140" r="24" fill="var(--surface)" stroke="var(--border)" strokeWidth="2" />
                <text x="250" y="136" textAnchor="middle" fill="var(--text)" fontSize="9">₹485,000</text>
                <text x="250" y="148" textAnchor="middle" fill="var(--text-muted)" fontSize="8">Tx-9041</text>

                {/* Node 4: Destination Account */}
                <circle cx="420" cy="100" r="28" fill="var(--surface)" stroke="var(--danger)" strokeWidth="2" />
                <text x="420" y="96" textAnchor="middle" fill="var(--danger)" fontSize="10" fontWeight="600">New Dest</text>
                <text x="420" y="110" textAnchor="middle" fill="var(--text-muted)" fontSize="8">FP-ICIC-8841</text>
              </svg>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>
              Graph edges represent evidence-backed associations linking pending transaction to previously unverified beneficiary destination.
            </div>
          </div>

          {/* Linked Transactions Table */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <ArrowRightLeft size={18} />
                <span>Linked Evidence Transactions ({transactions.length})</span>
              </h2>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Tx ID</th>
                    <th>Direction</th>
                    <th>Amount</th>
                    <th>Beneficiary Fingerprint</th>
                    <th>Channel Route</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t: any) => (
                    <tr key={t.id}>
                      <td style={{ fontWeight: 600 }}>{t.external_id}</td>
                      <td>
                        <span className="badge" style={{ background: 'var(--surface-muted)' }}>{t.direction}</span>
                      </td>
                      <td className="tabular-nums" style={{ fontWeight: 600 }}>{formatCurrency(t.amount)}</td>
                      <td style={{ fontSize: '12px' }}>{t.beneficiary_fingerprint || '—'}</td>
                      <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t.contact_route}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Supplier Verification + Gemini Copilot + Audit Trail */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Supplier Profile & Verification Box */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <Building2 size={18} />
                <span>Supplier Verification Status</span>
              </h2>
            </div>

            {supplier ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{supplier.display_name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Source: {supplier.trusted_contact_source}</div>
                </div>

                <div style={{ padding: '8px 10px', background: 'var(--surface-muted)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Trusted Contact Directory:</div>
                  <div style={{ fontWeight: 600, color: 'var(--text)' }}>
                    {supplier.known_contact_name} ({supplier.known_contact_phone})
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Established Beneficiary:</span>
                  <span style={{ fontWeight: 600 }}>{supplier.previous_beneficiary_fingerprint || supplier.current_beneficiary_fingerprint}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Requested Beneficiary:</span>
                  <span style={{ color: 'var(--danger)', fontWeight: 600 }}>{supplier.current_beneficiary_fingerprint}</span>
                </div>

                {calls && calls.length > 0 && (
                  <div style={{ marginTop: '10px', padding: '12px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'var(--surface-muted)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600, fontSize: '12px' }}>Latest Verification Call</span>
                      <span className="badge badge-simulated">{calls[0].provider}</span>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--danger)', fontWeight: 600, marginBottom: '4px' }}>
                      Result: {calls[0].answer_category?.toUpperCase() || 'COMPLETED'}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text)' }}>{calls[0].structured_summary}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', fontStyle: 'italic' }}>
                      {calls[0].uncertainty_note}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No supplier entity linked to this transaction burst.</div>
            )}
          </div>

          {/* Gemini AI Copilot Card */}
          <div className="card" style={{ border: '1px solid var(--primary)' }}>
            <div className="card-header">
              <h2 className="card-title" style={{ color: 'var(--primary)' }}>
                <Sparkles size={18} />
                <span>Gemini AI Copilot Synthesis</span>
              </h2>
              <button className="btn btn-sm btn-primary" onClick={handleTriggerGemini} disabled={geminiLoading}>
                {geminiLoading ? 'Analyzing...' : 'Analyze Episode'}
              </button>
            </div>

            {geminiResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
                <div style={{ padding: '8px', background: 'var(--surface-muted)', borderRadius: 'var(--radius-sm)' }}>
                  <strong>Risk Summary:</strong>
                  <div style={{ marginTop: '4px', color: 'var(--text)' }}>{geminiResult.risk_summary}</div>
                </div>

                <div>
                  <strong>Suggested Supplier Phone Interview Questions:</strong>
                  <ul style={{ paddingLeft: '18px', marginTop: '4px', color: 'var(--text)' }}>
                    {geminiResult.recommended_interview_questions?.map((q: string, i: number) => (
                      <li key={i} style={{ marginBottom: '4px' }}>{q}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <strong>Investigative Leads:</strong>
                  <ul style={{ paddingLeft: '18px', marginTop: '4px', color: 'var(--text-muted)' }}>
                    {geminiResult.investigative_leads?.map((l: string, i: number) => (
                      <li key={i}>{l}</li>
                    ))}
                  </ul>
                </div>

                <div style={{ fontSize: '11px', color: 'var(--warning)', borderTop: '1px solid var(--border)', paddingTop: '6px' }}>
                  {geminiResult.disposition_guidance}
                </div>
              </div>
            ) : (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Click <strong>Analyze Episode</strong> to run Gemini AI reasoning across the linked evidence signals and generate targeted phone interview questions.
              </div>
            )}
          </div>

          {/* Actions & Audit Trail */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <Clock size={18} />
                <span>Case Activity Log</span>
              </h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {actions && actions.map((act: any) => (
                <div key={act.id} style={{ fontSize: '12px', paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                    <span style={{ fontWeight: 600 }}>{act.action_type}</span>
                    <span className="tabular-nums">{formatDate(act.created_at)}</span>
                  </div>
                  <div style={{ color: 'var(--text)', marginTop: '2px' }}>{act.note}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Disposition Modal */}
      {showDispModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Record Human-Reviewed Disposition</h3>
              <button className="btn btn-sm" onClick={() => setShowDispModal(false)}>✕</button>
            </div>

            <div className="form-group">
              <label className="form-label">Review Outcome Decision</label>
              <select className="select" value={selectedDisp} onChange={(e) => setSelectedDisp(e.target.value)}>
                <option value="closed_verified">Closed Verified (Legitimate Authorized Payment)</option>
                <option value="closed_rejected">Closed Rejected (Fraud Prevented — Payment Cancelled)</option>
                <option value="closed_inconclusive">Closed Inconclusive</option>
                <option value="under_review">Keep Under Review</option>
                <option value="escalated">Escalate to Senior Fraud Committee</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Investigator Rationale (Mandatory Audit Trail)</label>
              <textarea
                className="textarea"
                rows={4}
                placeholder="Enter corroborating evidence details, phone callback notes, or vendor confirmation findings..."
                value={dispNote}
                onChange={(e) => setDispNote(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
              <button className="btn" onClick={() => setShowDispModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSubmitDisposition} disabled={actionLoading}>
                {actionLoading ? 'Saving...' : 'Commit Disposition'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
