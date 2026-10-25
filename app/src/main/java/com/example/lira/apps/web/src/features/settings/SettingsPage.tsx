import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Settings, Shield, Sparkles, Database, Sun, Moon } from 'lucide-react';

interface SettingsPageProps {
  theme: string;
  onToggleTheme: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ theme, onToggleTheme }) => {
  const [geminiStatus, setGeminiStatus] = useState<any>(null);

  useEffect(() => {
    api.getGeminiStatus().then(setGeminiStatus).catch(console.error);
  }, []);

  const weights = [
    { signal: 'Beneficiary / Bank-detail change', points: 24, description: 'Destination differs from previously recorded supplier beneficiary' },
    { signal: 'Contact-route mismatch', points: 18, description: 'Request arrives via untrusted route (e.g. unsolicited email) vs portal' },
    { signal: 'New or unseen recipient', points: 14, description: 'Recipient account has no established ledger history' },
    { signal: 'Velocity / possible structuring', points: 12, description: 'Multiple transfers exceed baseline or cluster near dual-authorization caps' },
    { signal: 'Amount drift', points: 10, description: 'Amount deviates significantly (>200%) from historical mean' },
    { signal: 'Urgency / unusual timing', points: 8, description: 'Emergency clearance or timing conflicts with vendor schedule' },
    { signal: 'Network / pass-through relationship', points: 9, description: 'Rapid inflow to outflow redirection through connected nodes' },
    { signal: 'Relevant prior risk context', points: 5, description: 'Existing open or escalated alerts tied to same counterparty' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Cloud & AI Integrations */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Sparkles size={18} color="var(--primary)" />
            <span>Cloud & AI Intelligence Integration</span>
          </h2>
          <span className="badge badge-simulated">
            {geminiStatus?.configured ? 'Gemini 1.5 Live' : 'Heuristic Mode'}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div style={{ padding: '14px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'var(--surface-muted)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, marginBottom: '6px' }}>
              <Database size={16} color="var(--primary)" />
              <span>Supabase Database (Single Source of Truth)</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              PostgreSQL schema with Row Level Security (RLS) protects cases, transactions, suppliers, NFC cards, and audit logs.
              Once you provide your Supabase URL and service role key, the backend automatically directs live queries to your Supabase project.
            </p>
          </div>

          <div style={{ padding: '14px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'var(--surface-muted)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, marginBottom: '6px' }}>
              <Sparkles size={16} color="var(--primary)" />
              <span>Google Gemini AI Engine</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              {geminiStatus?.message || 'Gemini provides automated fraud vector synthesis, telephone interview questions, and deep anomaly explanations.'}
              When you send the Gemini API key, it seamlessly elevates all case reasoning.
            </p>
          </div>
        </div>
      </div>

      {/* Theme & Display Preferences */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Settings size={18} />
            <span>Display & Accessibility Preferences</span>
          </h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontWeight: 600 }}>Color Theme</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              LIRA features high-contrast light and dark themes tailored for financial analysts.
            </div>
          </div>

          <button className="btn" onClick={onToggleTheme}>
            {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
            <span>Current: {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>
          </button>
        </div>
      </div>

      {/* Risk Engine Rules Weights Matrix */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Shield size={18} />
            <span>Risk Engine Weights Matrix (Engine: lira-rules-1.0)</span>
          </h2>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Max priority points sum: 100 pts
          </span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Risk Factor Signal</th>
                <th>Max Points</th>
                <th>What It Checks</th>
              </tr>
            </thead>
            <tbody>
              {weights.map((w, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{w.signal}</td>
                  <td className="tabular-nums" style={{ fontWeight: 700, color: 'var(--primary)' }}>
                    +{w.points} pts
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {w.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
