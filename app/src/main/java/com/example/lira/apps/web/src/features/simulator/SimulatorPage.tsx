import React, { useState } from 'react';
import { api } from '../../lib/api';
import { formatCurrency, getPriorityClass } from '../../lib/formatters';
import { FlaskConical, Play, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface SimulatorPageProps {
  onOpenCase: (caseId: string) => void;
}

export const SimulatorPage: React.FC<SimulatorPageProps> = ({ onOpenCase }) => {
  const [runningKey, setRunningKey] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<any>(null);

  const scenarios = [
    {
      key: 'normal_payment',
      title: '1. Routine Supplier Retainer',
      description: 'Standard payment to Apex Cloud Solutions. Fingerprint unchanged, vendor channel verified, amount normal.',
      expected: 'LOW Priority (0-24 pts)'
    },
    {
      key: 'changed_beneficiary',
      title: '2. Changed Beneficiary Destination',
      description: 'Established vendor request with a new bank destination fingerprint differing from historical ledger.',
      expected: 'WATCH / HIGH Priority'
    },
    {
      key: 'changed_beneficiary_urgent',
      title: '3. Flagship Showcase: Changed Beneficiary + Urgent Untrusted Route',
      description: 'High-urgency payment instruction via unsolicited external email attachment requesting new ICICI account.',
      expected: 'CRITICAL Priority (78 pts) — LIRA-1042 Episode'
    },
    {
      key: 'velocity_structuring',
      title: '4. Structuring / Burst Velocity Pattern',
      description: 'Three rapid transfers executed just below ₹50,000 threshold within 120 minutes.',
      expected: 'HIGH Priority (64 pts) — Episode Grouping'
    },
    {
      key: 'passthrough_rapid',
      title: '5. Pass-through Inflow / Outflow Dispersal',
      description: '₹850,000 inflow followed within 52 minutes by rapid dispersal to secondary linked accounts.',
      expected: 'WATCH / HIGH Priority'
    },
    {
      key: 'missing_evidence',
      title: '6. Missing Evidence Baseline / Uncertainty',
      description: 'First-time recipient with zero payment history. Proves LIRA avoids false certainty.',
      expected: 'LOW Completeness & Explicit Uncertainty Warnings'
    }
  ];

  const handleRun = async (key: string) => {
    try {
      setRunningKey(key);
      const res = await api.runSimulation(key, true);
      setLastResult(res);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setRunningKey(null);
    }
  };

  return (
    <div>
      <div className="demo-banner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FlaskConical size={16} color="var(--primary)" />
          <span><strong>Risk Engine Simulator:</strong> Execute deterministic payment scenarios to inspect rule points, signal firing, and case episode creation.</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {scenarios.map((s) => (
          <div key={s.key} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text)', marginBottom: '6px' }}>
                {s.title}
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5', marginBottom: '12px' }}>
                {s.description}
              </p>
              <div style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: 600, marginBottom: '16px' }}>
                Expected: {s.expected}
              </div>
            </div>

            <button
              className="btn btn-primary"
              onClick={() => handleRun(s.key)}
              disabled={runningKey !== null}
              style={{ width: '100%' }}
            >
              <Play size={14} />
              <span>{runningKey === s.key ? 'Evaluating Rules...' : 'Execute Scenario'}</span>
            </button>
          </div>
        ))}
      </div>

      {/* Realtime Simulation Outcome Banner & Breakdown */}
      {lastResult && (
        <div className="card" style={{ border: '2px solid var(--primary)', animation: 'fadeIn 0.2s ease' }}>
          <div className="card-header">
            <div>
              <h2 className="card-title" style={{ color: 'var(--primary)' }}>
                <CheckCircle2 size={18} />
                <span>Simulation Outcome: {lastResult.scenario_name}</span>
              </h2>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                {lastResult.disclaimer}
              </div>
            </div>

            {lastResult.case_created && (
              <button
                className="btn btn-sm btn-primary"
                onClick={() => onOpenCase(lastResult.case_created.id)}
              >
                Open Created Case ({lastResult.case_created.case_ref}) <ArrowRight size={14} />
              </button>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', padding: '14px', background: 'var(--surface-muted)', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
            <div>
              <div className="stat-label">Calculated Score</div>
              <div className="tabular-nums" style={{ fontSize: '20px', fontWeight: 700 }}>
                {lastResult.risk_score} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>/ 100</span>
              </div>
            </div>

            <div>
              <div className="stat-label">Assigned Priority</div>
              <div style={{ marginTop: '2px' }}>
                <span className={`badge ${getPriorityClass(lastResult.priority)}`}>
                  {lastResult.priority}
                </span>
              </div>
            </div>

            <div>
              <div className="stat-label">Evidence Confidence</div>
              <div className="tabular-nums" style={{ fontSize: '20px', fontWeight: 700 }}>
                {lastResult.evidence_confidence}%
              </div>
            </div>

            <div>
              <div className="stat-label">Data Completeness</div>
              <div className="tabular-nums" style={{ fontSize: '20px', fontWeight: 700 }}>
                {lastResult.data_completeness}%
              </div>
            </div>
          </div>

          <div style={{ fontWeight: 600, fontSize: '13px', marginBottom: '8px' }}>
            Observed Signal Points ({lastResult.signals_fired.length}):
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {lastResult.signals_fired.map((sig: any, i: number) => (
              <div key={i} style={{ padding: '8px 12px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                <div>
                  <span style={{ fontWeight: 600 }}>{sig.label}: </span>
                  <span style={{ color: 'var(--text-muted)' }}>{sig.explanation}</span>
                </div>
                <span className="badge" style={{ background: 'var(--surface-muted)' }}>+{sig.points} pts</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
