import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { formatCurrency, formatDate, getPriorityClass, getStatusLabel } from '../../lib/formatters';
import { ShieldAlert, AlertTriangle, Clock, ArrowRight, ShieldCheck, Cpu } from 'lucide-react';

interface DashboardProps {
  onNavigateToCase: (caseId: string) => void;
  onNavigateTab: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardProps> = ({ onNavigateToCase, onNavigateTab }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const res = await api.getDashboardSummary();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  if (loading || !data) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading financial risk intelligence...</div>;
  }

  const { kpis, priority_distribution, recent_cases, recent_activity } = data;

  return (
    <div>
      <div className="demo-banner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={16} color="var(--primary)" />
          <span><strong>LIRA Prototype Demo Active:</strong> All records are synthetic. Risk scores indicate relative review priority (0–100), not statistical fraud probabilities.</span>
        </div>
        <button className="btn btn-sm" onClick={() => onNavigateTab('simulator')}>
          Open Simulator
        </button>
      </div>

      {/* KPI Stats */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Active Cases</div>
          <div className="stat-value">{kpis.open_cases}</div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Requiring analyst attention</span>
        </div>

        <div className="stat-card" style={{ borderLeft: '4px solid var(--danger)' }}>
          <div className="stat-label" style={{ color: 'var(--danger)' }}>Critical Priority</div>
          <div className="stat-value" style={{ color: 'var(--danger)' }}>{kpis.critical_cases}</div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Beneficiary detail changes / High risk</span>
        </div>

        <div className="stat-card">
          <div className="stat-label">Awaiting Call Verification</div>
          <div className="stat-value">{kpis.awaiting_verification}</div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>AI supplier call requested</span>
        </div>

        <div className="stat-card">
          <div className="stat-label">Amount at Risk Review</div>
          <div className="stat-value">{formatCurrency(kpis.amount_at_risk)}</div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total potential review exposure</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* Recent Priority Cases */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <ShieldAlert size={18} />
              <span>Priority Investigation Queue</span>
            </h2>
            <button className="btn btn-sm" onClick={() => onNavigateTab('investigations')}>
              View All Cases
            </button>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Case Ref</th>
                  <th>Priority</th>
                  <th>Risk Score</th>
                  <th>Status</th>
                  <th>Amount</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recent_cases.map((c: any) => (
                  <tr key={c.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{c.case_ref}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{c.title.substring(0, 36)}...</div>
                    </td>
                    <td>
                      <span className={`badge ${getPriorityClass(c.priority)}`}>
                        {c.priority}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 700 }} className="tabular-nums">{c.risk_score}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}> / 100</span>
                    </td>
                    <td>
                      <span style={{ fontSize: '12px', fontWeight: 500 }}>{getStatusLabel(c.status)}</span>
                    </td>
                    <td className="tabular-nums" style={{ fontWeight: 600 }}>
                      {formatCurrency(c.amount_at_risk)}
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => onNavigateToCase(c.id)}
                      >
                        Inspect <ArrowRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Priority Breakdown & System Health */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Case Risk Distribution</h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--danger)', fontWeight: 600 }}>Critical (75–100)</span>
                  <span className="tabular-nums">{priority_distribution.critical}</span>
                </div>
                <div style={{ height: '8px', background: 'var(--surface-muted)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, (priority_distribution.critical / 5) * 100)}%`, height: '100%', background: 'var(--danger)' }}></div>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--warning)', fontWeight: 600 }}>High (50–74)</span>
                  <span className="tabular-nums">{priority_distribution.high}</span>
                </div>
                <div style={{ height: '8px', background: 'var(--surface-muted)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, (priority_distribution.high / 5) * 100)}%`, height: '100%', background: 'var(--warning)' }}></div>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--info)', fontWeight: 600 }}>Watch (25–49)</span>
                  <span className="tabular-nums">{priority_distribution.watch}</span>
                </div>
                <div style={{ height: '8px', background: 'var(--surface-muted)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, (priority_distribution.watch / 5) * 100)}%`, height: '100%', background: 'var(--info)' }}></div>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--success)', fontWeight: 600 }}>Low (0–24)</span>
                  <span className="tabular-nums">{priority_distribution.low}</span>
                </div>
                <div style={{ height: '8px', background: 'var(--surface-muted)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, (priority_distribution.low / 5) * 100)}%`, height: '100%', background: 'var(--success)' }}></div>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                <Cpu size={18} />
                <span>Console Infrastructure</span>
              </h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>FastAPI Engine:</span>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>Operational (v1.0)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Supabase PostgreSQL:</span>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>Source of Truth Active</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Voice AI Adapter:</span>
                <span className="badge badge-simulated">Mock Sandbox Ready</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>ESP32 Physical Terminals:</span>
                <span style={{ fontWeight: 600 }}>2 Registered</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Activity Trail */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Recent Audit Log & Operator Events</h2>
          <button className="btn btn-sm" onClick={() => onNavigateTab('audit')}>Full Audit Log</button>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target Object</th>
                <th>Audit Details</th>
              </tr>
            </thead>
            <tbody>
              {recent_activity.map((act: any) => (
                <tr key={act.id}>
                  <td className="tabular-nums" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {formatDate(act.created_at)}
                  </td>
                  <td>
                    <span className="badge" style={{ background: 'var(--surface-muted)' }}>
                      {act.actor_type}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{act.action}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{act.object_type}</td>
                  <td style={{ fontSize: '12px' }}>{JSON.stringify(act.details)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
