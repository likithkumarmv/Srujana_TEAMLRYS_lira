import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { formatDate } from '../../lib/formatters';
import { PhoneCall, ShieldAlert, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

export const VerificationQueuePage: React.FC = () => {
  const [calls, setCalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadCalls = async () => {
    try {
      setLoading(true);
      const res = await api.getVerificationCalls();
      setCalls(res.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCalls();
  }, []);

  return (
    <div>
      <div className="demo-banner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={16} color="var(--primary)" />
          <span><strong>AI Calling Agent Protocol:</strong> The assistant identifies itself as automated and questions only whether pending payment instruction was authorized. Outcome is supporting evidence only.</span>
        </div>
        <span className="badge badge-simulated">Mock Provider Active</span>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Call Identifier</th>
                <th>Supplier Target</th>
                <th>Trusted Number Source</th>
                <th>Call Status</th>
                <th>Structured Finding</th>
                <th>Uncertainty Assessment</th>
                <th>Time Completed</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    Loading verification call logs...
                  </td>
                </tr>
              ) : calls.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    No verification calls placed yet. You can trigger one from an Investigation workbench or the Simulator.
                  </td>
                </tr>
              ) : (
                calls.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{c.provider_call_id || c.id.substring(0, 8)}</div>
                      <span className="badge badge-simulated">{c.provider}</span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{c.supplier_name || 'Vendor Entity'}</div>
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {c.contact_source}
                    </td>
                    <td>
                      <span className="badge badge-low">{c.status}</span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: c.answer_category === 'denied_request' ? 'var(--danger)' : 'var(--success)' }}>
                        {c.answer_category?.toUpperCase() || 'COMPLETED'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '2px' }}>
                        {c.structured_summary}
                      </div>
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      {c.uncertainty_note || 'Human review required prior to payment release.'}
                    </td>
                    <td className="tabular-nums" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {formatDate(c.ended_at || c.created_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
